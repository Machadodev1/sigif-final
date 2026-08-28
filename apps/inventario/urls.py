from django.urls import path
from django.views.generic.base import RedirectView
from . import views

urlpatterns = [
    path('', views.inventario, name='inventario'),
    path('inv_historial/', views.inv_historial, name='inv_historial'),
    path('inv_control/', views.inv_control, name='inv_control'),
    path('inv_ingresos/', views.inv_ingresos, name='inv_ingresos'),
    path('registrar-entrada/', views.registrar_entrada, name='registrar_entrada'),
    path('entrada/pdf/<int:pk>/', views.exportar_entrada_pdf, name='exportar_entrada_pdf'),
    path('inv_configuracion/', views.inv_configuracion, name='inv_configuracion'),

]