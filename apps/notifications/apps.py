from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notifications"
    label = "notifications"
    verbose_name = "Notifications"

    def ready(self) -> None:  # noqa: D401
        # Import to register signal handlers when app loads.
        from . import signal_hooks  # noqa: F401
