"""Marketplace: Category tree + Service + Package + Bundle + Lead + Review."""
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from treebeard.mp_tree import MP_Node

from apps.accounts.models import VendorProfile
from apps.core.models import TimeStampedModel
from apps.core.validators import MaxFileSizeValidator
from apps.moderation.models import ModeratableMixin


class Category(MP_Node):
    """Service category tree (max 3 levels). Photography → Real Estate Photography → Twilight."""
    slug  = models.SlugField(max_length=80, unique=True)
    label = models.CharField(max_length=80)
    icon  = models.CharField(max_length=32, blank=True)  # Lucide icon name

    node_order_by = ["label"]

    def __str__(self) -> str:
        return self.label

    @property
    def depth_label(self) -> str:
        return " / ".join([a.label for a in self.get_ancestors()] + [self.label])


class Service(ModeratableMixin, TimeStampedModel):
    """One service offering by a vendor."""
    vendor      = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name="services")
    category    = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="services")
    title       = models.CharField(max_length=140)
    slug        = models.SlugField(max_length=160, unique=True, blank=True)
    description = models.TextField(max_length=4000)
    hero_image  = models.ImageField(
        upload_to="marketplace/services/", null=True, blank=True,
        validators=[MaxFileSizeValidator(10)],
    )
    response_time_hours = models.PositiveIntegerField(default=24,
                                                      help_text="Promised response time")
    is_active   = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category", "is_active", "moderation_status"]),
            models.Index(fields=["vendor"]),
        ]

    def __str__(self) -> str:
        return f"{self.vendor.business_name}: {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = f"{slugify(self.vendor.business_name)}-{slugify(self.title)}"
            self.slug = base[:160]
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        # Next.js public route (ADR-0005 split). Server-rendered legacy templates removed in DEB-002.
        return f"/services/{self.slug}/"

    @property
    def price_from(self) -> Decimal | None:
        first = self.packages.order_by("price_low").first()
        return first.price_low if first else None


class PackageTier(models.TextChoices):
    BASIC    = "basic",    _("Basic")
    STANDARD = "standard", _("Standard")
    PREMIUM  = "premium",  _("Premium")


class Package(TimeStampedModel):
    """Per-service tier (Basic/Standard/Premium)."""
    service     = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="packages")
    tier        = models.CharField(max_length=10, choices=PackageTier.choices)
    name        = models.CharField(max_length=80)
    description = models.TextField(max_length=600)
    price_low   = models.DecimalField(max_digits=10, decimal_places=2)
    price_high  = models.DecimalField(max_digits=10, decimal_places=2,
                                      help_text="Equal to price_low for fixed pricing")
    delivery_days = models.PositiveIntegerField(default=7)
    revisions   = models.PositiveIntegerField(default=1)
    features    = models.JSONField(default=list, blank=True,
                                    help_text='["item 1", "item 2"]')

    class Meta:
        ordering = ["service", "price_low"]
        unique_together = [("service", "tier")]

    def __str__(self) -> str:
        return f"{self.service.title} / {self.get_tier_display()}"


class BillingCadence(models.TextChoices):
    ONE_TIME  = "one_time",  _("One-time")
    MONTHLY   = "monthly",   _("Monthly")
    QUARTERLY = "quarterly", _("Quarterly")
    ANNUAL    = "annual",    _("Annual")


class Bundle(ModeratableMixin, TimeStampedModel):
    """Cross-service recurring offering. Vendor's own packaging."""
    vendor       = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name="bundles")
    name         = models.CharField(max_length=120)
    slug         = models.SlugField(max_length=160, unique=True, blank=True)
    description  = models.TextField(max_length=2000)
    price_total  = models.DecimalField(max_digits=10, decimal_places=2)
    billing_cadence = models.CharField(max_length=10, choices=BillingCadence.choices,
                                       default=BillingCadence.MONTHLY)
    min_term_months = models.PositiveSmallIntegerField(default=1)
    is_active    = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.vendor.business_name}: {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = (slugify(self.vendor.business_name) + "-" + slugify(self.name))[:160]
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        # Next.js public route (ADR-0005 split). Server-rendered legacy templates removed in DEB-002.
        return f"/services/bundles/{self.slug}/"


class BundleItem(TimeStampedModel):
    """Line item: this bundle includes service X with quantity Y per period."""
    bundle              = models.ForeignKey(Bundle, on_delete=models.CASCADE, related_name="items")
    service             = models.ForeignKey(Service, on_delete=models.PROTECT,
                                             related_name="in_bundles")
    quantity_per_period = models.PositiveIntegerField(default=1)
    fulfillment_note    = models.CharField(max_length=240, blank=True)
    sort_order          = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["bundle", "sort_order"]


class LeadStatus(models.TextChoices):
    PENDING   = "pending",   _("Pending")
    CONTACTED = "contacted", _("Contacted")
    WON       = "won",       _("Won")
    LOST      = "lost",      _("Lost")


class Lead(TimeStampedModel):
    """Buyer requested a quote — funnel into vendor's queue. Reviews tied here."""
    vendor   = models.ForeignKey(VendorProfile, on_delete=models.PROTECT, related_name="leads")
    buyer    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                  related_name="leads_sent")
    service  = models.ForeignKey(Service, on_delete=models.PROTECT, null=True, blank=True,
                                  related_name="leads")
    package  = models.ForeignKey(Package, on_delete=models.PROTECT, null=True, blank=True,
                                  related_name="leads")
    bundle   = models.ForeignKey(Bundle, on_delete=models.PROTECT, null=True, blank=True,
                                  related_name="leads")
    message  = models.TextField(max_length=2000)
    status   = models.CharField(max_length=10, choices=LeadStatus.choices,
                                default=LeadStatus.PENDING, db_index=True)
    won_at   = models.DateTimeField(null=True, blank=True)
    lost_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["vendor", "status", "-created_at"]),
            models.Index(fields=["buyer", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.buyer} → {self.vendor} ({self.status})"

    @property
    def can_be_reviewed(self) -> bool:
        return self.status == LeadStatus.WON


class LeadMessage(ModeratableMixin, TimeStampedModel):
    """In-platform message thread for a lead. Phase 5.1 wires real-time."""
    lead   = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name="lead_messages_sent")
    body   = models.TextField(max_length=4000)
    attachment_url = models.URLField(blank=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["lead", "created_at"]),
            models.Index(fields=["moderation_status"]),
        ]


class Review(ModeratableMixin, TimeStampedModel):
    """Verified-transaction review. One per Lead. Vendor can respond once."""
    lead   = models.OneToOneField(Lead, on_delete=models.CASCADE, related_name="review")
    rating = models.PositiveSmallIntegerField()  # 1-5
    body   = models.TextField(max_length=2000)
    vendor_response = models.TextField(max_length=2000, blank=True)
    vendor_response_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                                    name="rating_in_range"),
        ]

    def __str__(self) -> str:
        return f"★{self.rating} for {self.lead.vendor}"
