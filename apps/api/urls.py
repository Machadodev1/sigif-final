from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'api'

router = DefaultRouter()
router.register(r'auditoria', views.AuditoriaViewSet, basename='auditoria')
router.register(r'configuracion', views.EmpresaConfigViewSet, basename='empresa-config')
router.register(r'cliente', views.ClienteViewSet, basename='cliente')
router.register(r'factura', views.FacturaViewSet, basename='factura')
router.register(r'producto', views.ProductoViewSet, basename='producto')
router.register(r'usuario', views.UsuarioViewSet, basename='usuario')

urlpatterns = [path('', views.api_index, name='index')] + router.urls
