"""Marketplace API views — public + private + leads.

Public surface = approved + active services/bundles, verified vendors.
Private surface = vendor self-management (services / packages / bundles /
profile / onboard) + buyer/vendor lead workflow.
"""
from __future__ import annotations

import json
import time
from decimal import Decimal, InvalidOperation

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import VendorProfile
from apps.core.api.pagination import TimeCursorPagination
from apps.core.api.permissions import IsVendor
from apps.core.api.throttling import LeadThrottle, MessageThrottle

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
            business_name = (data.get("business_name") or "").strip()
            if not business_name and not profile:
                raise ValidationError({"business_name": "Required to start onboarding."})
            if not profile:
                slug = self._unique_vendor_slug(business_name)
                profile = VendorProfile.objects.create(
                    user=user, business_name=business_name, slug=slug,
                    tagline=data.get("tagline", ""), website=data.get("website", ""),
                    about=data.get("about", ""),
                    contact_phone=data.get("contact_phone", ""),
                    status=VendorProfile.Status.DRAFT,
                )
                user.is_vendor = True
                user.save(update_fields=["is_vendor", "updated_at"])
            else:
                if business_name:
                    profile.business_name = business_name
                for f in ("tagline", "website", "contact_phone", "about"):
                    if f in data:
                        setattr(profile, f, data[f])
                profile.save()
            self._save_wizard(profile, "business", {
                "name": profile.business_name,
                "tagline": profile.tagline,
                "website": profile.website,
                "contact_phone": profile.contact_phone,
                "about": profile.about,
            }, next_step="categories")
            return Response(
                {"step": step, "vendor_slug": profile.slug,
                 "status": profile.status, "wizard_state": profile.wizard_state},
                status=status.HTTP_200_OK,
            )

        if not profile:
            raise ValidationError("Complete the business step first.")

        if step == "categories":
            self._save_wizard(profile, "categories",
                              data.get("categories", []),
                              next_step="services")
            return Response(
                {"step": step, "saved": True, "wizard_state": profile.wizard_state},
                status=status.HTTP_200_OK,
            )

        if step == "services":
            self._save_wizard(profile, "services",
                              data.get("services", []),
                              next_step="gallery")
            return Response(
                {"step": step, "saved": True, "wizard_state": profile.wizard_state},
                status=status.HTTP_200_OK,
            )

        if step == "gallery":
            self._save_wizard(profile, "gallery",
                              data.get("gallery", []),
                              next_step="publish")
            return Response(
                {"step": step, "saved": True, "wizard_state": profile.wizard_state},
                status=status.HTTP_200_OK,
            )

        if step == "publish":
            if not data.get("accept_terms"):
                raise ValidationError({"accept_terms": "You must accept the terms."})
            now = timezone.now()
            self._materialize_services(profile)
            profile.submitted_at = now
            self._save_wizard(profile, "publish",
                              {"submitted_at": now.isoformat()},
                              next_step="publish")
            # Status stays DRAFT — ops flips to ACTIVE on review.
            profile.save()
            # Best-effort notify the vendor that their submission was received.
            try:
                from apps.notifications.services import notify
                notify(
                    user, "vendor_submitted",
                    title="Vendor application submitted",
                    body="Your application is under review. Most vendors are "
                         "approved within 24 hours.",
                    link="/dashboard/vendor",
                )
            except Exception:  # noqa: BLE001
                pass
            # Notify operators so they can review the submission.
            try:
                from django.contrib.auth import get_user_model

                from apps.notifications.services import notify

                _User = get_user_model()
                ops = _User.objects.filter(
                    groups__name="operator", is_active=True,
                ).distinct()
                for op in ops:
                    notify(
                        op, "ops_alert",
                        title=f"Vendor submitted: {profile.business_name}"[:200],
                        body=f"Vendor #{profile.pk} submitted for review.",
                        link=f"/admin/marketplace/vendorprofile/{profile.pk}/change/",
                    )
            except Exception:  # noqa: BLE001
                pass
            return Response(
                {"step": step, "status": profile.status,
                 "submitted_at": profile.submitted_at,
                 "wizard_state": profile.wizard_state},
                status=status.HTTP_200_OK,
            )

        # Unreachable.
        raise ValidationError({"step": "Unhandled step."})

    @staticmethod
    def _materialize_services(profile: VendorProfile) -> int:
        """Create real Service + Package rows from `wizard_state.data.services`.

        Idempotent: services already created (matched by title) are skipped.
        Returns the number of newly created Service rows.
        """
        state_data = (profile.wizard_state or {}).get("data") or {}
        services_data: list[dict] = list(state_data.get("services") or [])
        category_slugs: list[str] = list(state_data.get("categories") or [])

        # Default category — first one in the wizard, else fall back to ANY root.
        default_cat: Category | None = None
        if category_slugs:
            default_cat = Category.objects.filter(slug=category_slugs[0]).first()
        if default_cat is None:
            default_cat = Category.objects.first()
        if default_cat is None:
            return 0  # marketplace not seeded; nothing we can do.

        existing_titles = set(profile.services.values_list("title", flat=True))
        created = 0
        for svc in services_data:
            title = (svc.get("title") or "").strip()
            if not title or title in existing_titles:
                continue
            cat = default_cat
            cat_slug = (svc.get("category") or "").strip()
            if cat_slug:
                cat = Category.objects.filter(slug=cat_slug).first() or default_cat
            description = (svc.get("description") or "").strip() or "Pending vendor description."
            response_hours = int(svc.get("response_time_hours") or 24)

            service = Service.objects.create(
                vendor=profile, category=cat,
                title=title[:140],
                description=description[:4000],
                response_time_hours=max(1, min(response_hours, 24 * 14)),
                is_active=False,  # ops flips to active on review
            )

            for pkg in (svc.get("packages") or []):
                tier = (pkg.get("tier") or "basic").strip().lower()
                if tier not in {"basic", "standard", "premium"}:
                    tier = "basic"
                try:
                    price_low = Decimal(str(pkg.get("price_low") or "0"))
                    price_high = Decimal(str(pkg.get("price_high") or price_low))
                except (InvalidOperation, TypeError):
                    continue
                try:
                    Package.objects.create(
                        service=service,
                        tier=tier,
                        name=(pkg.get("name") or tier.title())[:80],
                        description=(pkg.get("description") or "")[:600],
                        price_low=price_low,
                        price_high=price_high,
                        delivery_days=int(pkg.get("delivery_days") or 7),
                        revisions=int(pkg.get("revisions") or 1),
                        features=list(pkg.get("features") or []),
                    )
                except Exception:  # noqa: BLE001 — skip duplicate-tier or bad rows
                    continue

            created += 1
        return created

    @staticmethod
    def _save_wizard(profile: VendorProfile, step: str, value, *, next_step: str) -> None:
        state = dict(profile.wizard_state or {})
        data = dict(state.get("data") or {})
        data[step] = value
        completed = list(state.get("completed_steps") or [])
        if step not in completed:
            completed.append(step)
        state["data"] = data
        state["completed_steps"] = completed
        state["current_step"] = next_step
        profile.wizard_state = state
        profile.save(update_fields=["wizard_state", "submitted_at",
                                     "tagline", "website", "contact_phone",
                                     "about", "business_name", "updated_at"])

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
    """GET/POST /v1/leads/<lead_id>/messages/ — party only.

    Writes throttled at 10/min via MessageThrottle to keep chat civilized.
    """

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = TimeCursorPagination

    def get_throttles(self):
        if self.request.method == "POST":
            return [MessageThrottle()]
        return super().get_throttles()

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


