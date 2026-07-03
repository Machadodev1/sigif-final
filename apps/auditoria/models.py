from django.db import models

class Auditoria(models.Model):

    MODULOS = [
        ("USUARIOS", "Usuarios"),
        ("PRODUCTOS", "Productos"),
        ("INVENTARIO", "Inventario"),
        ("FACTURACION", "Facturación"),
        ("CONFIGURACION", "Configuración"),
    ]

    usuario = models.CharField(max_length=100)
    accion = models.CharField(max_length=255)
    modulo = models.CharField(max_length=100, choices=MODULOS)
    fecha = models.DateTimeField(auto_now_add=True)