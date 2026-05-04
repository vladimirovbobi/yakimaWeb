"""Core API serializers — site meta, healthz."""
from __future__ import annotations

from rest_framework import serializers


class NavigationChildSerializer(serializers.Serializer):
    label = serializers.CharField()
    href = serializers.CharField()


class NavigationItemSerializer(serializers.Serializer):
    label = serializers.CharField()
    href = serializers.CharField()
    children = NavigationChildSerializer(many=True, required=False)


class FeatureFlagsSerializer(serializers.Serializer):
    ai_tools_enabled = serializers.BooleanField()
    marketplace_enabled = serializers.BooleanField()
    forum_enabled = serializers.BooleanField()


class SocialLinksSerializer(serializers.Serializer):
    twitter = serializers.CharField(required=False, allow_blank=True)
    facebook = serializers.CharField(required=False, allow_blank=True)
    instagram = serializers.CharField(required=False, allow_blank=True)
    youtube = serializers.CharField(required=False, allow_blank=True)


class SiteMetaSerializer(serializers.Serializer):
    """Public site metadata — read by Next.js for layout shell."""

    site_name = serializers.CharField()
    site_tagline = serializers.CharField()
    site_description = serializers.CharField()
    contact_email = serializers.EmailField()
    navigation = NavigationItemSerializer(many=True)
    feature_flags = FeatureFlagsSerializer()
    social_links = SocialLinksSerializer()


class HealthzSerializer(serializers.Serializer):
    status = serializers.CharField()
    time = serializers.DateTimeField()
    version = serializers.CharField(required=False, allow_blank=True)
