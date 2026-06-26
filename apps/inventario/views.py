from django.shortcuts import render
from apps.productos.models import Producto

from apps.configuracion.models import EmpresaConfig
from core.decoradores import requerir_rol




@requerir_rol(["Admin", "Empleado"])
def inv_configuracion(request):
    config = EmpresaConfig.objects.all()
    print(config)
    print (type(config))
    print("123")
    return render(request, 'configuracion/configuracion.html', {'config': config})



@requerir_rol(["Admin", "Empleado"])
def inventario(request):

    producto = Producto.objects.all()

    contexto = {
        'producto': producto
    }


    return render(request, "inventario/inventario copy.html", contexto)

@requerir_rol(["Admin", "Empleado"])
def inv_historial(request):

    return render(request, "inventario/inv_historial.html")

@requerir_rol(["Admin", "Empleado"])
def inv_control(request):
    producto = Producto.objects.all()

    contexto = {
        'producto': producto
    }

    return render(request, "inventario/inv_control.html", contexto)