"""Marketplace API views — public + private + leads.

Public surface = approved + active services/bundles, verified vendors.
Private surface = vendor self-management (services / packages / bundles /
profile / onboard) + buyer/vendor lead workflow.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.accounts.models import VendorProfile
from apps.core.api.pagination import TimeCursorPagination
from apps.core.api.permissions import IsVendor
from apps.core.api.throttling import LeadThrottle

from ..models import (
    Bundle,
    Category,
    Lead,
    Package,
    Review,
    Service,
)
from .serializers import (
    ONBOARD_STEPS,
    BundleCreateUpdateSerializer,
    BundleSerializer,
    CategoryTreeSerializer,
    LeadCreateSerializer,
    LeadDetailSerializer,
    LeadListSerializer,
    LeadMessageCreateSerializer,
    LeadMessageSerializer,
    LeadStatusUpdateSerializer,
    PackageCreateUpdateSerializer,
    PackageSerializer,
    ReviewCreateSerializer,
    ReviewResponseCreateSerializer,
    ReviewSerializer,
    ServiceCreateUpdateSerializer,
    ServiceDetailSerializer,
    ServiceListSerializer,
    VendorDetailSerializer,
    VendorOnboardStepSerializer,
    VendorPublicSerializer,
)

User = get_user_model()

PUBLIC_SERVICE_FILTER = Q(is_active=True, moderation_status="approved")


# ──────────────────────────────────────────────────────────────────────────
# Local permissions
# ──────────────────────────────────────────────────────────────────────────
class IsServiceOwner(permissions.BasePermission):
    """Object-level: vendor of the Service / Package / Bundle is the requester."""

    def has_object_permission(self, request, view, obj):
        # Service has .vendor.user; Package goes via .service.vendor.user;
        # Bundle has .vendor.user.
        owner_user_id = None
        if isinstance(obj, Service):
            owner_user_id = obj.vendor.user_id
        elif isinstance(obj, Package):
            owner_user_id = obj.service.vendor.user_id
        elif isinstance(obj, Bundle):
            owner_user_id = obj.vendor.user_id
        return owner_user_id == request.user.pk


class IsLeadParty(permissions.BasePermission):
    """Buyer or vendor of the lead."""

    def has_object_permission(self, request, view, obj: Lead) -> bool:
        return (obj.buyer_id == request.user.pk
                or obj.vendor.user_id == request.user.pk)


class IsLeadVendor(permissions.BasePermission):
    """Only the lead's vendor."""

    def has_object_permission(self, request, view, obj: Lead) -> bool:
        return obj.vendor.user_id == request.user.pk


class IsLeadBuyer(permissions.BasePermission):
    """Only the lead's buyer."""

    def has_object_permission(self, request, view, obj: Lead) -> bool:
        return obj.buyer_id == request.user.pk


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────
def _vendor_or_403(user) -> VendorProfile:
    profile = getattr(user, "vendor_profile", None)
    if not profile:
        raise PermissionDenied("Vendor profile required.")
    return profile


def _decimal_param(value: str | None) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError):
        return None


# ──────────────────────────────────────────────────────────────────────────
# Public — categories
# ──────────────────────────────────────────────────────────────────────────
class CategoryListView(generics.ListAPIView):
    """GET /public/v1/services/categories/ — full tree."""

    permission_classes = [permissions.AllowAny]
    serializer_class = CategoryTreeSerializer
    pagination_class = None

    def get_queryset(self):
        return Category.get_root_nodes()


# ──────────────────────────────────────────────────────────────────────────
# Public — services
# ──────────────────────────────────────────────────────────────────────────
class PublicServiceListView(generics.ListAPIView):
    """GET /public/v1/services/ — filterable, paginated."""

    permission_classes = [permissions.AllowAny]
    serializer_class = ServiceListSerializer
    pagination_class = TimeCursorPagination

    def get_queryset(self):
        qs = (Service.objects
              .filter(PUBLIC_SERVICE_FILTER)
              .select_related("vendor", "vendor__user", "category")
              .prefetch_related("packages")
              .annotate(packages_count=Count("packages", distinct=True)))

        params = self.request.query_params

        cat_slug = params.get("category")
        if cat_slug:
            cat = Category.objects.filter(slug=cat_slug).first()
            if cat:
                ids = [cat.pk, *cat.get_descendants().values_list("pk", flat=True)]
                qs = qs.filter(category_id__in=ids)

        vendor_slug = params.get("vendor")
        if vendor_slug:
            qs = qs.filter(vendor__slug=vendor_slug)

        min_price = _decimal_param(params.get("min_price"))
        max_price = _decimal_param(params.get("max_price"))
        if min_price is not None:
            qs = qs.filter(packages__price_low__gte=min_price)
        if max_price is not None:
            qs = qs.filter(packages__price_low__lte=max_price)

        if params.get("has_bundle") in ("1", "true", "yes"):
            qs = qs.filter(in_bundles__bundle__is_active=True,
                           in_bundles__bundle__moderation_status="approved").distinct()

        q = (params.get("q") or "").strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))

        return qs.distinct()


