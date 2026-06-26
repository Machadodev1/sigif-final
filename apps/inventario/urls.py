from django.urls import path
from django.views.generic.base import RedirectView
from . import views

urlpatterns = [
    path('', views.inventario, name='inventario'),
    path('inv_historial/', views.inv_historial, name='inv_historial'),
    path('inv_control/', views.inv_control, name='inv_control'),
    path('inv_configuracion/', views.inv_configuracion, name='inv_configuracion'),

]