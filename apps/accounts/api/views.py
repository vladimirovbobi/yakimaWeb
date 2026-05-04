"""Accounts API views — auth flows, /me/, realtor verify, public realtor list."""
from __future__ import annotations

from allauth.account.internal.flows.email_verification import (
    send_verification_email_for_user as _send_email_confirmation,
)
from allauth.account.models import EmailConfirmationHMAC


def send_email_confirmation(request, user, **kwargs):
    """Compat shim for allauth >= 65 (send_email_confirmation moved to internal flows)."""
    return _send_email_confirmation(request, user)
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Q
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework import generics, permissions, status
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotFound,
    ParseError,
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.api.authentication import clear_jwt_cookies, set_jwt_cookies
from apps.core.api.pagination import TimeCursorPagination
from apps.core.api.permissions import IsRealtor, IsVendor
from apps.tools.api.serializers import ToolUsageSerializer

from ..models import CheckTrigger, RealtorProfile, VerificationStatus
from ..tasks import verify_license_task
from .serializers import (
    LoginSerializer,
    MeUpdateSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PrivateRealtorProfileSerializer,
    PrivateUserSerializer,
    PublicRealtorProfileSerializer,
    RealtorProfilePartialUpdateSerializer,
    RealtorVerifySerializer,
    SignupSerializer,
    TOTPDeviceSetupSerializer,
    TOTPDeviceVerifySerializer,
    VendorProfileSerializer,
)

User = get_user_model()


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────
def _issue_tokens_for(user) -> tuple[str, str]:
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)


