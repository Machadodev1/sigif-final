from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import *

app_name = 'api'

router = DefaultRouter()
router.register(r'auditoria', AuditoriaViewSet, basename='auditoria')
router.register(r'configuracion', EmpresaConfigViewSet, basename='empresa')
router.register(r'clientes', ClienteViewSet, basename='clientes')
router.register(r'facturas', FacturaViewSet, basename='facturas')
router.register(r'productos', ProductoViewSet, basename='productos')
router.register(r'usuarios', UsuarioViewSet, basename='usuarios')

urlpatterns = router.urls

urlpatterns+=[
    path('api/token/logout/', LogoutView.as_view(), name='api_logout')
]