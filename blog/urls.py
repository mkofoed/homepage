from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='blog_index'),
    path('all/', views.post_list, name='blog_list'),
    path('<int:pk>/', views.detail, name='blog_detail'),
]
