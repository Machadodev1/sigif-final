from django.shortcuts import render
from apps.usuarios.models import Usuarios
from apps.productos.models import Producto
from django.http import JsonResponse

def index(request):
    total = Usuarios.objects.count()
    to = Producto.objects.count()
    low_stock = Producto.objects.filter(stock__lt=10).count()

    context = {
        'total': total,
        'to': to,
        'low_stock': low_stock

    }

    return render(request, 'dashboard/index.html', context)

def mant(request):

    return render(request, "mant.html")
