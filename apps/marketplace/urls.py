from django.urls import path

from . import views

app_name = "marketplace"

urlpatterns = [
    path("",                       views.service_list,   name="service_list"),
    path("leads/",                 views.my_leads,       name="my_leads"),
    path("<slug:slug>/",           views.service_detail, name="service_detail"),
    path("<slug:slug>/inquire/",   views.lead_create,    name="lead_create"),
]
