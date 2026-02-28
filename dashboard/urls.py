from django.urls import path

from dashboard import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard_home, name="home"),
    path("api/chart/", views.htmx_price_chart, name="htmx_price_chart"),
]
