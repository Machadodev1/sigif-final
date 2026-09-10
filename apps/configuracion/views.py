from django.shortcuts import render, redirect
from django.contrib import messages
from apps.usuarios.models import Usuarios
from .models import EmpresaConfig
from core.decoradores import requerir_rol
from apps.auditoria.models import Auditoria

@requerir_rol(["SuperAdmin", "Admin"])
def configuracion(request):

    # single-row: se crea sobre la marcha si aún no existe.
    config = EmpresaConfig.objects.first() or EmpresaConfig()

    if request.method == 'POST':
        # Permite guardar si es staff o si tiene rol autorizado en la sesión
        es_admin_sesion = request.session.get("logueado") and request.session.get("logueado").get("rol") in ["SuperAdmin", "Admin"]
        if request.user.is_staff or es_admin_sesion:

            def _limpiar_texto(valor, maximo):
                valor = (valor or "").strip()
                # SEGURIDAD: elimina marcado HTML/JS de los campos de texto.
                valor = valor.replace('<', '').replace('>', '')
                if len(valor) > maximo:
                    valor = valor[:maximo]
                return valor

            try:
                if 'nombre_comercial' in request.POST:
                    config.nombre_comercial = _limpiar_texto(request.POST.get('nombre_comercial'), 150)
                    config.nit = _limpiar_texto(request.POST.get('nit'), 50)
                    config.direccion = _limpiar_texto(request.POST.get('direccion'), 255)
                    if not config.nombre_comercial:
                        raise ValueError("nombre_comercial")
                    messages.success(request, "Los datos de la empresa fueron actualizados correctamente.", extra_tags='module-configuracion')

                elif 'moneda' in request.POST:
                    config.moneda = "COP ($) - Pesos Colombianos"  # Fijo a COP
                    config.impuesto = _limpiar_texto(request.POST.get('impuesto'), 10)
                    correo_contacto = (request.POST.get('correo_contacto') or "").strip()
                    if len(correo_contacto) <= 100:
                        from django.core.validators import validate_email
                        from django.core.exceptions import ValidationError
                        try:
                            validate_email(correo_contacto)
                        except ValidationError:
                            raise ValueError("correo_contacto")
                        config.correo_contacto = correo_contacto
                    else:
                        raise ValueError("correo_contacto")
                    messages.success(request, "La configuración del sistema fue actualizada correctamente.", extra_tags='module-configuracion')

                config.save()

                Auditoria.objects.create(
                    usuario=request.session["logueado"]["nombre"],
                    accion="ACTUALIZÓ LA CONFIGURACIÓN DE LA EMPRESA",
                    modulo="CONFIGURACION"
                )
            except (ValueError, TypeError):
                # Sin cambios si la validación falla: se evita guardar datos corruptos.
                messages.error(request, "Verifica los datos ingresados. El correo debe ser válido y los campos no pueden quedar vacíos.", extra_tags='module-configuracion')

    return render(request, 'configuracion/configuracion.html', {'config': config})




@requerir_rol(["SuperAdmin", "Admin"])
def backupypermisos(request):

    usuarios = Usuarios.objects.all()

    if request.method == "POST":
        user_id = request.POST.get("user_id")
        cargo = request.POST.get("rol_asignar")

        logueado = request.session.get("logueado") or {}
        actor = Usuarios.objects.filter(
            pk=logueado.get("id"), activo=True
        ).first()

        # SEGURIDAD: roles permitidos; nada fuera de la lista se guarda.
        cargos_validos = [c[0] for c in Usuarios.CARGOS]
        if cargo not in cargos_validos:
            messages.error(
                request,
                "El rol seleccionado no es válido.",
            )
            return redirect("backupypermisos")

        if not str(user_id).isdigit():
            messages.error(request, "El usuario seleccionado no es válido.")
            return redirect("backupypermisos")

        # SEGURIDAD: un Admin no puede asignar (ni auto-asignarse) SuperAdmin.
        if (actor and actor.cargo != "SuperAdmin") and cargo == "SuperAdmin":
            Auditoria.objects.create(
                usuario=actor.nombre,
                accion=f"INTENTO RECHAZADO DE ASIGNAR SUPERADMIN A USUARIO {user_id}",
                modulo="CONFIGURACION",
            )
            messages.error(
                request,
                "Solo el SuperAdmin puede asignar el rol de SuperAdmin.",
            )
            return redirect("backupypermisos")

        try:
            usuario = Usuarios.objects.get(id=int(user_id))

            # SEGURIDAD: el SuperAdmin principal está protegido.
            if usuario.es_superadmin_principal:
                messages.error(
                    request,
                    "El SuperAdmin principal no puede modificarse.",
                )
                return redirect("backupypermisos")

            usuario.cargo = cargo
            usuario.save()
            Auditoria.objects.create(
                usuario=request.session["logueado"]["nombre"],
                accion=f"ACTUALIZÓ EL CARGO DE {usuario.nombre}: {cargo}",
                modulo="CONFIGURACION"
            )

            usuario.refresh_from_db()

            messages.success(
                request,
                f"El cargo de {usuario.nombre} fue actualizado a {usuario.cargo}."
            )

        except Usuarios.DoesNotExist:
            messages.error(request, "El usuario seleccionado no existe.")

        return redirect("backupypermisos")

    return render(
        request,
        "configuracion/backupypermisos.html",
        {"usuarios": usuarios}
    )