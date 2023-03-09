from django.urls import path

from .views import AboutView

app_name = "home"
urlpatterns = [
    path("", AboutView.as_view(), name="about"),
]
