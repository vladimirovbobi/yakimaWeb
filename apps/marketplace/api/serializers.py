"""Marketplace serializers — public + private + lead/review flows.

Models reference:
- Service (ModeratableMixin) has: vendor, category, title, slug, description,
  hero_image, response_time_hours, is_active, moderation_status.
- Package has: service, tier, name, description, price_low, price_high,
  delivery_days, revisions, features (JSON list).
- Bundle (ModeratableMixin) has: vendor, name, slug, description, price_total,
  billing_cadence, min_term_months, is_active.
- BundleItem has: bundle, service, quantity_per_period, fulfillment_note,
  sort_order.
- Lead has: vendor, buyer, service, package, bundle, message, status, won_at,
  lost_at.
- LeadMessage has: lead, sender, body.
- Review (ModeratableMixin) has: lead, rating, body, vendor_response,
  vendor_response_at.

The ICD uses "title" for Service display name; the model field is `title`.
The ICD uses `description_html`; we sanitize-render markdown on output.
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Avg, Count
from django.utils import timezone
from rest_framework import serializers

from apps.accounts.api.serializers import PublicUserSerializer
from apps.accounts.models import VendorProfile
from apps.content.services.sanitize import render_markdown

from ..models import (
    BillingCadence,
    Bundle,
    BundleItem,
    Category,
    Lead,
    LeadMessage,
    LeadStatus,
    Package,
    PackageTier,
    Review,
    Service,
)

User = get_user_model()


# ──────────────────────────────────────────────────────────────────────────
# Categories (treebeard MP_Node)
# ──────────────────────────────────────────────────────────────────────────
class CategoryNodeSerializer(serializers.ModelSerializer):
    """Flat node — no children. Used in lists + path crumbs."""

    depth = serializers.SerializerMethodField()
    parent = serializers.SerializerMethodField()
    children_count = serializers.SerializerMethodField()
    name = serializers.CharField(source="label", read_only=True)

    class Meta:
        model = Category
        fields = ("id", "slug", "name", "icon", "depth", "parent", "children_count")
        read_only_fields = fields

    def get_depth(self, obj: Category) -> int:
        return obj.depth

    def get_parent(self, obj: Category) -> int | None:
        parent = obj.get_parent()
        return parent.pk if parent else None

    def get_children_count(self, obj: Category) -> int:
        return obj.get_children_count()


class CategoryTreeSerializer(serializers.ModelSerializer):
    """Recursive — caps at 3 levels. Yakima category trees are shallow."""

    name = serializers.CharField(source="label", read_only=True)
    depth = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "slug", "name", "icon", "depth", "children")
        read_only_fields = fields

    def get_depth(self, obj: Category) -> int:
        return obj.depth

    def get_children(self, obj: Category) -> list:
        if obj.depth >= 3:
            return []
        kids = obj.get_children()
        if not kids:
            return []
        return CategoryTreeSerializer(kids, many=True, context=self.context).data


# ──────────────────────────────────────────────────────────────────────────
# Vendor (public-facing surface for marketplace listings)
# ──────────────────────────────────────────────────────────────────────────
class VendorPublicSerializer(serializers.ModelSerializer):
    """Compact vendor card for service lists + cross-references."""

    display_name = serializers.CharField(source="business_name", read_only=True)
    response_time_hours = serializers.SerializerMethodField()
    services_count = serializers.SerializerMethodField()
    rating_avg = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    verified = serializers.SerializerMethodField()

    class Meta:
        model = VendorProfile
        fields = (
            "id", "slug", "business_name", "display_name", "tagline", "website",
            "response_time_hours", "services_count", "rating_avg", "review_count",
            "verified",
        )
        read_only_fields = fields

    def get_response_time_hours(self, obj: VendorProfile) -> int | None:
        agg = obj.services.filter(is_active=True).aggregate(v=Avg("response_time_hours"))
        v = agg.get("v")
        return int(v) if v is not None else None

    def get_services_count(self, obj: VendorProfile) -> int:
        return obj.services.filter(is_active=True, moderation_status="approved").count()

    def get_rating_avg(self, obj: VendorProfile) -> float | None:
        agg = (Review.objects
               .filter(lead__vendor=obj, moderation_status="approved")
               .aggregate(v=Avg("rating")))
        v = agg.get("v")
        return round(float(v), 2) if v is not None else None

    def get_review_count(self, obj: VendorProfile) -> int:
        return Review.objects.filter(
            lead__vendor=obj, moderation_status="approved",
        ).count()

    def get_verified(self, obj: VendorProfile) -> bool:
        return obj.status == VendorProfile.Status.ACTIVE


class VendorDetailSerializer(VendorPublicSerializer):
    """Adds long-form fields. Used on /vendors/<slug>/."""

    user = PublicUserSerializer(read_only=True)

    class Meta(VendorPublicSerializer.Meta):
        fields = (
            *VendorPublicSerializer.Meta.fields,
            "user", "status",
        )


# ──────────────────────────────────────────────────────────────────────────
# Packages
# ──────────────────────────────────────────────────────────────────────────
class PackageSerializer(serializers.ModelSerializer):
    """Read-only nested view inside a service."""

    class Meta:
        model = Package
        fields = (
            "id", "tier", "name", "description",
            "price_low", "price_high", "delivery_days", "revisions", "features",
        )
        read_only_fields = fields


class PackageCreateUpdateSerializer(serializers.ModelSerializer):
    """Vendor-only write serializer. service is set by the view."""

    class Meta:
        model = Package
        fields = (
            "id", "tier", "name", "description",
            "price_low", "price_high", "delivery_days", "revisions", "features",
        )
        read_only_fields = ("id",)

    def validate_tier(self, value: str) -> str:
        if value not in dict(PackageTier.choices):
            raise serializers.ValidationError("Unknown tier.")
        return value

    def validate_features(self, value):
        if value in (None, ""):
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError("features must be a list of strings.")
        if not all(isinstance(x, str) for x in value):
            raise serializers.ValidationError("features must be a list of strings.")
        if len(value) > 24:
            raise serializers.ValidationError("Max 24 features.")
        return [s.strip()[:160] for s in value if s.strip()]

    def validate(self, attrs: dict) -> dict:
        low = attrs.get("price_low")
        high = attrs.get("price_high", low)
        if low is not None and high is not None and Decimal(high) < Decimal(low):
            raise serializers.ValidationError({"price_high": "Must be ≥ price_low."})
        return attrs


# ──────────────────────────────────────────────────────────────────────────
# Bundles
# ──────────────────────────────────────────────────────────────────────────
class BundleItemSerializer(serializers.ModelSerializer):
    """Read-side: includes a compact Service block."""

    service = serializers.SerializerMethodField()

    class Meta:
        model = BundleItem
        fields = ("id", "service", "quantity_per_period", "fulfillment_note", "sort_order")
        read_only_fields = fields

    def get_service(self, obj: BundleItem) -> dict:
        s = obj.service
        return {
            "id": s.pk, "slug": s.slug, "title": s.title,
            "category_slug": s.category.slug if s.category_id else None,
        }


class BundleItemWriteSerializer(serializers.Serializer):
    """Write-side: bundle item by service slug."""

    service_slug = serializers.SlugField(max_length=160)
    quantity_per_period = serializers.IntegerField(min_value=1, max_value=999, default=1)
    fulfillment_note = serializers.CharField(required=False, allow_blank=True, max_length=240)
    sort_order = serializers.IntegerField(min_value=0, max_value=999, default=0)


class BundleSerializer(serializers.ModelSerializer):
    """Read-only nested + standalone view."""

    items = BundleItemSerializer(many=True, read_only=True)
    cadence = serializers.CharField(source="billing_cadence", read_only=True)

    class Meta:
        model = Bundle
        fields = (
            "id", "slug", "name", "description",
            "price_total", "billing_cadence", "cadence",
            "min_term_months", "is_active", "items", "created_at",
        )
        read_only_fields = fields


class BundleCreateUpdateSerializer(serializers.ModelSerializer):
    """Vendor write — accepts nested items by service slug."""

    items = BundleItemWriteSerializer(many=True, required=False)

    class Meta:
        model = Bundle
        fields = (
            "id", "name", "description",
            "price_total", "billing_cadence", "min_term_months", "is_active", "items",
        )
        read_only_fields = ("id",)

    def validate_billing_cadence(self, value: str) -> str:
        if value not in dict(BillingCadence.choices):
            raise serializers.ValidationError("Unknown cadence.")
        return value

    def _attach_items(self, bundle: Bundle, items_data: list) -> None:
        # Validate all service slugs belong to the bundle's vendor.
        slugs = [it["service_slug"] for it in items_data]
        services = {s.slug: s for s in Service.objects.filter(
            slug__in=slugs, vendor=bundle.vendor,
        )}
        missing = [slug for slug in slugs if slug not in services]
        if missing:
            raise serializers.ValidationError({"items": f"Unknown service slugs: {missing}"})
        bundle.items.all().delete()
        BundleItem.objects.bulk_create([
            BundleItem(
                bundle=bundle,
                service=services[it["service_slug"]],
                quantity_per_period=it.get("quantity_per_period", 1),
                fulfillment_note=it.get("fulfillment_note", ""),
                sort_order=it.get("sort_order", 0),
            )
            for it in items_data
        ])

    @transaction.atomic
    def create(self, validated_data: dict) -> Bundle:
        items_data = validated_data.pop("items", [])
        vendor = self.context["vendor"]
        bundle = Bundle.objects.create(vendor=vendor, **validated_data)
        if items_data:
            self._attach_items(bundle, items_data)
        return bundle

    @transaction.atomic
    def update(self, instance: Bundle, validated_data: dict) -> Bundle:
        items_data = validated_data.pop("items", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        if items_data is not None:
            self._attach_items(instance, items_data)
        return instance


# ──────────────────────────────────────────────────────────────────────────
# Services
# ──────────────────────────────────────────────────────────────────────────
class _ServiceCategoryEmbed(serializers.ModelSerializer):
    name = serializers.CharField(source="label", read_only=True)

    class Meta:
        model = Category
        fields = ("slug", "name")
        read_only_fields = fields


class ServiceListSerializer(serializers.ModelSerializer):
    """One row in /services/. Fast path — no description, no portfolio."""

    vendor = VendorPublicSerializer(read_only=True)
    category = _ServiceCategoryEmbed(read_only=True)
    starting_price_cents = serializers.SerializerMethodField()
    cover_image = serializers.SerializerMethodField()
    packages_count = serializers.IntegerField(read_only=True)
    has_bundle = serializers.SerializerMethodField()
    rating_avg = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    lead_count_30d = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = (
            "id", "slug", "title",
            "vendor", "category",
            "starting_price_cents", "currency",
            "packages_count", "has_bundle",
            "cover_image", "summary",
            "rating_avg", "review_count", "lead_count_30d",
            "response_time_hours", "is_active", "created_at",
        )
        read_only_fields = fields

    currency = serializers.SerializerMethodField()

    def get_currency(self, _obj: Service) -> str:
        return "USD"

    def get_starting_price_cents(self, obj: Service) -> int | None:
        # Prefer prefetched min if the view annotated it; else compute.
        first = getattr(obj, "_starting_price_low", None)
        if first is None:
            pkg = obj.packages.order_by("price_low").first()
            first = pkg.price_low if pkg else None
        return int(Decimal(first) * 100) if first is not None else None

    def get_cover_image(self, obj: Service) -> dict | None:
        if not obj.hero_image:
            return None
        try:
            return {"url": obj.hero_image.url, "blurhash": None}
        except (ValueError, AttributeError):
            return None

    def get_has_bundle(self, obj: Service) -> bool:
        return obj.in_bundles.filter(
            bundle__is_active=True, bundle__moderation_status="approved",
        ).exists()

    def get_rating_avg(self, obj: Service) -> float | None:
        agg = (Review.objects
               .filter(lead__service=obj, moderation_status="approved")
               .aggregate(v=Avg("rating")))
        v = agg.get("v")
        return round(float(v), 2) if v is not None else None

    def get_review_count(self, obj: Service) -> int:
        return Review.objects.filter(
            lead__service=obj, moderation_status="approved",
        ).count()

    def get_lead_count_30d(self, obj: Service) -> int:
        cutoff = timezone.now() - timedelta(days=30)
        return obj.leads.filter(created_at__gte=cutoff).count()

    def get_summary(self, obj: Service) -> str:
        text = (obj.description or "").strip()
        if len(text) <= 160:
            return text
        return text[:157].rstrip() + "…"


class ServiceDetailSerializer(ServiceListSerializer):
    """Full service detail — sanitized HTML body, packages, bundles, reviews summary."""

    description_html = serializers.SerializerMethodField()
    packages = PackageSerializer(many=True, read_only=True)
    bundles = serializers.SerializerMethodField()
    reviews_summary = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    class Meta(ServiceListSerializer.Meta):
        fields = (
            *ServiceListSerializer.Meta.fields,
            "description", "description_html", "packages", "bundles",
            "reviews_summary",
        )

    def get_description_html(self, obj: Service) -> str:
        return render_markdown(obj.description or "")

    def get_bundles(self, obj: Service) -> list:
        bundles = (Bundle.objects
                   .filter(items__service=obj, is_active=True,
                           moderation_status="approved")
                   .distinct()
                   .prefetch_related("items__service"))
        return BundleSerializer(bundles, many=True, context=self.context).data

    def get_reviews_summary(self, obj: Service) -> dict:
        rows = (Review.objects
                .filter(lead__service=obj, moderation_status="approved")
                .values("rating")
                .annotate(c=Count("id")))
        total = sum(r["c"] for r in rows)
        avg = (sum(r["rating"] * r["c"] for r in rows) / total) if total else None
        breakdown = {str(i): 0 for i in range(1, 6)}
        for r in rows:
            breakdown[str(r["rating"])] = r["c"]
        return {
            "average": round(float(avg), 2) if avg is not None else None,
            "count": total,
            "breakdown": breakdown,
        }

    def get_category(self, obj: Service) -> dict:
        c = obj.category
        if not c:
            return {}
        ancestors = [{"slug": a.slug, "name": a.label} for a in c.get_ancestors()]
        return {"slug": c.slug, "name": c.label, "ancestors": ancestors}


class ServiceCreateUpdateSerializer(serializers.ModelSerializer):
    """Vendor write — moderation runs via post-save signal."""

    category = serializers.SlugRelatedField(slug_field="slug", queryset=Category.objects.all())

    class Meta:
        model = Service
        fields = (
            "id", "title", "category", "description",
            "hero_image", "response_time_hours", "is_active",
        )
        read_only_fields = ("id",)

    def validate_description(self, value: str) -> str:
        text = (value or "").strip()
        if len(text) < 60:
            raise serializers.ValidationError(
                "Description must be at least 60 characters.",
            )
        return text


# ──────────────────────────────────────────────────────────────────────────
# Vendor onboarding wizard
# ──────────────────────────────────────────────────────────────────────────
ONBOARD_STEPS = ("business", "categories", "services", "gallery", "publish")


class VendorOnboardStepSerializer(serializers.Serializer):
    """Per-step input. Step 1 (business) creates the VendorProfile draft."""

    # business
    business_name = serializers.CharField(max_length=200, required=False)
    tagline = serializers.CharField(max_length=160, required=False, allow_blank=True)
    website = serializers.URLField(required=False, allow_blank=True)
    contact_phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    about = serializers.CharField(required=False, allow_blank=True, max_length=2000)

    # categories — list of slugs
    categories = serializers.ListField(
        child=serializers.SlugField(max_length=80),
        required=False, allow_empty=True, max_length=12,
    )

    # services — list of {title, description, price_low, price_high, packages[], hero_url}
    services = serializers.ListField(
        child=serializers.DictField(), required=False, allow_empty=True, max_length=24,
    )

    # gallery — list of {url, alt, caption} dicts (or plain URLs accepted)
    gallery = serializers.ListField(
        child=serializers.JSONField(), required=False, allow_empty=True, max_length=24,
    )

    # publish — terms acceptance
    accept_terms = serializers.BooleanField(required=False, default=False)


# ──────────────────────────────────────────────────────────────────────────
# Leads
# ──────────────────────────────────────────────────────────────────────────
class _ServiceCompactSerializer(serializers.ModelSerializer):
    """Mini service block embedded in leads."""

    vendor_slug = serializers.CharField(source="vendor.slug", read_only=True)

    class Meta:
        model = Service
        fields = ("id", "slug", "title", "vendor_slug")
        read_only_fields = fields


class _BundleCompactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bundle
        fields = ("id", "slug", "name")
        read_only_fields = fields


class _PackageCompactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = ("id", "tier", "name", "price_low", "price_high")
        read_only_fields = fields


class LeadCreateSerializer(serializers.Serializer):
    """POST /leads/ — buyer creates an inquiry. XOR (service|bundle)."""

    service = serializers.SlugField(max_length=160, required=False, allow_null=True)
    package_id = serializers.IntegerField(required=False, allow_null=True)
    bundle = serializers.SlugField(max_length=160, required=False, allow_null=True)
    message = serializers.CharField(min_length=10, max_length=2000)
    # Optional buyer-supplied display fields kept for parity with public form fields.
    buyer_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    buyer_email = serializers.EmailField(required=False, allow_blank=True)
    buyer_phone = serializers.CharField(max_length=32, required=False, allow_blank=True)

    def validate(self, attrs: dict) -> dict:
        service_slug = attrs.get("service")
        bundle_slug = attrs.get("bundle")
        if bool(service_slug) == bool(bundle_slug):
            raise serializers.ValidationError(
                "Specify exactly one of `service` or `bundle`.",
            )
        request = self.context["request"]

        if service_slug:
            service = (Service.objects
                       .filter(slug=service_slug, is_active=True,
                               moderation_status="approved")
                       .select_related("vendor")
                       .first())
            if not service:
                raise serializers.ValidationError({"service": "Not found."})
            if service.vendor.user_id == request.user.pk:
                raise serializers.ValidationError(
                    "You cannot inquire about your own service.",
                )
            attrs["_service"] = service
            attrs["_vendor"] = service.vendor
            pkg_id = attrs.get("package_id")
            if pkg_id:
                pkg = service.packages.filter(pk=pkg_id).first()
                if not pkg:
                    raise serializers.ValidationError(
                        {"package_id": "Package not part of this service."},
                    )
                attrs["_package"] = pkg
        else:
            bundle = (Bundle.objects
                      .filter(slug=bundle_slug, is_active=True,
                              moderation_status="approved")
                      .select_related("vendor")
                      .first())
            if not bundle:
                raise serializers.ValidationError({"bundle": "Not found."})
            if bundle.vendor.user_id == request.user.pk:
                raise serializers.ValidationError(
                    "You cannot inquire about your own bundle.",
                )
            attrs["_bundle"] = bundle
            attrs["_vendor"] = bundle.vendor
        return attrs

    def create(self, validated_data: dict) -> Lead:
        request = self.context["request"]
        return Lead.objects.create(
            vendor=validated_data["_vendor"],
            buyer=request.user,
            service=validated_data.get("_service"),
            package=validated_data.get("_package"),
            bundle=validated_data.get("_bundle"),
            message=validated_data["message"][:2000],
        )


class LeadListSerializer(serializers.ModelSerializer):
    service = _ServiceCompactSerializer(read_only=True)
    package = _PackageCompactSerializer(read_only=True)
    bundle = _BundleCompactSerializer(read_only=True)
    vendor = VendorPublicSerializer(read_only=True)
    buyer = PublicUserSerializer(read_only=True)
    message_excerpt = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = (
            "id", "vendor", "buyer", "service", "package", "bundle",
            "status", "message_excerpt", "created_at",
        )
        read_only_fields = fields

    def get_message_excerpt(self, obj: Lead) -> str:
        text = (obj.message or "").strip()
        return text[:160] + ("…" if len(text) > 160 else "")


class LeadDetailSerializer(LeadListSerializer):
    """Adds full message + thread metadata."""

    messages_count = serializers.SerializerMethodField()
    latest_message = serializers.SerializerMethodField()
    review_id = serializers.SerializerMethodField()

    class Meta(LeadListSerializer.Meta):
        fields = (
            *LeadListSerializer.Meta.fields,
            "message", "won_at", "lost_at",
            "messages_count", "latest_message", "review_id",
        )

    def get_messages_count(self, obj: Lead) -> int:
        return obj.messages.count()

    def get_latest_message(self, obj: Lead) -> dict | None:
        m = obj.messages.order_by("-created_at").first()
        if not m:
            return None
        return {
            "id": m.pk,
            "sender_id": m.sender_id,
            "body": m.body[:200],
            "created_at": m.created_at,
        }

    def get_review_id(self, obj: Lead) -> int | None:
        return getattr(getattr(obj, "review", None), "pk", None)


class LeadStatusUpdateSerializer(serializers.Serializer):
    """Vendor flips status. Won → set won_at; Lost → set lost_at."""

    status = serializers.ChoiceField(choices=LeadStatus.choices)
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def update(self, instance: Lead, validated_data: dict) -> Lead:
        new_status = validated_data["status"]
        instance.status = new_status
        now = timezone.now()
        if new_status == LeadStatus.WON and not instance.won_at:
            instance.won_at = now
        if new_status == LeadStatus.LOST and not instance.lost_at:
            instance.lost_at = now
        instance.save(update_fields=["status", "won_at", "lost_at", "updated_at"])
        return instance


# ──────────────────────────────────────────────────────────────────────────
# Lead messages
# ──────────────────────────────────────────────────────────────────────────
class LeadMessageSerializer(serializers.ModelSerializer):
    sender = PublicUserSerializer(read_only=True)

    class Meta:
        model = LeadMessage
        fields = ("id", "lead", "sender", "body", "created_at")
        read_only_fields = ("id", "lead", "sender", "created_at")


class LeadMessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadMessage
        fields = ("body",)

    def validate_body(self, value: str) -> str:
        text = (value or "").strip()
        if not text:
            raise serializers.ValidationError("Message body required.")
        return text[:4000]


# ──────────────────────────────────────────────────────────────────────────
# Reviews
# ──────────────────────────────────────────────────────────────────────────
class ReviewSerializer(serializers.ModelSerializer):
    """Public-facing review (after moderation approval)."""

    reviewer = serializers.SerializerMethodField()
    response = serializers.CharField(source="vendor_response", read_only=True)
    response_at = serializers.DateTimeField(source="vendor_response_at", read_only=True)
    lead_id = serializers.IntegerField(source="lead.pk", read_only=True)

    class Meta:
        model = Review
        fields = (
            "id", "lead_id", "reviewer", "rating", "body",
            "response", "response_at", "moderation_status", "created_at",
        )
        read_only_fields = fields

    def get_reviewer(self, obj: Review) -> dict:
        return PublicUserSerializer(obj.lead.buyer).data


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Buyer-only — must own the lead and lead must be `won`."""

    class Meta:
        model = Review
        fields = ("rating", "body")

    def validate_rating(self, value: int) -> int:
        if not 1 <= int(value) <= 5:
            raise serializers.ValidationError("Rating must be 1-5.")
        return int(value)

    def validate(self, attrs: dict) -> dict:
        lead: Lead = self.context["lead"]
        request = self.context["request"]
        if lead.buyer_id != request.user.pk:
            raise serializers.ValidationError("Only the buyer can review this lead.")
        if not lead.can_be_reviewed:
            raise serializers.ValidationError(
                "Reviews are allowed only after the lead is marked won.",
            )
        if Review.objects.filter(lead=lead).exists():
            raise serializers.ValidationError("This lead already has a review.")
        return attrs

    def create(self, validated_data: dict) -> Review:
        return Review.objects.create(lead=self.context["lead"], **validated_data)


