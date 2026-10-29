import json
import os
import shutil
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.core.management import call_command
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.usuarios.models import Usuarios
from apps.auditoria.models import Auditoria
from core.decoradores import requerir_rol
from .models import EmpresaConfig, Backup


def _get_backup_dir():
    backup_dir = settings.BASE_DIR / 'backups'
    backup_dir.mkdir(exist_ok=True)
    return backup_dir


def _crear_backup_db(tipo='manual', request=None):
    backup_dir = _get_backup_dir()
    timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    nombre_archivo = f'sigif_backup_{timestamp}.json'
    ruta_archivo = backup_dir / nombre_archivo

    try:
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            call_command('dumpdata', '--natural-foreign', '--natural-primary', '--exclude=contenttypes', '--exclude=auth.permission', '--exclude=sessions', '--exclude=admin.logentry', stdout=f)

        tamaño = ruta_archivo.stat().st_size

        creado_por = 'Sistema'
        if request and request.session.get('logueado'):
            creado_por = request.session['logueado'].get('nombre', 'Sistema')

        backup = Backup.objects.create(
            nombre=nombre_archivo,
            archivo=f'backups/{nombre_archivo}',
            tamaño=tamaño,
            tipo=tipo,
            creado_por=creado_por
        )

        if request:
            Auditoria.objects.create(
                usuario=creado_por,
                accion=f"GENERÓ BACKUP {'AUTOMÁTICO' if tipo == 'automatico' else 'MANUAL'}: {nombre_archivo}",
                modulo="CONFIGURACION"
            )

        return backup, None
    except Exception as e:
        if ruta_archivo.exists():
            ruta_archivo.unlink()
        return None, str(e)


