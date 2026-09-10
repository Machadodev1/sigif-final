from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from rest_framework.authtoken.views import obtain_auth_token
from apps.api.views import LogoutView
from core.error_views import error_400, error_403, error_404, error_500
# pyrefly: ignore [missing-import]
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
    path('api/api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('api/auth/logout/', LogoutView.as_view(), name='api_logout')
]

# Manejadores de errores HTTP personalizados
handler400 = error_400
handler403 = error_403
handler404 = error_404
handler500 = error_500

# URLs de previsualización (solo en modo DEBUG)
if settings.DEBUG:
    urlpatterns += [
        path('errores/preview/400/', lambda req: error_400(req), name='preview_400'),
        path('errores/preview/403/', lambda req: error_403(req), name='preview_403'),
        path('errores/preview/404/', lambda req: error_404(req), name='preview_404'),
        path('errores/preview/500/', lambda req: error_500(req), name='preview_500'),
    ]

