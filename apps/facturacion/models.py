# Create your models here.
from django.db import models
from django.db.models import Sum 

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    correo = models.EmailField()
    
    def __str__(self):
        return self.nombre
    def get_total_gastado(self):
        resultado = self.factura_set.aggregate(total_compras=Sum('total'))['total_compras']
        return resultado if resultado else 0

    def get_ultima_fecha(self):
        ultima_factura = self.factura_set.order_by('-fecha').first()
        return ultima_factura.fecha if ultima_factura else "Sin compras"

class Factura(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    fecha = models.DateField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Factura de {self.cliente.nombre} - ${self.total}"