from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='dashboard'),
    path('mant/', views.mant, name='mant'),
]