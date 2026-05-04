"""Locked-down moderation admin."""
from django.contrib import admin

from .models import ActionTemplate, Flag, ModerationDecision


@admin.register(ActionTemplate)
class ActionTemplateAdmin(admin.ModelAdmin):
    list_display  = ("slug", "label", "action", "is_active", "sort_order")
    list_filter   = ("action", "is_active")
    search_fields = ("slug", "label", "default_reason")
    list_editable = ("is_active", "sort_order")


@admin.register(ModerationDecision)
class ModerationDecisionAdmin(admin.ModelAdmin):
    list_display  = ("created_at", "layer", "action", "severity", "classifier_ver",
                     "target_type", "target_id")
    list_filter   = ("layer", "action", "severity", "classifier_ver")
    search_fields = ("input_hash", "reason")
    readonly_fields = tuple(f.name for f in ModerationDecision._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Flag)
class FlagAdmin(admin.ModelAdmin):
    list_display  = ("created_at", "reporter", "reason", "status",
                     "target_type", "target_id", "resolved_by")
    list_filter   = ("reason", "status")
    search_fields = ("reporter__email", "notes")
    readonly_fields = ("created_at", "updated_at", "reporter", "target_type", "target_id")
