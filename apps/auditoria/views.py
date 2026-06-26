from django.shortcuts import render
from .models import Auditoria

# Create your views here.

def auditoria(request):
    datos = Auditoria.objects.all().order_by('-fecha')
    return render(request, 'auditoria/ver_registros.html', {'datos': datos})
#