# ──────────────────────────────────────────────────────────────────────────
# SSE — lead message stream
# ──────────────────────────────────────────────────────────────────────────
SSE_STREAM_TIMEOUT_SECONDS = 300         # hard close after 5 minutes
SSE_KEEPALIVE_SECONDS = 30               # ping cadence
SSE_POLL_SECONDS = 2                     # poll DB every 2s for new rows


def _sse_format(event: str, data: dict | str) -> bytes:
    """Encode a single SSE frame. `data` is JSON-serialized when dict-like."""
    body = data if isinstance(data, str) else json.dumps(data, default=str)
    return (f"event: {event}\n" f"data: {body}\n\n").encode("utf-8")


class LeadMessageStreamView(APIView):
    """GET /api/v1/streams/leads/<lead_id>/messages/ — SSE feed of new messages.

    Permission check happens BEFORE we open the stream. After the stream is
    open, we hold the request open for up to 5 minutes, polling DB every 2s
    for new LeadMessage rows after `last_seen_id` and emitting a `message`
    event for each. A `ping` event is emitted every 30s to keep proxies awake.
    """

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, lead_id: int):
        from ..models import Lead, LeadMessage
        lead = (Lead.objects
                .select_related("vendor", "vendor__user", "buyer")
                .filter(pk=lead_id).first())
        if lead is None:
            raise NotFound("Lead not found.")
        if not (lead.buyer_id == request.user.pk
                or lead.vendor.user_id == request.user.pk):
            raise PermissionDenied("Not a party to this lead.")

        try:
            last_seen_id = int(request.query_params.get("last_id") or 0)
        except (TypeError, ValueError):
            last_seen_id = 0

        # Capture the value before the generator starts so we don't keep
        # the request bound during iteration.
        lead_pk = lead.pk

        def stream():
            opened_at = time.monotonic()
            last_keepalive = opened_at
            cursor = last_seen_id
            yield _sse_format("open", {"lead_id": lead_pk, "since_id": cursor})
            while True:
                if time.monotonic() - opened_at > SSE_STREAM_TIMEOUT_SECONDS:
                    yield _sse_format("close", {"reason": "timeout"})
                    break
                msgs = list(LeadMessage.objects
                            .filter(lead_id=lead_pk, pk__gt=cursor)
                            .order_by("pk")
                            .values("id", "body", "sender_id", "created_at")[:50])
                for m in msgs:
                    yield _sse_format("message", m)
                    cursor = m["id"]
                now = time.monotonic()
                if now - last_keepalive >= SSE_KEEPALIVE_SECONDS:
                    yield _sse_format("ping", {})
                    last_keepalive = now
                time.sleep(SSE_POLL_SECONDS)

        resp = StreamingHttpResponse(stream(), content_type="text/event-stream")
        resp["Cache-Control"] = "no-cache, no-transform"
        resp["X-Accel-Buffering"] = "no"
        resp["Connection"] = "keep-alive"
        return resp
