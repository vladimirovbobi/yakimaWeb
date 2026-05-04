from django.apps import AppConfig


class ForumConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.forum"
    verbose_name = "Forum"

    def ready(self):
        from . import signals  # noqa: F401
