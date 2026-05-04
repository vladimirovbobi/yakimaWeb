"""DRF permission classes (per docs/ACCESS-MATRIX.md)."""
from django.conf import settings
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied


class IsRealtor(permissions.BasePermission):
    """Verified WA realtor only."""

    def has_permission(self, request, view):
        u = request.user
        return bool(
            u and u.is_authenticated and u.is_realtor
            and getattr(u, "realtor_profile", None)
            and u.realtor_profile.verification_status == "verified"
        )


class IsVendor(permissions.BasePermission):
    """Active vendor only."""

    def has_permission(self, request, view):
        u = request.user
        return bool(
            u and u.is_authenticated and u.is_vendor
            and getattr(u, "vendor_profile", None)
            and u.vendor_profile.status == "active"
        )


class IsModerator(permissions.BasePermission):
    """Staff member of `moderator` group (or higher)."""

    def has_permission(self, request, view):
        u = request.user
        if not (u and u.is_authenticated):
            return False
        if u.is_superuser:
            return True
        return u.groups.filter(name__in=["moderator", "operator"]).exists()


class IsOperator(permissions.BasePermission):
    """Staff member of `operator` group (or higher)."""

    def has_permission(self, request, view):
        u = request.user
        if not (u and u.is_authenticated):
            return False
        if u.is_superuser:
            return True
        return u.groups.filter(name="operator").exists()


class IsAdmin(permissions.BasePermission):
    """Django superuser only."""

    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and u.is_superuser)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Object-level: read for anyone, write only for the owner."""

    OWNERSHIP_FIELDS = ("author", "user", "owner", "created_by")

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        for field in self.OWNERSHIP_FIELDS:
            owner = getattr(obj, field, None)
            if owner is not None:
                return owner == request.user
        return False


class ReadOnly(permissions.BasePermission):
    """Allow only GET/HEAD/OPTIONS — used on public viewsets."""

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """Read for anyone, write requires auth."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)


class _OTPRequired(PermissionDenied):
    """Sentinel — translates to 403 with a recognizable code via the
    custom problem-detail handler."""
    default_code = "otp_required"


class RequiresOTP(permissions.BasePermission):
    """Staff users must have a verified TOTP device on the request.

    In dev with `DJANGO_OTP_REQUIRED_FOR_STAFF=False`, this permission becomes
    a no-op so local ergonomics aren't blocked; production keeps it on.
    """

    message = "Two-factor authentication required for this endpoint."

    def has_permission(self, request, view):
        u = request.user
        if not (u and u.is_authenticated):
            return False
        if not u.is_staff:
            # Non-staff never satisfy ops endpoints anyway — defer to companions.
            return True
        if not getattr(settings, "DJANGO_OTP_REQUIRED_FOR_STAFF", True):
            return True
        # `request.user.is_verified` is set by django_otp.middleware.OTPMiddleware.
        if callable(getattr(u, "is_verified", None)) and u.is_verified():
            return True
        return False
