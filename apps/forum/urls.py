from django.urls import path

from . import views

app_name = "forum"

urlpatterns = [
    path("",                       views.thread_list,    name="thread_list"),
    path("new/",                   views.thread_create,  name="thread_create"),
    path("vote/<str:target_type>/<int:target_id>/", views.vote, name="vote"),
    path("<slug:slug>/",           views.thread_detail,  name="thread_detail"),
    path("<slug:slug>/reply/",     views.reply_create,   name="reply_create"),
]
