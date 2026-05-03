"""AccessLog middleware + thread-local request storage for signals to read."""
import threading
from typing import Optional

from django.http import HttpRequest

from .models import AccessLog, Surface

_local = threading.local()


def get_current_request() -> Optional[HttpRequest]:
    return getattr(_local, "request", None)


def get_current_user():
    req = get_current_request()
    if req is None or not hasattr(req, "user"):
        return None
    user = req.user
    if not user.is_authenticated:
        return None
    return user


def _resolve_surface(path: str) -> Optional[str]:
    if path.startswith("/admin/"):
        return Surface.ADMIN
    if path.startswith("/mod/"):
        return Surface.MOD
    if path.startswith("/operator/"):
        return Surface.OPERATOR
    return None


class AccessLogMiddleware:
    """Stash request thread-local + log staff route hits."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _local.request = request
        try:
            response = self.get_response(request)
        finally:
            self._maybe_log(request, response if "response" in dir() else None)
            _local.request = None
        return response

    def _maybe_log(self, request, response):
        if response is None:
            return
        surface = _resolve_surface(request.path)
        if surface is None:
            return
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            return  # log only authenticated staff route hits
        try:
            AccessLog.objects.create(
                actor=user, surface=surface,
                path=request.path[:500], method=request.method,
                status_code=getattr(response, "status_code", 0),
                ip=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:400],
            )
        except Exception:  # noqa: BLE001
            pass  # never let logging fail a request
