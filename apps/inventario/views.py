from django.shortcuts import render
from django.db.models import Q
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


    return render(request, "inventario/inventario.html", contexto)

@requerir_rol(["Admin", "Empleado"])
def inv_historial(request):
    q = request.GET.get('q', '').strip()
    movimientos = Producto.objects.all().order_by('-fecha_actualizacion', '-id')
    
    if q:
        movimientos = movimientos.filter(
            Q(nombre__icontains=q) | 
            Q(categoria__icontains=q) | 
            Q(id__icontains=q)
        )

    for movimiento in movimientos:
        movimiento.total = movimiento.precio * movimiento.stock

    contexto = {
        'movimientos': movimientos,
        'q': q,
    }

    return render(request, "inventario/inv_historial.html", contexto)

@requerir_rol(["Admin", "Empleado"])
def inv_control(request):
    producto = Producto.objects.all()

    contexto = {
        'producto': producto
    }

    return render(request, "inventario/inv_control.html", contexto)