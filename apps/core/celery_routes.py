"""Celery task routing — image-heavy tasks land on the dedicated img-worker.

Reference compose service: ``img-worker`` (separate Celery worker on the
``images`` queue). Tasks listed here pin to that queue; everything else
defaults to the general ``celery`` queue.

To send a new task to img-worker, either:
  1. Decorate it with ``@shared_task(queue="images")``, or
  2. Add its dotted path here.

Loaded by ``config/celery.py`` (CELERY_TASK_ROUTES setting).
"""

CELERY_TASK_ROUTES = {
    "apps.tools.tasks.run_furniture_remover": {"queue": "images"},
    "apps.tools.tasks.generate_og_image": {"queue": "images"},
    "apps.content.tasks.resize_hero_image": {"queue": "images"},
    "apps.moderation.tasks.moderate_image_task": {"queue": "images"},
    # Default queue ("celery") handles everything else.
}
