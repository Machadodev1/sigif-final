
import os
from django.db import models
from django.conf import settings


class EmpresaConfig(models.Model):
    nombre_comercial = models.CharField(max_length=150, default="SIGIF")
    nit = models.CharField(max_length=50, default="900.123.456-7")
    direccion = models.CharField(max_length=255, default="CASA DE MOYA \"LA AURORA\" ")
    moneda = models.CharField(max_length=50, default="COP ($) - Pesos Colombianos")
    impuesto = models.CharField(max_length=10, default="19%")
    correo_contacto = models.EmailField(default="soporte@sigif.com")
    backup_email = models.EmailField(blank=True, null=True, verbose_name="Correo para envío de backups")
    backup_frecuencia = models.CharField(
        max_length=20,
        choices=[
            ('diario', 'Diario'),
            ('semanal', 'Semanal'),
            ('mensual', 'Mensual'),
            ('nunca', 'Nunca'),
        ],
        default='semanal',
        verbose_name="Frecuencia de backup automático"
    )

    def __str__(self):
        return self.nombre_comercial


class Backup(models.Model):
    TIPO_CHOICES = [
        ('manual', 'Manual'),
        ('automatico', 'Automático'),
    ]

    nombre = models.CharField(max_length=255)
    archivo = models.FileField(upload_to='backups/')
    tamaño = models.BigIntegerField(default=0)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='manual')
    creado_por = models.CharField(max_length=100)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    enviado_email = models.BooleanField(default=False)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.nombre

    def get_tamaño_mb(self):
        return round(self.tamaño / (1024 * 1024), 2)