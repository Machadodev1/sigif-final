from apps.usuarios.models import Usuarios


def menu_modulos(request):
    """Expone los módulos que el usuario autenticado puede ver en el menú.

    El rol se lee de la base de datos (no de la sesión) para que los cambios
    de cargo se reflejen de inmediato.
    """
    logueado = request.session.get('logueado') or {}
    usuario = Usuarios.objects.filter(pk=logueado.get('id'), activo=True).first()
    cargo = usuario.cargo if usuario else None

    es_admin = cargo in ('SuperAdmin', 'Admin')

    return {
        'modulo_dashboard': cargo is not None,
        'modulo_productos': cargo in ('SuperAdmin', 'Admin', 'Empleado'),
        'modulo_inventario': cargo in ('SuperAdmin', 'Admin', 'Empleado'),
        'modulo_facturacion': cargo in ('SuperAdmin', 'Admin', 'Empleado'),
        'modulo_finanzas': cargo in ('SuperAdmin', 'Admin'),
        'modulo_usuarios': es_admin,
        'modulo_auditoria': es_admin,
        'modulo_configuracion': es_admin,
    }