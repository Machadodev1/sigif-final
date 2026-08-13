from django.shortcuts import render
from django.db.models import Sum
from django.utils import timezone
from apps.usuarios.models import Usuarios
from apps.productos.models import Producto
from apps.auditoria.models import Auditoria
from apps.facturacion.models import Factura

def index(request):
    
    total = Usuarios.objects.count()
    to = Producto.objects.count()
    low_stock = Producto.objects.filter(stock__lt=5).count()

    
    now = timezone.now()
    inicio_mes = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    sales_this_month = Factura.objects.filter(
        fecha__gte=inicio_mes
    ).aggregate(total=Sum('total'))['total'] or 0

    actividad_reciente = Auditoria.objects.order_by('-fecha')[:5]

    productos_bajo_stock = Producto.objects.filter(stock__lt=5).order_by('stock')[:5]

    context = {
        'total': total,
        'to': to,
        'low_stock': low_stock,
        'sales_this_month': sales_this_month,
        'actividad_reciente': actividad_reciente,
        'productos_bajo_stock': productos_bajo_stock,
    }

    return render(request, 'dashboard/index.html', context)

def mant(request):

    return render(request, "mant.html")
