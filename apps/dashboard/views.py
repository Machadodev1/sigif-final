from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum

from apps.usuarios.models import Usuarios
from apps.productos.models import Producto
from apps.facturacion.models import Factura
from apps.auditoria.models import Auditoria


def index(request):
    total = Usuarios.objects.count()
    to = Producto.objects.count()
    low_stock = Producto.objects.filter(stock__lt=5).count()

    ahora = timezone.localtime()
    inicio_mes = ahora.replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    ventas_totales = (
        Factura.objects
        .filter(fecha__gte=inicio_mes)
        .aggregate(total=Sum("total"))["total"] or 0
    )

    actividades_recientes = (
        Auditoria.objects
        .order_by("-fecha")[:4]
    )

    context = {
        "total": total,
        "to": to,
        "low_stock": low_stock,
        "ventas_totales": ventas_totales,
        "actividades_recientes": actividades_recientes,
    }

    return render(request, "dashboard/index.html", context)


def mant(request):
    return render(request, "mant.html")