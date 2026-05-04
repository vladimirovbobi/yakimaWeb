"""Auth routes — /api/v1/auth/."""
from django.urls import path

from .views import (
    EmailConfirmView,
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetView,
    RefreshView,
    SignupView,
    TOTPSetupView,
    TOTPVerifyView,
)

urlpatterns = [
    path("signup/",  SignupView.as_view(),  name="auth-signup"),
    path("login/",   LoginView.as_view(),   name="auth-login"),
    path("logout/",  LogoutView.as_view(),  name="auth-logout"),
    path("refresh/", RefreshView.as_view(), name="auth-refresh"),

    path("verify-email/<str:key>/",
         EmailConfirmView.as_view(), name="auth-verify-email"),

    path("password-reset/",
         PasswordResetView.as_view(), name="auth-password-reset"),
    path("password-reset-confirm/<str:uidb64>/<str:token>/",
         PasswordResetConfirmView.as_view(), name="auth-password-reset-confirm"),

    path("2fa/totp/setup/",  TOTPSetupView.as_view(),  name="auth-totp-setup"),
    path("2fa/totp/verify/", TOTPVerifyView.as_view(), name="auth-totp-verify"),
]
