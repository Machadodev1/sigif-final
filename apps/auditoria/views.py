from django.shortcuts import render
from .models import Auditoria
from core.decoradores import requerir_rol


@requerir_rol(["Admin"])
def auditoria(request):

    modulo = request.GET.get("modulo")

    datos = Auditoria.objects.all().order_by("-fecha")

    if modulo:
        datos = datos.filter(modulo=modulo)

    modulos = Auditoria.MODULOS

    return render(request, "auditoria/ver_registros.html", {
        "datos": datos,
        "modulos": modulos,
        "modulo_actual": modulo,
    })