"""apps.accounts URLs — mounted under /realtor/."""
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("verify/", views.realtor_verify, name="realtor_verify"),
    path("status/", views.realtor_status, name="realtor_status"),
    path("bio/",    views.realtor_bio_edit, name="realtor_bio_edit"),
]
