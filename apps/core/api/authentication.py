"""JWT-in-httpOnly-cookie authentication (per ADR-0008).

Reads the access token from the `yw_access` cookie. No Authorization header.
Frontend never sees the token — middleware in Next.js validates by cookie presence,
backend validates the signature here.
"""
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class JWTCookieAuthentication(JWTAuthentication):
    """JWT auth that reads the token from a cookie instead of Authorization header."""

    def authenticate(self, request):
        raw_token = request.COOKIES.get(settings.JWT_AUTH_COOKIE)
        if not raw_token:
            return None
        try:
            validated_token = self.get_validated_token(raw_token)
        except InvalidToken:
            return None
        return self.get_user(validated_token), validated_token


def set_jwt_cookies(response, access: str, refresh: str | None = None) -> None:
    """Set access (and optionally refresh) JWT cookies on the response."""
    response.set_cookie(
        settings.JWT_AUTH_COOKIE,
        access,
        max_age=int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
        httponly=settings.JWT_AUTH_COOKIE_HTTPONLY,
        secure=settings.JWT_AUTH_COOKIE_SECURE,
        samesite=settings.JWT_AUTH_COOKIE_SAMESITE,
        path=settings.JWT_AUTH_COOKIE_PATH,
    )
    if refresh:
        response.set_cookie(
            settings.JWT_AUTH_REFRESH_COOKIE,
            refresh,
            max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
            httponly=settings.JWT_AUTH_COOKIE_HTTPONLY,
            secure=settings.JWT_AUTH_COOKIE_SECURE,
            samesite=settings.JWT_AUTH_COOKIE_SAMESITE,
            path=settings.JWT_AUTH_REFRESH_COOKIE_PATH,
        )


def clear_jwt_cookies(response) -> None:
    """Remove JWT cookies on logout."""
    response.delete_cookie(settings.JWT_AUTH_COOKIE, path=settings.JWT_AUTH_COOKIE_PATH)
    response.delete_cookie(
        settings.JWT_AUTH_REFRESH_COOKIE,
        path=settings.JWT_AUTH_REFRESH_COOKIE_PATH,
    )
