from django.urls import path
from django.views.generic.base import RedirectView
from . import views

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='factura-list', permanent=False), name='facturacion'),
    path('facturas/', views.FacturaListView.as_view(), name='factura-list'),
    path('facturas/<int:pk>/', views.FacturaDetailView.as_view(), name='factura-detail'),
    path('clientes/', views.clientes_view, name='clientes'),
    path('productos/', views.productos_facturacion_view, name='productos_facturacion'),
    path('pago/', views.pago, name='pago'),
    path('confirmar-venta/', views.confirmar_venta, name='confirmar_venta'),
    path('factura/pdf/<int:pk>/', views.exportar_factura_pdf, name='exportar_factura_pdf'),
]