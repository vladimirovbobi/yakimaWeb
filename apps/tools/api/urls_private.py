"""Private tool routes — /api/v1/tools/ + /api/v1/streams/tools/."""
from django.urls import path

from .views import (
    DescriptionWriterRunView,
    FurnitureRemoverRunView,
    ToolTaskStatusView,
    ToolTaskStreamView,
)

urlpatterns = [
    path("description/",       DescriptionWriterRunView.as_view(),
         name="tools-description"),
    path("furniture-remover/", FurnitureRemoverRunView.as_view(),
         name="tools-furniture-remover"),
    path("tasks/<int:task_id>/", ToolTaskStatusView.as_view(),
         name="tools-task-status"),
    path("streams/<int:task_id>/", ToolTaskStreamView.as_view(),
         name="tools-task-stream"),
]
