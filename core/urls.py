from django.contrib.auth.decorators import login_required
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("architecture/", views.architecture, name="architecture"),
    path("health/", views.health_check, name="health_check_home"),
    path("api/health/", views.health_check, name="health_check"),
    path("api/github-stats/", views.github_stats, name="github_stats"),
    path("api/metrics/", login_required(views.metrics), name="metrics"),
]