class PublicServiceDetailView(generics.RetrieveAPIView):
    """GET /public/v1/services/<slug>/."""

    permission_classes = [permissions.AllowAny]
    serializer_class = ServiceDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return (Service.objects
                .filter(PUBLIC_SERVICE_FILTER)
                .select_related("vendor", "vendor__user", "category")
                .prefetch_related("packages"))


class PublicPackageListView(generics.ListAPIView):
    """GET /public/v1/services/<service_slug>/packages/."""

    permission_classes = [permissions.AllowAny]
    serializer_class = PackageSerializer
    pagination_class = None

    def get_queryset(self):
        return (Package.objects
                .filter(service__slug=self.kwargs["service_slug"],
                        service__is_active=True,
                        service__moderation_status="approved")
                .order_by("price_low"))


# ──────────────────────────────────────────────────────────────────────────
# Public — vendors
# ──────────────────────────────────────────────────────────────────────────
class PublicVendorListView(generics.ListAPIView):
    """GET /public/v1/vendors/."""

    permission_classes = [permissions.AllowAny]
    serializer_class = VendorPublicSerializer
    pagination_class = TimeCursorPagination

    def get_queryset(self):
        qs = (VendorProfile.objects
              .filter(status=VendorProfile.Status.ACTIVE)
              .select_related("user"))

        params = self.request.query_params
        cat_slug = params.get("category")
        if cat_slug:
            cat = Category.objects.filter(slug=cat_slug).first()
            if cat:
                ids = [cat.pk, *cat.get_descendants().values_list("pk", flat=True)]
                qs = qs.filter(services__category_id__in=ids).distinct()

        q = (params.get("q") or "").strip()
        if q:
            qs = qs.filter(Q(business_name__icontains=q) | Q(tagline__icontains=q))
        return qs


class PublicVendorDetailView(generics.RetrieveAPIView):
    """GET /public/v1/vendors/<slug>/."""

    permission_classes = [permissions.AllowAny]
    serializer_class = VendorDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return (VendorProfile.objects
                .filter(status=VendorProfile.Status.ACTIVE)
                .select_related("user"))


class PublicVendorServicesView(generics.ListAPIView):
    """GET /public/v1/vendors/<vendor_slug>/services/."""

    permission_classes = [permissions.AllowAny]
    serializer_class = ServiceListSerializer
    pagination_class = TimeCursorPagination

    def get_queryset(self):
        return (Service.objects
                .filter(PUBLIC_SERVICE_FILTER, vendor__slug=self.kwargs["vendor_slug"])
                .select_related("vendor", "vendor__user", "category")
                .annotate(packages_count=Count("packages", distinct=True)))


# ──────────────────────────────────────────────────────────────────────────
# Private — services (vendor)
# ──────────────────────────────────────────────────────────────────────────
class ServiceCreateView(generics.CreateAPIView):
    """POST /v1/services/ — IsVendor."""

    permission_classes = [IsVendor]
    serializer_class = ServiceCreateUpdateSerializer

    def perform_create(self, serializer):
        vendor = _vendor_or_403(self.request.user)
        serializer.save(vendor=vendor)


class ServiceUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /v1/services/<slug>/."""

    permission_classes = [IsVendor, IsServiceOwner]
    serializer_class = ServiceCreateUpdateSerializer
    lookup_field = "slug"

    def get_queryset(self):
        # Vendor sees own services regardless of moderation_status.
        return (Service.objects
                .select_related("vendor", "vendor__user", "category"))

    def perform_destroy(self, instance: Service):
        # Soft delete via deactivation — preserves leads + reviews FKs.
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])


# ──────────────────────────────────────────────────────────────────────────
# Private — packages (per service)
# ──────────────────────────────────────────────────────────────────────────
class PackageListCreateView(generics.ListCreateAPIView):
    """GET/POST /v1/services/<service_slug>/packages/."""

    permission_classes = [IsVendor]
    serializer_class = PackageCreateUpdateSerializer
    pagination_class = None

    def _get_service(self) -> Service:
        vendor = _vendor_or_403(self.request.user)
        service = get_object_or_404(
            Service.objects.select_related("vendor"),
            slug=self.kwargs["service_slug"], vendor=vendor,
        )
        return service

    def get_queryset(self):
        return self._get_service().packages.order_by("price_low")

    def perform_create(self, serializer):
        serializer.save(service=self._get_service())


class PackageUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /v1/services/packages/<id>/."""

    permission_classes = [IsVendor, IsServiceOwner]
    serializer_class = PackageCreateUpdateSerializer

    def get_queryset(self):
        return Package.objects.select_related("service__vendor")


