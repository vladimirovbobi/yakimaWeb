"""Audit admin — read-only, append-only."""
from django.contrib import admin

from .models import AccessLog, ActionLog


@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display  = ("created_at", "actor", "action", "target_type", "target_id", "ip")
    list_filter   = ("action",)
    search_fields = ("actor__email", "action", "ip")
    readonly_fields = tuple(f.name for f in ActionLog._meta.fields)
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display  = ("created_at", "actor", "surface", "method", "path", "status_code", "ip")
    list_filter   = ("surface", "method", "status_code")
    search_fields = ("actor__email", "path", "ip")
    readonly_fields = tuple(f.name for f in AccessLog._meta.fields)
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