class ReviewResponseCreateSerializer(serializers.Serializer):
    """Vendor reply to a published review. One per review."""

    response = serializers.CharField(min_length=2, max_length=2000)

    def update(self, instance: Review, validated_data: dict) -> Review:
        if instance.vendor_response:
            raise serializers.ValidationError("Vendor response already exists.")
        instance.vendor_response = validated_data["response"][:2000]
        instance.vendor_response_at = timezone.now()
        instance.save(update_fields=["vendor_response", "vendor_response_at", "updated_at"])
        return instance


# Re-export for accounts to pull a richer vendor view if needed.
__all__ = (
    "CategoryNodeSerializer", "CategoryTreeSerializer",
    "PackageSerializer", "PackageCreateUpdateSerializer",
    "BundleItemSerializer", "BundleSerializer", "BundleCreateUpdateSerializer",
    "ServiceListSerializer", "ServiceDetailSerializer", "ServiceCreateUpdateSerializer",
    "VendorPublicSerializer", "VendorDetailSerializer",
    "VendorOnboardStepSerializer", "ONBOARD_STEPS",
    "LeadCreateSerializer", "LeadListSerializer", "LeadDetailSerializer",
    "LeadStatusUpdateSerializer",
    "LeadMessageSerializer", "LeadMessageCreateSerializer",
    "ReviewSerializer", "ReviewCreateSerializer", "ReviewResponseCreateSerializer",
)
