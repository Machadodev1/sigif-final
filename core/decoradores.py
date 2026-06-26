from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def requerir_rol(roles_permitidos):

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            logueado = request.session.get("logueado")
            if not logueado:
                messages.error(request, "Debes iniciar sesión para continuar.")
                return redirect("dashboard")

            
            rol = logueado.get("rol")

            
            if not rol:
                try:
                    is_staff = getattr(request.user, "is_staff", None)
                    if is_staff is not None:
                        rol = "Admin" if is_staff else "Empleado"
                except Exception:
                    rol = None


            if rol in roles_permitidos:
                return view_func(request, *args, **kwargs)

            messages.error(request, "No tienes permisos para acceder a esta sección.")
            return redirect("dashboard")

        return _wrapped_view

    return decorator