# ──────────────────────────────────────────────────────────────────────────
# Auth
# ──────────────────────────────────────────────────────────────────────────
class SignupView(generics.GenericAPIView):
    """POST /api/v1/auth/signup/ — create user, send confirmation, optionally log in."""

    serializer_class = SignupSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []
    throttle_scope = "anon"

    def post(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = User.objects.create_user(
            email=ser.validated_data["email"],
            password=ser.validated_data["password"],
        )
        try:
            send_email_confirmation(request, user, signup=True)
        except Exception:  # noqa: BLE001 — email delivery failures must not break signup
            pass

        body = PrivateUserSerializer(user).data
        response = Response(body, status=status.HTTP_201_CREATED)

        verification = getattr(settings, "ACCOUNT_EMAIL_VERIFICATION", "mandatory")
        if verification != "mandatory":
            access, refresh = _issue_tokens_for(user)
            set_jwt_cookies(response, access, refresh)
        return response


class LoginView(generics.GenericAPIView):
    """POST /api/v1/auth/login/ — issue JWT cookies on success."""

    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def post(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)

        user = authenticate(
            request,
            email=ser.validated_data["email"],
            password=ser.validated_data["password"],
        )
        if user is None or not user.is_active:
            raise AuthenticationFailed("Invalid credentials.")

        access, refresh = _issue_tokens_for(user)
        body = PrivateUserSerializer(user).data
        response = Response(body, status=status.HTTP_200_OK)
        set_jwt_cookies(response, access, refresh)
        return response


class LogoutView(APIView):
    """POST /api/v1/auth/logout/ — blacklist refresh, clear cookies."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        raw_refresh = request.COOKIES.get(settings.JWT_AUTH_REFRESH_COOKIE)
        if raw_refresh:
            try:
                RefreshToken(raw_refresh).blacklist()
            except TokenError:
                pass
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_jwt_cookies(response)
        return response


class RefreshView(APIView):
    """POST /api/v1/auth/refresh/ — read refresh cookie, rotate, set new cookies."""

    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def post(self, request, *args, **kwargs):
        raw_refresh = request.COOKIES.get(settings.JWT_AUTH_REFRESH_COOKIE)
        if not raw_refresh:
            raise InvalidToken("No refresh cookie.")
        try:
            old = RefreshToken(raw_refresh)
            new_access = str(old.access_token)
            # Rotate: blacklist old, mint new
            try:
                old.blacklist()
            except TokenError:
                pass
            new_refresh = RefreshToken.for_user(
                User.objects.get(id=old["user_id"])
            )
            new_refresh_str = str(new_refresh)
        except (TokenError, KeyError, User.DoesNotExist) as exc:
            raise InvalidToken(str(exc)) from exc

        response = Response(status=status.HTTP_200_OK)
        set_jwt_cookies(response, new_access, new_refresh_str)
        return response


class EmailConfirmView(APIView):
    """GET /api/v1/auth/verify-email/<key>/ — confirm via allauth HMAC."""

    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def get(self, request, key: str, *args, **kwargs):
        confirmation = EmailConfirmationHMAC.from_key(key)
        if confirmation is None:
            raise NotFound("Invalid or expired confirmation key.")
        confirmation.confirm(request)
        return Response({"verified": True}, status=status.HTTP_200_OK)


class PasswordResetView(generics.GenericAPIView):
    """POST /api/v1/auth/password-reset/ — kick off Django reset email."""

    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []
    throttle_scope = "anon"

    def post(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        form = PasswordResetForm(data={"email": ser.validated_data["email"]})
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                from_email=settings.DEFAULT_FROM_EMAIL,
            )
        # Same response on hit/miss to avoid user enumeration.
        return Response({"detail": "If an account exists, a reset email is on its way."},
                        status=status.HTTP_200_OK)


class PasswordResetConfirmView(generics.GenericAPIView):
    """POST /api/v1/auth/password-reset-confirm/<uidb64>/<token>/."""

    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []

    def post(self, request, uidb64: str, token: str, *args, **kwargs):
        # Allow uid+token via URL or body — URL is the primary path.
        data = dict(request.data)
        data.setdefault("uid", uidb64)
        data.setdefault("token", token)
        ser = self.get_serializer(data=data)
        ser.is_valid(raise_exception=True)

        try:
            uid = force_str(urlsafe_base64_decode(ser.validated_data["uid"]))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as exc:
            raise ParseError("Invalid reset link.") from exc

        if not default_token_generator.check_token(user, ser.validated_data["token"]):
            raise PermissionDenied("Reset token is invalid or expired.")

        user.set_password(ser.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"detail": "Password updated."}, status=status.HTTP_200_OK)


# ──────────────────────────────────────────────────────────────────────────
# 2FA (TOTP)
# ──────────────────────────────────────────────────────────────────────────
class TOTPSetupView(APIView):
    """POST /api/v1/auth/2fa/totp/setup/ — return provisioning URI + secret."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Wipe any previous unconfirmed devices; one setup at a time.
        TOTPDevice.objects.filter(user=request.user, confirmed=False).delete()
        device = TOTPDevice.objects.create(
            user=request.user, name="default", confirmed=False,
        )
        body = {
            "provisioning_uri": device.config_url,
            "secret_b32": device.bin_key.hex(),  # bin_key is bytes; expose hex of secret
        }
        ser = TOTPDeviceSetupSerializer(body)
        return Response(ser.data, status=status.HTTP_201_CREATED)


class TOTPVerifyView(generics.GenericAPIView):
    """POST /api/v1/auth/2fa/totp/verify/ — confirm device with a 6-digit token."""

    serializer_class = TOTPDeviceVerifySerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        device = (TOTPDevice.objects
                  .filter(user=request.user, confirmed=False)
                  .order_by("-id").first())
        if device is None:
            raise NotFound("No pending TOTP device — call /setup/ first.")
        if not device.verify_token(ser.validated_data["token"]):
            raise ValidationError({"token": "Invalid token."})
        device.confirmed = True
        device.save(update_fields=["confirmed"])
        return Response({"detail": "TOTP enabled."}, status=status.HTTP_200_OK)


# ──────────────────────────────────────────────────────────────────────────
# /me/
# ──────────────────────────────────────────────────────────────────────────
class MeView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/v1/me/."""

    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return MeUpdateSerializer
        return PrivateUserSerializer

    def update(self, request, *args, **kwargs):
        # Always partial — full PUT not supported on this endpoint.
        kwargs["partial"] = True
        super_response = super().update(request, *args, **kwargs)
        # Echo full PrivateUserSerializer so the client gets the new state.
        return Response(PrivateUserSerializer(self.get_object()).data,
                        status=super_response.status_code)


class MyRealtorProfileView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/v1/me/realtor/."""

    permission_classes = [permissions.IsAuthenticated, IsRealtor]
    serializer_class = PrivateRealtorProfileSerializer

    def get_object(self):
        profile = getattr(self.request.user, "realtor_profile", None)
        if profile is None:
            raise NotFound("No realtor profile yet — call /realtor/verify/ first.")
        return profile


class MyVendorProfileView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/v1/me/vendor/."""

    permission_classes = [permissions.IsAuthenticated, IsVendor]
    serializer_class = VendorProfileSerializer

    def get_object(self):
        profile = getattr(self.request.user, "vendor_profile", None)
        if profile is None:
            raise NotFound("No vendor profile yet.")
        return profile


class MyToolUsageListView(generics.ListAPIView):
    """GET /api/v1/me/tool-usage/."""

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = TimeCursorPagination
    serializer_class = ToolUsageSerializer

    def get_queryset(self):
        return (self.request.user.tool_runs
                .select_related("tool")
                .order_by("-created_at"))


# ──────────────────────────────────────────────────────────────────────────
# Realtor verify + edit (private)
# ──────────────────────────────────────────────────────────────────────────
class RealtorVerifyView(generics.GenericAPIView):
    """POST /api/v1/realtor/verify/ — kick off ARELLO check via Celery."""

    serializer_class = RealtorVerifySerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        profile, _ = RealtorProfile.objects.update_or_create(
            user=request.user,
            defaults={
                "license_number": d["license_number"],
                "license_type": d["license_type"],
                "verification_status": VerificationStatus.PENDING,
            },
        )
        if request.user.full_name != d["full_name"]:
            request.user.full_name = d["full_name"]
            request.user.save(update_fields=["full_name"])

        async_result = verify_license_task.delay(
            profile.pk, triggered_by=CheckTrigger.SIGNUP,
        )

        body = {
            "task_id": getattr(async_result, "id", None),
            "verification_status": profile.verification_status,
            "profile": PrivateRealtorProfileSerializer(profile).data,
        }
        return Response(body, status=status.HTTP_202_ACCEPTED)


class RealtorProfilePartialUpdateView(generics.UpdateAPIView):
    """PATCH /api/v1/realtor/profile/ — bio + headshot + brokerage + phone."""

    permission_classes = [permissions.IsAuthenticated, IsRealtor]
    serializer_class = RealtorProfilePartialUpdateSerializer
    http_method_names = ["patch", "options", "head"]

    def get_object(self):
        profile = getattr(self.request.user, "realtor_profile", None)
        if profile is None:
            raise NotFound("No realtor profile to update.")
        return profile

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        super().update(request, *args, **kwargs)
        return Response(
            PrivateRealtorProfileSerializer(self.get_object()).data,
            status=status.HTTP_200_OK,
        )


# ──────────────────────────────────────────────────────────────────────────
# Public realtor list / detail
# ──────────────────────────────────────────────────────────────────────────
class PublicRealtorListView(generics.ListAPIView):
    """GET /api/public/v1/realtors/ — verified-only, searchable by name + brokerage."""

    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []
    pagination_class = TimeCursorPagination
    serializer_class = PublicRealtorProfileSerializer

    def get_queryset(self):
        qs = (RealtorProfile.objects
              .select_related("user")
              .filter(verification_status=VerificationStatus.VERIFIED))
        q = self.request.query_params.get("q") or self.request.query_params.get("search")
        if q:
            qs = qs.filter(
                Q(user__full_name__icontains=q) | Q(brokerage__icontains=q),
            )
        return qs.order_by("-verified_at", "-created_at")


class PublicRealtorDetailView(generics.RetrieveAPIView):
    """GET /api/public/v1/realtors/<pk>/ — verified realtor by user id."""

    permission_classes = [permissions.AllowAny]
    authentication_classes: list = []
    serializer_class = PublicRealtorProfileSerializer
    lookup_field = "user_id"
    lookup_url_kwarg = "user_id"

    def get_queryset(self):
        return (RealtorProfile.objects
                .select_related("user")
                .filter(verification_status=VerificationStatus.VERIFIED))
