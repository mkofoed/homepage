from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('architecture/', views.architecture, name='architecture'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/health/', views.health_check, name='health_check'),
    path('api/github-stats/', views.github_stats, name='github_stats'),
    path('api/metrics/', views.metrics, name='metrics'),
]
