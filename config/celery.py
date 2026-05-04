"""Celery app — picks up settings + registers tasks from all apps.

Task routing: image-heavy work goes to the ``images`` queue (img-worker
service in compose). See ``apps/core/celery_routes.py`` for the map.
"""
import os
from celery import Celery

from apps.core.celery_routes import CELERY_TASK_ROUTES

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("yakimaweb")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.task_routes = CELERY_TASK_ROUTES
app.conf.task_default_queue = "celery"
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):  # noqa: ANN001
    print(f"Celery alive — request: {self.request!r}")
