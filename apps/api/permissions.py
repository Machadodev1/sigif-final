from rest_framework.permissions import BasePermission

from apps.usuarios.models import Usuarios

ROLES_ESCRITURA = ('SuperAdmin', 'Admin')
ROLES_LECTURA = ('SuperAdmin', 'Admin', 'Empleado')


def _rol_actor(request):
    """Determina el rol del actor real de la petición.

    Prioridad:
      1. Sesión web SIGIF ('logueado'), que usa el modelo Usuarios (cargo).
      2. Token/User de Django (staff): se considera SuperAdmin si es staff;
         si está autenticado pero no es staff, se deniegan las escrituras.
    """
    logueado = getattr(request, 'session', None) and request.session.get('logueado')
    if logueado:
        usuario = Usuarios.objects.filter(pk=logueado.get('id'), activo=True).first()
        if usuario:
            return usuario.cargo
        return None

    user = getattr(request, 'user', None)
    if user and getattr(user, 'is_authenticated', False):
        if getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False):
            return 'SuperAdmin'
        return 'Empleado'

    return None


class RolApiPermission(BasePermission):
    """Permite consultar la API sin autenticación.
    Las operaciones de escritura requieren un rol autorizado."""

    ESTA = 'RolApiPermission'

    def has_permission(self, request, view):

        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True

        rol = _rol_actor(request)

        if not rol or rol not in ROLES_LECTURA:
            return False

        return rol in ROLES_ESCRITURA