# ──────────────────────────────────────────────────────────────────────────
# Private — bundles (per vendor)
# ──────────────────────────────────────────────────────────────────────────
class BundleListCreateView(generics.ListCreateAPIView):
    """GET/POST /v1/services/bundles/."""

    permission_classes = [IsVendor]
    pagination_class = TimeCursorPagination

    def get_serializer_class(self):
        if self.request.method == "POST":
            return BundleCreateUpdateSerializer
        return BundleSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["vendor"] = _vendor_or_403(self.request.user)
        return ctx

    def get_queryset(self):
        vendor = _vendor_or_403(self.request.user)
        return (Bundle.objects
                .filter(vendor=vendor)
                .prefetch_related("items__service"))


class BundleUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /v1/services/bundles/<slug>/."""

    permission_classes = [IsVendor, IsServiceOwner]
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return BundleCreateUpdateSerializer
        return BundleSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["vendor"] = _vendor_or_403(self.request.user)
        return ctx

    def get_queryset(self):
        return Bundle.objects.select_related("vendor", "vendor__user").prefetch_related(
            "items__service",
        )


# ──────────────────────────────────────────────────────────────────────────
# Private — vendor onboard wizard
# ──────────────────────────────────────────────────────────────────────────
class VendorOnboardStepView(generics.GenericAPIView):
    """POST/PATCH /v1/vendors/onboard/<step>/.

    Step keys: business | categories | services | gallery | publish.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = VendorOnboardStepSerializer

    def _step(self) -> str:
        step = self.kwargs.get("step")
        if step not in ONBOARD_STEPS:
            raise ValidationError({"step": f"Must be one of {ONBOARD_STEPS}."})
        return step

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        return self._handle(request, partial=False)

    def patch(self, request, *args, **kwargs):
        return self._handle(request, partial=True)

    def _handle(self, request, *, partial: bool):
        step = self._step()
        ser = self.get_serializer(data=request.data, partial=partial)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        user = request.user
        profile = getattr(user, "vendor_profile", None)

        if step == "business":
            business_name = data.get("business_name", "").strip()
            if not business_name and not profile:
                raise ValidationError({"business_name": "Required to start onboarding."})
            if not profile:
                slug = self._unique_vendor_slug(business_name)
                profile = VendorProfile.objects.create(
                    user=user, business_name=business_name, slug=slug,
                    tagline=data.get("tagline", ""), website=data.get("website", ""),
                    status=VendorProfile.Status.DRAFT,
                )
                user.is_vendor = True
                user.save(update_fields=["is_vendor", "updated_at"])
            else:
                if business_name:
                    profile.business_name = business_name
                if "tagline" in data:
                    profile.tagline = data["tagline"]
                if "website" in data:
                    profile.website = data["website"]
                profile.save()
            return Response(
                {"step": step, "vendor_slug": profile.slug, "status": profile.status},
                status=status.HTTP_200_OK,
            )

        if not profile:
            raise ValidationError("Complete the business step first.")

        if step in ("categories", "services", "gallery"):
            # Stored on the profile as side-effects in the wizard's session payload.
            # For now, treat these steps as autosave no-ops at the DB level — the
            # actual category/service/image wiring happens via dedicated endpoints.
            # TODO(phase-5.2): persist wizard scratchpad to a JSONField or session.
            return Response(
                {"step": step, "saved": True, "echo": data},
                status=status.HTTP_200_OK,
            )

        if step == "publish":
            if not data.get("accept_terms"):
                raise ValidationError({"accept_terms": "You must accept the terms."})
            # Move to ACTIVE — admin can flip to SUSPENDED on review.
            # ACCESS-MATRIX says "Vendor application under review" → status remains
            # DRAFT until ops approves; flipping to ACTIVE is op-only. We instead
            # leave status=DRAFT and surface a `submitted_at` flag.
            # TODO(phase-5.2): add VendorProfile.submitted_at + ops review flow.
            profile.save()
            return Response(
                {"step": step, "status": profile.status, "submitted": True},
                status=status.HTTP_200_OK,
            )

        # Unreachable.
        raise ValidationError({"step": "Unhandled step."})

    @staticmethod
    def _unique_vendor_slug(business_name: str) -> str:
        base = slugify(business_name)[:180] or "vendor"
        slug = base
        i = 2
        while VendorProfile.objects.filter(slug=slug).exists():
            slug = f"{base}-{i}"[:200]
            i += 1
        return slug


