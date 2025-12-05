from django.urls import path
from . import views

urlpatterns = [
    path('echo/', views.echo, name='api_echo'),
    path('calculate/', views.calculate, name='api_calculate'),
    path('random-quote/', views.random_quote, name='api_random_quote'),
    path('fibonacci/', views.fibonacci, name='api_fibonacci'),
    path('palindrome/', views.palindrome, name='api_palindrome'),
]
