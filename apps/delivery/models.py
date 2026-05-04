"""Delivery models — source-of-truth schema for the FastAPI delivery service.

Django runs migrations against these tables. The delivery service reads/writes
via SQLAlchemy with matching column names — see `delivery/db.py`.
"""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel
from apps.marketplace.models import Lead


class PackageStatus(models.TextChoices):
    OPEN      = "open",      _("Open")
    FINALIZED = "finalized", _("Finalized")
    REVOKED   = "revoked",   _("Revoked")


class DeliveryPackage(TimeStampedModel):
    """One package = one delivery from a vendor to a buyer, scoped to a Lead."""

    lead    = models.ForeignKey(Lead, on_delete=models.PROTECT, related_name="delivery_packages")
    vendor  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                related_name="delivery_packages_sent")
    buyer   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                related_name="delivery_packages_received")
    name    = models.CharField(max_length=240, default="Delivery")
    note    = models.TextField(blank=True)
    status  = models.CharField(max_length=16, choices=PackageStatus.choices,
                               default=PackageStatus.OPEN, db_index=True)
    finalized_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "delivery_packages"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["lead", "status"]),
            models.Index(fields=["vendor", "-created_at"]),
            models.Index(fields=["buyer", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"Package {self.pk} for Lead {self.lead_id} ({self.status})"


class FileScanStatus(models.TextChoices):
    PENDING  = "pending",  _("Pending")
    CLEAN    = "clean",    _("Clean")
    INFECTED = "infected", _("Infected")
    SKIPPED  = "skipped",  _("Skipped (no scanner configured)")


class DeliveryFile(TimeStampedModel):
    """One file in a package."""

    package      = models.ForeignKey(DeliveryPackage, on_delete=models.CASCADE,
                                      related_name="files")
    filename     = models.CharField(max_length=240)
    content_type = models.CharField(max_length=80)
    size_bytes   = models.PositiveBigIntegerField()
    sha256       = models.CharField(max_length=64, blank=True)
    storage_path = models.CharField(max_length=512)
    scan_status  = models.CharField(max_length=16, choices=FileScanStatus.choices,
                                     default=FileScanStatus.PENDING, db_index=True)

    class Meta:
        db_table = "delivery_files"
        ordering = ["package", "filename"]
        indexes = [
            models.Index(fields=["package"]),
        ]

    def __str__(self) -> str:
        return f"{self.filename} ({self.size_bytes}B)"


class DeliveryAccessLog(TimeStampedModel):
    """Every read access — and every write event — gets logged."""

    package    = models.ForeignKey(DeliveryPackage, on_delete=models.CASCADE,
                                    related_name="access_log")
    file       = models.ForeignKey(DeliveryFile, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name="access_log")
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                    related_name="delivery_accesses")
    action     = models.CharField(max_length=24)  # manifest|download|finalize|upload
    ip_addr    = models.CharField(max_length=64, blank=True)
    user_agent = models.CharField(max_length=240, blank=True)

    class Meta:
        db_table = "delivery_access_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["package", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self) -> str:
        ts = self.created_at.strftime("%Y-%m-%d %H:%M")
        return f"{self.user_id} {self.action} pkg={self.package_id} @ {ts}"
