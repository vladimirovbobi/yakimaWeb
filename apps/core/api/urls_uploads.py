"""Upload URLs — mounted at /api/v1/uploads/."""
from __future__ import annotations

from django.urls import path

from .uploads import ImageUploadView

urlpatterns = [
    path("", ImageUploadView.as_view(), name="uploads-create"),
]
