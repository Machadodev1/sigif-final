from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def requerir_rol(roles_permitidos):

    def decorator(view_func):

        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):

            logueado = request.session.get("logueado")

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

            if not logueado:

                messages.error(
                    request,
                    "Debes iniciar sesión para continuar.",
                    extra_tags=f"module-{modulo}"
                )

                return redirect("dashboard")

            rol = logueado.get("rol")

            if not rol:

                is_staff = getattr(request.user, "is_staff", None)

                if is_staff is not None:
                    rol = "Admin" if is_staff else "Empleado"

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

            cargo = request.POST.get("cargo")
            cargo_actual = request.session["logueado"].get("cargo")

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

            logueado = request.session.get("logueado")

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

            if not logueado:

                messages.error(
                    request,
                    "Debes iniciar sesión para continuar.",
                    extra_tags=f"module-{modulo}"
                )

                return redirect("dashboard")

            rol = logueado.get("rol")

            if not rol:

                is_staff = getattr(request.user, "is_staff", None)

                if is_staff is not None:
                    rol = "Admin" if is_staff else "Empleado"

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