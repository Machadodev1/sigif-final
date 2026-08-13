from django.shortcuts import render
from apps.usuarios.models import Usuarios
from apps.productos.models import Producto
from apps.facturacion.models import Factura
from django.db.models import Sum

def index(request):
    total = Usuarios.objects.count()
    to = Producto.objects.count()
    low_stock = Producto.objects.filter(stock__lt=5).count()

    ventas_totales = Factura.objects.aggregate(
        total=Sum('total')
    )['total'] or 0

    context = {
        'total': total,
        'to': to,
        'low_stock': low_stock,
        'ventas_totales': ventas_totales,
    }

    return render(request, 'dashboard/index.html', context)

def mant(request):
    return render(request, 'mant.html')