from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


class ExpiringTokenAuthentication(TokenAuthentication):

    # Tiempo de validez del token (configurable via settings).
    def _tiempo_expiracion(self):
        return timedelta(
            minutes=getattr(settings, 'TOKEN_EXPIRATION_MINUTES', 60)
        )

    def authenticate_credentials(self, key):
        model = self.get_model()

        try:
            token = model.objects.select_related('user').get(key=key)
        except model.DoesNotExist:
            raise AuthenticationFailed({
                'error': 'Token inválido',
                'is_authenticated': False
            })

        # SEGURIDAD: los tokens caducan después de su intervalo de validez.
        vencimiento = token.created + self._tiempo_expiracion()
        if timezone.now() > vencimiento:
            token.delete()
            raise AuthenticationFailed({
                'error': 'El Token ha expirado',
                'is_authenticated': False
            })

        if not token.user.is_active:
            raise AuthenticationFailed({
                'error': 'Usuario inactivo',
                'is_authenticated': False
            })

        return (token.user, token)