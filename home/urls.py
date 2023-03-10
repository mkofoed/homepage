from django.urls import path, include

from .views import AboutView

app_name = "home"
urlpatterns = [
    path("", AboutView.as_view(), name="about"),
    path("blog/", include("blog.urls", namespace="blog")),
    path("markdownx/", include("markdownx.urls")),
]
