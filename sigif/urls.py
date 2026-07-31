from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/', include('apps.api.urls')),
    path('inicio/', include('apps.dashboard.urls')),
    path('', include('apps.usuarios.urls')),
    path('productos/', include('apps.productos.urls')),
    path('inventario/', include('apps.inventario.urls')),
    path('facturacion/', include('apps.facturacion.urls')),
    path('auditoria/', include('apps.auditoria.urls')),
    path('configuracion/', include('apps.configuracion.urls')),
]