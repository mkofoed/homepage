from django.urls import path

app_name = "dashboard"

from dashboard import views

urlpatterns = [
    path("", views.dashboard_home, name="home"),
    path("api/chart/", views.htmx_price_chart, name="htmx_price_chart"),
]
