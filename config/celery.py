"""Celery app — picks up settings + registers tasks from all apps.

Task routing: image-heavy work goes to the ``images`` queue (img-worker
service in compose). See ``apps/core/celery_routes.py`` for the map.
"""
import os
from celery import Celery
from celery.schedules import crontab

from apps.core.celery_routes import CELERY_TASK_ROUTES

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("yakimaweb")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.task_routes = CELERY_TASK_ROUTES
app.conf.task_default_queue = "celery"
app.autodiscover_tasks()

# ─── Beat schedule ───────────────────────────────────────────────────────
# Times use CELERY_TIMEZONE (America/Los_Angeles per settings).
app.conf.beat_schedule = {
    "notifications-daily-digest": {
        "task": "apps.notifications.tasks.deliver_email_digest",
        "schedule": crontab(hour=9, minute=0),
    },
    "notifications-purge-old": {
        "task": "apps.notifications.tasks.purge_old_notifications",
        "schedule": crontab(hour=4, minute=0, day_of_week=1),  # Monday 04:00
    },
    "audit-anomaly-detection-hourly": {
        "task": "apps.audit.tasks.run_anomaly_detection",
        "schedule": crontab(minute=15),  # 15 past every hour
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):  # noqa: ANN001
    print(f"Celery alive — request: {self.request!r}")
