from django.urls import path

from . import views

app_name = "content"

urlpatterns = [
    path("",                  views.post_list,      name="post_list"),
    path("write/",            views.post_authoring, name="post_author"),
    path("mine/",             views.my_posts,       name="my_posts"),
    path("videos/",           views.videos,         name="videos"),
    path("<slug:slug>/",      views.post_detail,    name="post_detail"),
    path("<slug:slug>/comment/", views.comment_create, name="comment_create"),
]
