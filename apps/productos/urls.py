from django.urls import path
from . import views

urlpatterns = [
    path('', views.productos, name='productos'),
    path('crear_productos/', views.crear_producto, name='crear_productos'),
    path('actualizar_productos/<int:id>/', views.actualizar_producto, name='actualizar_productos'),
    path('activar-desactivar/<int:id>/',views.activar_desactivar_producto,name='activar_desactivar_producto'),
]