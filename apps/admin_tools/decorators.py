"""Role-based access decorators."""
from functools import wraps

from django.core.exceptions import PermissionDenied
from django.http import HttpRequest


def require_role(*roles: str):
    """View decorator — user.role must be in `roles`. Anonymous → PermissionDenied."""
    def deco(view):
        @wraps(view)
        def wrapped(request: HttpRequest, *a, **kw):
            user = getattr(request, "user", None)
            if user is None or not user.is_authenticated:
                raise PermissionDenied("login required")
            if getattr(user, "role", None) not in roles and not user.is_superuser:
                raise PermissionDenied(f"role required: {', '.join(roles)}")
            return view(request, *a, **kw)
        return wrapped
    return deco


def require_otp(view):
    """View decorator — require django-otp verified device for staff."""
    from django_otp import user_has_device
    from django_otp.decorators import otp_required

    @wraps(view)
    def wrapped(request, *a, **kw):
        user = getattr(request, "user", None)
        if user and user.is_authenticated and user.is_staff:
            if not user_has_device(user):
                raise PermissionDenied("staff users must enroll TOTP")
        return otp_required(view)(request, *a, **kw)
    return wrapped
