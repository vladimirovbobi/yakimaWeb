"""Tool admin — operators control which tools are live + per-role limits."""
from django.contrib import admin

from .models import Tool, ToolUsage


@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display  = ("slug", "name", "model_id", "is_enabled",
                     "member_daily_limit", "realtor_daily_limit",
                     "cost_per_run_estimate_usd")
    list_filter   = ("is_enabled",)
    search_fields = ("slug", "name")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ToolUsage)
class ToolUsageAdmin(admin.ModelAdmin):
    list_display  = ("created_at", "user", "tool", "status",
                     "tokens_in", "tokens_out", "cost_usd", "duration_ms")
    list_filter   = ("status", "tool", "block_reason")
    search_fields = ("user__email", "tool__slug", "error")
    readonly_fields = tuple(f.name for f in ToolUsage._meta.fields)
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
