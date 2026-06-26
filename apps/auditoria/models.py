from django.db import models

# Create your models here.
class Auditoria(models.Model):
    usuario = models.CharField(max_length=100)
    accion = models.CharField(max_length=255)
    modulo = models.CharField(max_length=100)
    fecha = models.DateTimeField(auto_now_add=True)