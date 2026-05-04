"""Marketplace admin — locked-down + treebeard-aware."""
from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from .models import (Bundle, BundleItem, Category, Lead, LeadMessage, Package,
                     Review, Service)


@admin.register(Category)
class CategoryAdmin(TreeAdmin):
    form = movenodeform_factory(Category)
    list_display  = ("label", "slug", "depth_label")
    search_fields = ("label", "slug")


class PackageInline(admin.TabularInline):
    model = Package
    extra = 0


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display  = ("title", "vendor", "category", "is_active", "moderation_status",
                     "response_time_hours", "created_at")
    list_filter   = ("is_active", "moderation_status", "category")
    search_fields = ("title", "vendor__business_name", "description")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [PackageInline]
    readonly_fields = ("moderation_status", "moderation_score", "moderated_at",
                        "created_at", "updated_at")


class BundleItemInline(admin.TabularInline):
    model = BundleItem
    extra = 0


@admin.register(Bundle)
class BundleAdmin(admin.ModelAdmin):
    list_display  = ("name", "vendor", "billing_cadence", "price_total", "is_active",
                     "moderation_status")
    list_filter   = ("billing_cadence", "is_active", "moderation_status")
    search_fields = ("name", "vendor__business_name")
    inlines = [BundleItemInline]


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display  = ("service", "tier", "name", "price_low", "price_high", "delivery_days")
    list_filter   = ("tier",)
    search_fields = ("service__title", "name")
    autocomplete_fields = ("service",)


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display  = ("created_at", "buyer", "vendor", "service", "package", "bundle", "status")
    list_filter   = ("status",)
    search_fields = ("buyer__email", "vendor__business_name", "message")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("buyer", "vendor", "service", "package", "bundle")


@admin.register(LeadMessage)
class LeadMessageAdmin(admin.ModelAdmin):
    list_display  = ("created_at", "lead", "sender")
    search_fields = ("body",)
    readonly_fields = ("lead", "sender", "body", "created_at", "updated_at")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display  = ("created_at", "rating", "lead", "moderation_status")
    list_filter   = ("rating", "moderation_status")
    search_fields = ("body", "vendor_response", "lead__buyer__email")
    readonly_fields = ("lead", "rating", "moderation_status", "moderation_score",
                        "moderated_at", "created_at", "updated_at")
