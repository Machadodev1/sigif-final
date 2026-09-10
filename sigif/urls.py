from django.contrib import admin
from django.urls import path, include
from apps.api.views import LogoutView, LoginTokenView
from core.error_views import (
    error_400,
    error_403,
    error_404,
    error_500,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/', include('apps.api.urls')),
    path('inicio/', include('apps.dashboard.urls')),
    path('', include('apps.usuarios.urls')),
    path('productos/', include('apps.productos.urls')),
    path('inventario/', include('apps.inventario.urls')),
    path('facturacion/', include('apps.facturacion.urls')),
    path('finanzas/', include('apps.finanzas.urls')),
    path('auditoria/', include('apps.auditoria.urls')),
    path('configuracion/', include('apps.configuracion.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui'
    ),

    path(
        'api/redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc'
    ),
    path('api/api-token-auth/', LoginTokenView.as_view(), name='api_token_auth'),
    path('api/auth/logout/', LogoutView.as_view(), name='api_logout')
]

handler400 = error_400
handler403 = error_403
handler404 = error_404
handler500 = error_500
