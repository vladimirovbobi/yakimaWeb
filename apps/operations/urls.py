from django.urls import path

from . import views

app_name = "operations"

urlpatterns = [
    path("",          views.dashboard,    name="dashboard"),
    path("mod/",      views.mod_queue,    name="mod_queue"),
    path("mod/<int:decision_id>/", views.mod_action, name="mod_action"),
    path("audit/",    views.audit_viewer, name="audit"),
]
