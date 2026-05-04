"""Accounts: User, RealtorProfile, VendorProfile, LicenseCheck."""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel
from apps.core.validators import MaxFileSizeValidator
from .managers import UserManager


class Role(models.TextChoices):
    MEMBER  = "member",  _("Member")
    REALTOR = "realtor", _("Realtor")
    VENDOR  = "vendor",  _("Vendor")
    STAFF   = "staff",   _("Staff")
    ADMIN   = "admin",   _("Admin")


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """Email-login user. Roles via flags + display field."""

    email      = models.EmailField(_("email"), unique=True, db_index=True)
    full_name  = models.CharField(_("full name"), max_length=200, blank=True)
    avatar     = models.ImageField(
        upload_to="avatars/", null=True, blank=True,
        validators=[MaxFileSizeValidator(5)],
    )

    role       = models.CharField(max_length=12, choices=Role.choices, default=Role.MEMBER)
    is_realtor = models.BooleanField(default=False, db_index=True)
    is_vendor  = models.BooleanField(default=False, db_index=True)

    is_staff   = models.BooleanField(default=False)
    is_active  = models.BooleanField(default=True)
    last_seen  = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.email

    def get_full_name(self) -> str:
        return self.full_name or self.email

    def get_short_name(self) -> str:
        return (self.full_name or self.email).split()[0]

    def touch_last_seen(self) -> None:
        self.last_seen = timezone.now()
        self.save(update_fields=["last_seen"])


class LicenseType(models.TextChoices):
    BROKER             = "broker",             _("Broker")
    MANAGING_BROKER    = "managing_broker",    _("Managing Broker")
    DESIGNATED_BROKER  = "designated_broker",  _("Designated Broker")
    BRANCH_MANAGER     = "branch_manager",     _("Branch Manager")


class VerificationStatus(models.TextChoices):
    PENDING   = "pending",   _("Pending")
    VERIFIED  = "verified",  _("Verified")
    EXPIRED   = "expired",   _("Expired")
    SUSPENDED = "suspended", _("Suspended")
    REVOKED   = "revoked",   _("Revoked")
    NOT_FOUND = "not_found", _("Not found")
    ERROR     = "error",     _("Error")


class RealtorProfile(TimeStampedModel):
    """Verified WA real estate licensee."""

    user            = models.OneToOneField(User, on_delete=models.CASCADE, related_name="realtor_profile")
    license_number  = models.CharField(max_length=32, db_index=True)
    license_type    = models.CharField(max_length=24, choices=LicenseType.choices, default=LicenseType.BROKER)
    verification_status = models.CharField(max_length=12, choices=VerificationStatus.choices,
                                          default=VerificationStatus.PENDING, db_index=True)
    verified_at     = models.DateTimeField(null=True, blank=True)
    license_expires = models.DateField(null=True, blank=True)
    brokerage       = models.CharField(max_length=200, blank=True)
    headshot        = models.ImageField(
        upload_to="realtors/", null=True, blank=True,
        validators=[MaxFileSizeValidator(5)],
    )
    bio             = models.TextField(max_length=2000, blank=True)
    phone           = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = "Realtor profile"
        verbose_name_plural = "Realtor profiles"

    def __str__(self) -> str:
        return f"{self.user.email} ({self.license_number})"

    @property
    def is_verified(self) -> bool:
        return self.verification_status == VerificationStatus.VERIFIED


class VendorProfile(TimeStampedModel):
    """Marketplace vendor — skeleton in P1, fleshed out in P5."""

    class Status(models.TextChoices):
        DRAFT     = "draft",     _("Draft")
        ACTIVE    = "active",    _("Active")
        SUSPENDED = "suspended", _("Suspended")

    user          = models.OneToOneField(User, on_delete=models.CASCADE, related_name="vendor_profile")
    business_name = models.CharField(max_length=200)
    slug          = models.SlugField(max_length=200, unique=True, blank=True)
    status        = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    tagline       = models.CharField(max_length=160, blank=True)
    website       = models.URLField(blank=True)

    class Meta:
        verbose_name = "Vendor profile"
        verbose_name_plural = "Vendor profiles"

    def __str__(self) -> str:
        return self.business_name


class CheckTrigger(models.TextChoices):
    SIGNUP    = "signup",    _("Signup")
    SCHEDULED = "scheduled", _("Scheduled (Celery beat)")
    MANUAL    = "manual",    _("Manual recheck")


class LicenseCheck(TimeStampedModel):
    """Audit row per ARELLO call. Never delete — keep raw response forever."""

    profile       = models.ForeignKey(RealtorProfile, on_delete=models.CASCADE, related_name="checks")
    status        = models.CharField(max_length=24)  # raw status from ARELLO
    raw_response  = models.JSONField(default=dict)
    source        = models.CharField(max_length=24, default="arello")
    triggered_by  = models.CharField(max_length=12, choices=CheckTrigger.choices, default=CheckTrigger.SIGNUP)
    error         = models.TextField(blank=True)

    class Meta:
        verbose_name = "License check"
        verbose_name_plural = "License checks"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.profile.license_number} → {self.status} @ {self.created_at:%Y-%m-%d}"
