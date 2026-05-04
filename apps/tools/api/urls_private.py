"""Private tool routes — /api/v1/tools/."""
from django.urls import path

from .views import (
    DescriptionWriterRunView,
    FurnitureRemoverRunView,
    ToolTaskStatusView,
)

urlpatterns = [
    path("description/",       DescriptionWriterRunView.as_view(),
         name="tools-description"),
    path("furniture-remover/", FurnitureRemoverRunView.as_view(),
         name="tools-furniture-remover"),
    path("tasks/<int:task_id>/", ToolTaskStatusView.as_view(),
         name="tools-task-status"),
]
