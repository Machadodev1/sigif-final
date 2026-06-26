from django.shortcuts import render
from .models import Auditoria
from core.decoradores import requerir_rol

# Create your views here.

@requerir_rol(["Admin"])
def auditoria(request):

    datos = Auditoria.objects.all().order_by('-fecha')
    return render(request, 'auditoria/ver_registros.html', {'datos': datos})
#