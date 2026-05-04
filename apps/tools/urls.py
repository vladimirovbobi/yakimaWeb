from django.urls import path

from . import views

app_name = "tools"

urlpatterns = [
    path("",                     views.tool_index, name="index"),
    path("description-writer/",  views.description_writer, name="description_writer"),
    path("description-writer/<int:pk>/", views.description_writer_result, name="description_writer_result"),
    path("furniture-remover/",   views.furniture_remover, name="furniture_remover"),
    path("usage/<slug:slug>.json", views.usage_today_json, name="usage_json"),
]
