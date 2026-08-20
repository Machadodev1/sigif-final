from django.shortcuts import render
from apps.productos.models import Producto

from apps.configuracion.models import EmpresaConfig
from core.decoradores import requerir_rol
from apps.facturacion.models import DetalleFactura



@requerir_rol(["Admin", "Empleado"])
def inv_configuracion(request):
    config = EmpresaConfig.objects.all()
    print(config)
    print (type(config))
    print("123")
    return render(request, 'configuracion/configuracion.html', {'config': config})



@requerir_rol(["SuperAdmin","Admin", "Empleado"])
def inventario(request):

    producto = Producto.objects.all()

    contexto = {
        'producto': producto
    }


    return render(request, "inventario/inventario.html", contexto)

@requerir_rol(["SuperAdmin","Admin", "Empleado"])
def inv_historial(request):
    movimientos = Producto.objects.all()

    for movimiento in movimientos:
        movimiento.valor_total = movimiento.precio * movimiento.stock

    salidas = DetalleFactura.objects.select_related(
        'producto',
        'factura',
        'factura__cliente'
    ).order_by('-factura__fecha')[:20]

    return render(
        request,
        'inventario/inv_historial.html',
        {
            'movimientos': movimientos,
            'salidas': salidas
        }
    )

@requerir_rol(["SuperAdmin","Admin", "Empleado"])
def inv_control(request):
    producto = Producto.objects.all()

    contexto = {
        'producto': producto
    }

    return render(request, "inventario/inv_control.html", contexto)