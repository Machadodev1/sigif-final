from django.shortcuts import render, redirect

from .models import EmpresaConfig


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


def backupypermisos(request):
    return render(request, 'configuracion/backupypermisos.html')