class VendorProfileMeView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /v1/vendors/me/. Tagline goes through moderation via signals."""

    permission_classes = [IsVendor]
    serializer_class = VendorDetailSerializer

    def get_object(self):
        return _vendor_or_403(self.request.user)


# ──────────────────────────────────────────────────────────────────────────
# Leads
# ──────────────────────────────────────────────────────────────────────────
class LeadCreateView(generics.CreateAPIView):
    """POST /v1/leads/ — IsAuthenticated, throttle 5/hr."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [LeadThrottle]
    serializer_class = LeadCreateSerializer

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        lead = ser.save()
        return Response(LeadDetailSerializer(lead).data, status=status.HTTP_201_CREATED)


class MyLeadListView(generics.ListAPIView):
    """GET /v1/leads/me/ — buyer + vendor view (filtered)."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LeadListSerializer
    pagination_class = TimeCursorPagination

    def get_queryset(self):
        user = self.request.user
        as_role = (self.request.query_params.get("as") or "both").lower()
        status_param = self.request.query_params.get("status")

        qs = (Lead.objects
              .select_related("vendor", "vendor__user", "buyer",
                              "service", "service__vendor", "package", "bundle")
              .order_by("-created_at"))

        vendor_profile = getattr(user, "vendor_profile", None)
        if as_role == "buyer":
            qs = qs.filter(buyer=user)
        elif as_role == "vendor":
            if not vendor_profile:
                return qs.none()
            qs = qs.filter(vendor=vendor_profile)
        else:
            cond = Q(buyer=user)
            if vendor_profile:
                cond |= Q(vendor=vendor_profile)
            qs = qs.filter(cond)

        if status_param:
            qs = qs.filter(status=status_param)
        return qs


class LeadDetailView(generics.RetrieveAPIView):
    """GET /v1/leads/<id>/ — party only."""

    permission_classes = [permissions.IsAuthenticated, IsLeadParty]
    serializer_class = LeadDetailSerializer

    def get_queryset(self):
        return (Lead.objects
                .select_related("vendor", "vendor__user", "buyer",
                                "service", "package", "bundle")
                .prefetch_related("messages"))


class LeadStatusUpdateView(generics.UpdateAPIView):
    """PATCH /v1/leads/<id>/status/ — vendor only."""

    permission_classes = [IsVendor, IsLeadVendor]
    serializer_class = LeadStatusUpdateSerializer
    http_method_names = ["patch", "options", "head"]

    def get_queryset(self):
        return Lead.objects.select_related("vendor", "vendor__user")

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        ser = self.get_serializer(instance, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.update(instance, ser.validated_data)
        return Response(LeadDetailSerializer(instance).data)


# ──────────────────────────────────────────────────────────────────────────
# Lead messages
# ──────────────────────────────────────────────────────────────────────────
class LeadMessageListCreateView(generics.ListCreateAPIView):
    """GET/POST /v1/leads/<lead_id>/messages/ — party only."""

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = TimeCursorPagination

    def get_serializer_class(self):
        return (LeadMessageCreateSerializer if self.request.method == "POST"
                else LeadMessageSerializer)

    def _lead(self) -> Lead:
        lead = get_object_or_404(
            Lead.objects.select_related("vendor", "vendor__user"),
            pk=self.kwargs["lead_id"],
        )
        if not (lead.buyer_id == self.request.user.pk
                or lead.vendor.user_id == self.request.user.pk):
            raise PermissionDenied("Not a party to this lead.")
        return lead

    def get_queryset(self):
        return (self._lead().messages
                .select_related("sender")
                .order_by("created_at"))

    def perform_create(self, serializer):
        lead = self._lead()
        serializer.save(lead=lead, sender=self.request.user)


# ──────────────────────────────────────────────────────────────────────────
# Reviews
# ──────────────────────────────────────────────────────────────────────────
class ReviewCreateView(generics.CreateAPIView):
    """POST /v1/leads/<lead_id>/review/ — buyer + lead `won` only."""

    permission_classes = [permissions.IsAuthenticated, IsLeadBuyer]
    serializer_class = ReviewCreateSerializer

    def _lead(self) -> Lead:
        lead = get_object_or_404(
            Lead.objects.select_related("vendor", "vendor__user", "buyer"),
            pk=self.kwargs["lead_id"],
        )
        # Object-level check via the dedicated permission.
        self.check_object_permissions(self.request, lead)
        return lead

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["lead"] = self._lead()
        return ctx

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        review = ser.save()
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)


class ReviewResponseCreateView(generics.GenericAPIView):
    """POST /v1/leads/reviews/<id>/response/ — vendor of the lead only."""

    permission_classes = [IsVendor]
    serializer_class = ReviewResponseCreateSerializer

    def get_queryset(self):
        return Review.objects.select_related("lead__vendor", "lead__vendor__user")

    def post(self, request, *args, **kwargs):
        review = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        if review.lead.vendor.user_id != request.user.pk:
            raise PermissionDenied("Only the vendor on the lead can respond.")
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.update(review, ser.validated_data)
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)
