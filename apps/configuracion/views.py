from django.shortcuts import render, redirect
from django.contrib import messages
from apps.usuarios.models import Usuarios
from .models import EmpresaConfig
from core.decoradores import requerir_rol


@requerir_rol(["Admin"])
def configuracion(request):

    config = EmpresaConfig.objects.get (id=1)


    if request.method == 'POST':

        
        if request.user.is_staff:
           
            if 'nombre_comercial' in request.POST:
                config.nombre_comercial = request.POST.get('nombre_comercial')
                config.nit = request.POST.get('nit')
                config.direccion = request.POST.get('direccion')
            
            elif 'moneda' in request.POST:
                config.moneda = request.POST.get('moneda')
                config.impuesto = request.POST.get('impuesto')
                config.correo_contacto = request.POST.get('correo_contacto')

            config.save() 
            
    return render(request, 'configuracion/configuracion.html', {'config': config})




@requerir_rol(["Admin"])
def backupypermisos(request):

    usuarios = Usuarios.objects.all()

    if request.method == "POST":
        user_id = request.POST.get("user_id")
        cargo = request.POST.get("rol_asignar")

        print("USER ID:", user_id)
        print("CARGO RECIBIDO:", cargo)

        try:
            usuario = Usuarios.objects.get(id=user_id)

            print("USUARIO:", usuario.nombre)
            print("CARGO ANTES:", usuario.cargo)

            usuario.cargo = cargo
            usuario.save()

            usuario.refresh_from_db()

            print("CARGO DESPUÉS:", usuario.cargo)

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