from django.shortcuts import render
from .models import Auditoria
from core.decoradores import requerir_rol
from django.db import models
from datetime import datetime


@requerir_rol(["SuperAdmin","Admin"])
def auditoria(request):

    modulo = request.GET.get("modulo")
    q = request.GET.get("q", "").strip()
    fecha_desde = request.GET.get("fecha_desde")
    fecha_hasta = request.GET.get("fecha_hasta")

    datos = Auditoria.objects.all().order_by("-fecha")

    if modulo:
        datos = datos.filter(modulo=modulo)

    if q:
        datos = datos.filter(models.Q(usuario__icontains=q) | models.Q(accion__icontains=q))

    # filtrar por rango de fechas si se proveen
    try:
        if fecha_desde:
            d = datetime.fromisoformat(fecha_desde)
            datos = datos.filter(fecha__gte=d)
        if fecha_hasta:
            # para incluir todo el día, si el usuario pasa solo fecha, tratamos como fin de día
            h = datetime.fromisoformat(fecha_hasta)
            # si solo viene la fecha, ampliar hasta el fin del día
            if h.hour == 0 and h.minute == 0 and h.second == 0:
                h = h.replace(hour=23, minute=59, second=59)
            datos = datos.filter(fecha__lte=h)
    except Exception:
        # Si hay error de parseo, ignoramos el filtro de fecha
        pass

    modulos = Auditoria.MODULOS

    return render(request, "auditoria/ver_registros.html", {
        "datos": datos,
        "modulos": modulos,
        "modulo_actual": modulo,
        "q": q,
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
    })




