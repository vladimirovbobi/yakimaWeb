"""Locked-down ModelAdmin for accounts. Explicit fields + readonly. No bulk edit on sensitive."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import LicenseCheck, RealtorProfile, User, VendorProfile


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("-created_at",)
    list_display  = ("email", "role", "is_realtor", "is_vendor", "is_staff", "is_active", "created_at", "last_seen")
    list_filter   = ("role", "is_realtor", "is_vendor", "is_staff", "is_active")
    search_fields = ("email", "full_name")
    readonly_fields = ("created_at", "updated_at", "last_seen", "last_login")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("full_name", "avatar")}),
        ("Roles & permissions", {"fields": ("role", "is_realtor", "is_vendor",
                                             "is_staff", "is_superuser", "is_active",
                                             "groups", "user_permissions")}),
        ("Audit", {"fields": ("created_at", "updated_at", "last_seen", "last_login")}),
    )
    filter_horizontal = ("groups", "user_permissions")
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        # Only superusers can flip the realtor flag manually (use verify flow normally)
        if obj and not request.user.is_superuser:
            ro += ["is_realtor", "is_vendor", "is_staff", "is_superuser",
                   "groups", "user_permissions", "role"]
        return ro


@admin.register(RealtorProfile)
class RealtorProfileAdmin(admin.ModelAdmin):
    list_display  = ("user", "license_number", "license_type", "verification_status",
                     "verified_at", "license_expires", "brokerage")
    list_filter   = ("verification_status", "license_type")
    search_fields = ("user__email", "license_number", "brokerage")
    readonly_fields = ("verified_at", "created_at", "updated_at")
    autocomplete_fields = ("user",)


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display  = ("business_name", "user", "status", "created_at")
    list_filter   = ("status",)
    search_fields = ("business_name", "user__email", "slug")
    prepopulated_fields = {"slug": ("business_name",)}


@admin.register(LicenseCheck)
class LicenseCheckAdmin(admin.ModelAdmin):
    list_display  = ("profile", "status", "source", "triggered_by", "created_at")
    list_filter   = ("status", "source", "triggered_by")
    search_fields = ("profile__license_number", "profile__user__email")
    readonly_fields = ("profile", "status", "raw_response", "source", "triggered_by",
                       "error", "created_at", "updated_at")

    def has_add_permission(self, request):
        return False  # Only created via the verification task

    def has_delete_permission(self, request, obj=None):
        return False  # Audit log — never delete
