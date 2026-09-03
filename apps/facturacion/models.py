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
    METODOS_PAGO = [
        ('EFECTIVO', 'Efectivo'), ('TARJETA', 'Tarjeta'),
        ('TRANSFERENCIA', 'Transferencia'), ('CREDITO', 'Crédito'),
    ]
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
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, default='EFECTIVO')
    valor_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_vencimiento = models.DateField(null=True, blank=True)

    @property
    def saldo_pendiente(self):
        return max(self.total - self.valor_pagado, Decimal('0'))

    @property
    def estado_pago(self):
        from django.utils import timezone
        if self.saldo_pendiente <= 0:
            return 'PAGADA'
        if self.fecha_vencimiento and self.fecha_vencimiento < timezone.localdate():
            return 'VENCIDA'
        return 'PARCIAL' if self.valor_pagado else 'PENDIENTE'

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
