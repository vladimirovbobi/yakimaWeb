"""Celery app — picks up settings + registers tasks from all apps."""
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("yakimaweb")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):  # noqa: ANN001
    print(f"Celery alive — request: {self.request!r}")
