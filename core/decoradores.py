from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def _obtener_usuario_de_sesion(request):
    from apps.usuarios.models import Usuarios

    logueado = request.session.get("logueado") or {}
    usuario_id = logueado.get("id")
    if not usuario_id:
        return None

    usuario = Usuarios.objects.filter(pk=usuario_id, activo=True).first()
    if usuario:
        # SEGURIDAD: el rol y el nombre de la sesión se refrescan desde la
        # base de datos; no se confía en valores alterados en el navegador.
        request.session["logueado"] = {
            "id": usuario.id,
            "nombre": usuario.nombre,
            "rol": usuario.cargo,
        }
        request.session.modified = True
    return usuario


def requerir_rol(roles_permitidos):

    def decorator(view_func):

        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):

            usuario = _obtener_usuario_de_sesion(request)

            # Inferir nombre del módulo para poder etiquetar el mensaje
            try:
                resolver = getattr(request, "resolver_match", None)

                if resolver and resolver.app_name:
                    modulo = resolver.app_name
                else:
                    components = view_func.__module__.split(".")
                    modulo = (
                        components[-2]
                        if components[-1] == "views" and len(components) >= 2
                        else components[-1]
                    )

            except Exception:
                modulo = "app"

            if not usuario:

                messages.error(
                    request,
                    "Debes iniciar sesión para continuar.",
                    extra_tags=f"module-{modulo}"
                )

                return redirect("dashboard")

            rol = usuario.cargo

            if rol in roles_permitidos:
                return view_func(request, *args, **kwargs)

            messages.error(
                request,
                "No tienes permisos para acceder a este módulo.",
                extra_tags=f"module-{modulo}"
            )

            return redirect("dashboard")

        return _wrapped_view

    return decorator


def impedir_crear_superadmin(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if request.method == "POST":

            from apps.usuarios.models import Usuarios

            cargo = request.POST.get("cargo")
            logueado = request.session.get("logueado") or {}
            actor = Usuarios.objects.filter(
                pk=logueado.get("id"), activo=True
            ).first()
            cargo_actual = actor.cargo if actor else None

            if cargo == "SuperAdmin" and cargo_actual != "SuperAdmin":

                messages.error(
                    request,
                    "Solo el SuperAdmin puede crear otro SuperAdmin."
                )

                return redirect("crear_usuarios")

        return view_func(request, *args, **kwargs)

    return wrapper


def requerir_rol_accion(roles_permitidos, url_retorno):

    def decorator(view_func):

        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):

            usuario = _obtener_usuario_de_sesion(request)

            # Inferir nombre del módulo
            try:
                resolver = getattr(request, "resolver_match", None)

                if resolver and resolver.app_name:
                    modulo = resolver.app_name
                else:
                    components = view_func.__module__.split(".")
                    modulo = (
                        components[-2]
                        if components[-1] == "views" and len(components) >= 2
                        else components[-1]
                    )

            except Exception:
                modulo = "app"

            if not usuario:

                messages.error(
                    request,
                    "Debes iniciar sesión para continuar.",
                    extra_tags=f"module-{modulo}"
                )

                return redirect("dashboard")

            rol = usuario.cargo

            # TIENE PERMISO
            if rol in roles_permitidos:
                return view_func(request, *args, **kwargs)

            # NO TIENE PERMISO
            messages.warning(
                request,
                "No tienes permitido realizar esta acción.",
                extra_tags=f"module-{modulo}"
            )

            # VOLVER AL MÓDULO
            return redirect(url_retorno)

        return _wrapped_view

    return decorator