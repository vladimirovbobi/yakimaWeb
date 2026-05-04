"""Accounts serializers — public-safe + private + auth flows."""
from __future__ import annotations

import re

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from ..models import (
    LicenseCheck,
    LicenseType,
    RealtorProfile,
    VendorProfile,
    VerificationStatus,
)

User = get_user_model()

LICENSE_NUMBER_RE = re.compile(r"^[A-Za-z0-9\-]{4,32}$")


# ──────────────────────────────────────────────────────────────────────────
# User serializers
# ──────────────────────────────────────────────────────────────────────────
class PublicUserSerializer(serializers.ModelSerializer):
    """Anyone-readable view of a user. No PII beyond display."""

    avatar = serializers.ImageField(use_url=True, read_only=True)

    class Meta:
        model = User
        fields = ("id", "full_name", "avatar", "role")
        read_only_fields = fields


class PrivateUserSerializer(serializers.ModelSerializer):
    """The signed-in user's own view. Includes email + flags."""

    avatar = serializers.ImageField(use_url=True, read_only=True)

    class Meta:
        model = User
        fields = (
            "id", "email", "full_name", "avatar", "role",
            "is_realtor", "is_vendor", "last_seen", "created_at",
        )
        read_only_fields = (
            "id", "email", "role", "is_realtor", "is_vendor",
            "last_seen", "created_at",
        )


class MeUpdateSerializer(serializers.ModelSerializer):
    """PATCH /me/ payload — limited to display fields."""

    class Meta:
        model = User
        fields = ("full_name", "avatar")


# ──────────────────────────────────────────────────────────────────────────
# Realtor profile serializers
# ──────────────────────────────────────────────────────────────────────────
class PublicRealtorProfileSerializer(serializers.ModelSerializer):
    """Verified-only public-facing profile. License number deliberately omitted."""

    user = PublicUserSerializer(read_only=True)
    headshot = serializers.ImageField(use_url=True, read_only=True)

    class Meta:
        model = RealtorProfile
        fields = (
            "id", "user", "license_type", "brokerage", "headshot",
            "bio", "phone", "verified_at",
        )
        read_only_fields = fields


class PrivateRealtorProfileSerializer(serializers.ModelSerializer):
    """The realtor's own view of /me/realtor/ — includes full license_number + status."""

    user = PublicUserSerializer(read_only=True)
    headshot = serializers.ImageField(use_url=True, required=False, allow_null=True)

    class Meta:
        model = RealtorProfile
        fields = (
            "id", "user",
            "license_number", "license_type", "license_expires",
            "verification_status", "verified_at",
            "brokerage", "headshot", "bio", "phone",
        )
        read_only_fields = (
            "id", "user", "license_number", "license_type",
            "license_expires", "verification_status", "verified_at",
        )


class RealtorVerifySerializer(serializers.Serializer):
    """Input to POST /realtor/verify/ — validate license shape."""

    license_number = serializers.CharField(min_length=4, max_length=32)
    license_type = serializers.ChoiceField(choices=LicenseType.choices)
    full_name = serializers.CharField(min_length=2, max_length=200)

    def validate_license_number(self, value: str) -> str:
        cleaned = (value or "").strip().upper()
        if not LICENSE_NUMBER_RE.match(cleaned):
            raise serializers.ValidationError(
                "That doesn't look like a valid license number."
            )
        return cleaned


class RealtorProfilePartialUpdateSerializer(serializers.ModelSerializer):
    """PATCH /realtor/profile/ — bio + headshot + brokerage + phone only."""

    headshot = serializers.ImageField(use_url=True, required=False, allow_null=True)

    class Meta:
        model = RealtorProfile
        fields = ("brokerage", "headshot", "bio", "phone")


# ──────────────────────────────────────────────────────────────────────────
# Vendor profile (skeleton — fleshed out in Phase 5)
# ──────────────────────────────────────────────────────────────────────────
class VendorProfileSerializer(serializers.ModelSerializer):
    user = PublicUserSerializer(read_only=True)

    class Meta:
        model = VendorProfile
        fields = (
            "id", "user", "business_name", "slug", "status",
            "tagline", "website",
        )
        read_only_fields = ("id", "user", "slug", "status")


# ──────────────────────────────────────────────────────────────────────────
# Audit (op-only)
# ──────────────────────────────────────────────────────────────────────────
class LicenseCheckSerializer(serializers.ModelSerializer):
    """Audit trail row. raw_response intentionally omitted — admin-only via Django admin."""

    profile_id = serializers.IntegerField(source="profile.pk", read_only=True)

    class Meta:
        model = LicenseCheck
        fields = (
            "id", "profile_id", "status", "source",
            "triggered_by", "error", "created_at",
        )
        read_only_fields = fields


# ──────────────────────────────────────────────────────────────────────────
# Auth flow serializers
# ──────────────────────────────────────────────────────────────────────────
class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=12, max_length=128)
    password_confirm = serializers.CharField(write_only=True, min_length=12, max_length=128)

    def validate_email(self, value: str) -> str:
        normalised = value.strip().lower()
        if User.objects.filter(email__iexact=normalised).exists():
            raise serializers.ValidationError("An account with that email already exists.")
        return normalised

    def validate(self, attrs: dict) -> dict:
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        validate_password(attrs["password"])
        return attrs


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=12, max_length=128)
    new_password_confirm = serializers.CharField(write_only=True, min_length=12, max_length=128)

    def validate(self, attrs: dict) -> dict:
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "Passwords do not match."})
        validate_password(attrs["new_password"])
        return attrs


# ──────────────────────────────────────────────────────────────────────────
# 2FA serializers
# ──────────────────────────────────────────────────────────────────────────
class TOTPDeviceSetupSerializer(serializers.Serializer):
    """Output only — returned once when a TOTPDevice is created."""

    provisioning_uri = serializers.CharField(read_only=True)
    secret_b32 = serializers.CharField(read_only=True)


class TOTPDeviceVerifySerializer(serializers.Serializer):
    """Input — confirm setup with a 6-digit token."""

    token = serializers.RegexField(regex=r"^\d{6}$", max_length=6)
