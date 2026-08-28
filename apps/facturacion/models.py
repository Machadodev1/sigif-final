from django.db import models
from django.db.models import Sum

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    correo = models.EmailField()

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


from decimal import Decimal

class Factura(models.Model):
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE
    )

    usuario = models.CharField(
    max_length=100,
    null=True,
    blank=True
)

    fecha = models.DateTimeField(
        auto_now_add=True
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    descuento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    @property
    def base_gravable(self):
        return self.total / Decimal("1.19")

    @property
    def iva(self):
        return self.total - self.base_gravable

    def __str__(self):
        return f"Factura #{self.id} - {self.cliente.nombre}"


class DetalleFactura(models.Model):
    factura = models.ForeignKey(
        Factura,
        on_delete=models.CASCADE,
        related_name='detalles'
    )

    producto = models.ForeignKey(
        'productos.Producto',
        on_delete=models.CASCADE
    )

    cantidad = models.PositiveIntegerField()

    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return f"{self.producto.nombre} - {self.cantidad}"