def _crear_zip_backup(backup):
    backup_dir = _get_backup_dir()
    ruta_json = backup_dir / backup.nombre
    if not ruta_json.exists():
        raise FileNotFoundError(
            f"El archivo del backup '{backup.nombre}' no existe en el servidor. "
            "Genera el backup de nuevo antes de enviarlo."
        )

    nombre_zip = backup.nombre.replace('.json', '.zip')
    ruta_zip = backup_dir / nombre_zip

    with zipfile.ZipFile(ruta_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(ruta_json, backup.nombre)

    return ruta_zip, nombre_zip


def _enviar_backup_email(backup, email_destino):
    try:
        ruta_zip, nombre_zip = _crear_zip_backup(backup)

        email = EmailMessage(
            subject=f'Backup SIGIF - {backup.nombre}',
            body=f'Adjunto encontrará el backup de la base de datos generado el {backup.fecha_creacion.strftime("%d/%m/%Y %H:%M")}.\n\nTamaño: {backup.get_tamaño_mb()} MB\nTipo: {backup.get_tipo_display()}\nGenerado por: {backup.creado_por}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email_destino],
        )
        email.attach_file(ruta_zip)
        email.send()

        backup.enviado_email = True
        backup.save()

        ruta_zip.unlink()
        return True, None
    except Exception as e:
        return False, str(e)


@requerir_rol(["SuperAdmin", "Admin"])
def configuracion(request):
    config = EmpresaConfig.objects.first() or EmpresaConfig()

    if request.method == 'POST':
        es_admin_sesion = request.session.get("logueado") and request.session.get("logueado").get("rol") in ["SuperAdmin", "Admin"]
        if request.user.is_staff or es_admin_sesion:

            def _limpiar_texto(valor, maximo):
                valor = (valor or "").strip()
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
                    config.moneda = "COP ($) - Pesos Colombianos"
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

                    backup_email = (request.POST.get('backup_email') or "").strip()
                    if backup_email:
                        from django.core.validators import validate_email
                        from django.core.exceptions import ValidationError
                        try:
                            validate_email(backup_email)
                        except ValidationError:
                            raise ValueError("backup_email")
                        config.backup_email = backup_email
                    else:
                        config.backup_email = None

                    config.backup_frecuencia = request.POST.get('backup_frecuencia', 'semanal')

                    messages.success(request, "La configuración del sistema fue actualizada correctamente.", extra_tags='module-configuracion')

                config.save()

                Auditoria.objects.create(
                    usuario=request.session["logueado"]["nombre"],
                    accion="ACTUALIZÓ LA CONFIGURACIÓN DE LA EMPRESA",
                    modulo="CONFIGURACION"
                )
            except (ValueError, TypeError):
                messages.error(request, "Verifica los datos ingresados. El correo debe ser válido y los campos no pueden quedar vacíos.", extra_tags='module-configuracion')

    return render(request, 'configuracion/configuracion.html', {'config': config})


@requerir_rol(["SuperAdmin", "Admin"])
def backupypermisos(request):
    usuarios = Usuarios.objects.all()
    backups = Backup.objects.all()[:20]
    config = EmpresaConfig.objects.first() or EmpresaConfig()
    ultimo_backup = backups[0] if backups else None

    logueado = request.session.get("logueado") or {}
    rol_actual = logueado.get("rol")
    es_superadmin = rol_actual == "SuperAdmin"

    if request.method == "POST":
        action = request.POST.get('action')

        # Retrocompatibilidad: peticiones antiguas de cambio de rol sin 'action'.
        if not action and 'rol_asignar' in request.POST:
            action = 'cambiar_rol'

        if action == 'cambiar_rol':
            return _cambiar_rol(request)

        elif action == 'generar_backup':
            return _generar_backup(request)

        elif action == 'programar_backup':
            return _programar_backup(request)

        elif action == 'enviar_backup_email':
            return _enviar_backup_email_view(request)

    return render(
        request,
        "configuracion/backupypermisos.html",
        {
            "usuarios": usuarios,
            "backups": backups,
            "config": config,
            "ultimo_backup": ultimo_backup,
            "es_superadmin": es_superadmin,
            "puede_gestionar": rol_actual in ["SuperAdmin", "Admin"],
            "puede_enviar_email": rol_actual in ["SuperAdmin", "Admin"],
        }
    )


def _cambiar_rol(request):
    user_id = request.POST.get("user_id")
    cargo = request.POST.get("rol_asignar")

    logueado = request.session.get("logueado") or {}
    actor = Usuarios.objects.filter(
        pk=logueado.get("id"), activo=True
    ).first()

    cargos_validos = [c[0] for c in Usuarios.CARGOS]
    if cargo not in cargos_validos:
        messages.error(request, "El rol seleccionado no es válido.")
        return redirect("backupypermisos")

    if not str(user_id).isdigit():
        messages.error(request, "El usuario seleccionado no es válido.")
        return redirect("backupypermisos")

    if (actor and actor.cargo != "SuperAdmin") and cargo == "SuperAdmin":
        Auditoria.objects.create(
            usuario=actor.nombre,
            accion=f"INTENTO RECHAZADO DE ASIGNAR SUPERADMIN A USUARIO {user_id}",
            modulo="CONFIGURACION",
        )
        messages.error(request, "Solo el SuperAdmin puede asignar el rol de SuperAdmin.")
        return redirect("backupypermisos")

    try:
        usuario = Usuarios.objects.get(id=int(user_id))

        if usuario.es_superadmin_principal:
            messages.error(request, "El SuperAdmin principal no puede modificarse.")
            return redirect("backupypermisos")

        usuario.cargo = cargo
        usuario.save()
        Auditoria.objects.create(
            usuario=request.session["logueado"]["nombre"],
            accion=f"ACTUALIZÓ EL CARGO DE {usuario.nombre}: {cargo}",
            modulo="CONFIGURACION"
        )

        usuario.refresh_from_db()
        messages.success(request, f"El cargo de {usuario.nombre} fue actualizado a {usuario.cargo}.")

    except Usuarios.DoesNotExist:
        messages.error(request, "El usuario seleccionado no existe.")

    return redirect("backupypermisos")


def _generar_backup(request):
    backup, error = _crear_backup_db('manual', request)
    if error:
        messages.error(request, f"Error al generar backup: {error}")
        return redirect("backupypermisos")

    messages.success(request, f"Backup generado correctamente: {backup.nombre} ({backup.get_tamaño_mb()} MB)")

    config = EmpresaConfig.objects.first()
    if config and config.backup_email:
        exito, error_email = _enviar_backup_email(backup, config.backup_email)
        if exito:
            messages.success(request, f"Backup enviado en .zip a {config.backup_email}.")
        else:
            messages.error(request, f"El backup se generó, pero falló el envío por correo: {error_email}")
    else:
        messages.warning(request, "El backup se generó, pero no hay un correo configurado para su envío. Configúralo en la pestaña General y Empresa.")

    return redirect("backupypermisos")


def _programar_backup(request):
    config = EmpresaConfig.objects.first() or EmpresaConfig()
    frecuencia = request.POST.get('frecuencia', 'semanal')
    config.backup_frecuencia = frecuencia
    config.save()

    messages.success(request, f"Frecuencia de backup automático configurada a: {dict(config._meta.get_field('backup_frecuencia').choices).get(frecuencia, frecuencia)}")
    return redirect("backupypermisos")


def _enviar_backup_email_view(request):
    backup_id = request.POST.get('backup_id')
    if not backup_id:
        messages.error(request, "Debe seleccionar un backup.")
        return redirect("backupypermisos")

    backup = get_object_or_404(Backup, id=backup_id)

    # Validar que el archivo del backup exista en disco antes de intentar enviarlo.
    if not (_get_backup_dir() / backup.nombre).exists():
        messages.error(
            request,
            f"El archivo del backup '{backup.nombre}' no existe en el servidor. "
            "Genera el backup de nuevo."
        )
        return redirect("backupypermisos")

    config = EmpresaConfig.objects.first()

    if not config or not config.backup_email:
        messages.error(request, "No hay correo configurado para envío de backups. Configúrelo en la pestaña General.")
        return redirect("backupypermisos")

    exito, error = _enviar_backup_email(backup, config.backup_email)
    if exito:
        messages.success(request, f"Backup {backup.nombre} enviado correctamente a {config.backup_email}")
    else:
        messages.error(request, f"Error al enviar backup: {error}")

    return redirect("backupypermisos")


@requerir_rol(["SuperAdmin", "Admin"])
def descargar_backup(request, backup_id):
    backup = get_object_or_404(Backup, id=backup_id)
    backup_dir = _get_backup_dir()
    ruta_archivo = backup_dir / backup.nombre

    if not ruta_archivo.exists():
        messages.error(request, "El archivo de backup no existe en el servidor.")
        return redirect("backupypermisos")

    Auditoria.objects.create(
        usuario=request.session["logueado"]["nombre"],
        accion=f"DESCARGÓ BACKUP: {backup.nombre}",
        modulo="CONFIGURACION"
    )

    response = FileResponse(open(ruta_archivo, 'rb'), as_attachment=True, filename=backup.nombre)
    return response


@requerir_rol(["SuperAdmin"])
def restaurar_backup(request, backup_id):
    if request.method != 'POST':
        return redirect("backupypermisos")

    backup = get_object_or_404(Backup, id=backup_id)
    backup_dir = _get_backup_dir()
    ruta_archivo = backup_dir / backup.nombre

    if not ruta_archivo.exists():
        messages.error(request, "El archivo de backup no existe en el servidor.")
        return redirect("backupypermisos")

    try:
        call_command('loaddata', str(ruta_archivo))
        messages.success(request, f"Backup {backup.nombre} restaurado correctamente.")

        Auditoria.objects.create(
            usuario=request.session["logueado"]["nombre"],
            accion=f"RESTAURÓ BACKUP: {backup.nombre}",
            modulo="CONFIGURACION"
        )
    except Exception as e:
        messages.error(request, f"Error al restaurar backup: {str(e)}")

    return redirect("backupypermisos")


@requerir_rol(["SuperAdmin", "Admin"])
def lista_backups_api(request):
    backups = Backup.objects.all()[:50]
    data = [{
        'id': b.id,
        'nombre': b.nombre,
        'tamaño_mb': b.get_tamaño_mb(),
        'tipo': b.get_tipo_display(),
        'creado_por': b.creado_por,
        'fecha_creacion': b.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
        'enviado_email': b.enviado_email,
    } for b in backups]
    return JsonResponse({'backups': data})