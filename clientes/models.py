from django.db import models
from django.db.models import Sum

# Create your models here.
class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    correo = models.EmailField()
    documento = models.CharField(max_length=50, blank=True, null=True, unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nombre

    def get_total_gastado(self):
        resultado = self.factura_set.aggregate(
            total_compras=Sum('total')
        )['total_compras']

        return resultado if resultado else 0

    def get_ultima_fecha(self):
        ultima_factura = self.factura_set.order_by('-fecha').first()

        return ultima_factura.fecha if ultima_factura else "Sin compras"