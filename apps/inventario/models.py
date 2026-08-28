from django.db import models


class EntradaInventario(models.Model):

    proveedor = models.CharField(max_length=150)
    documento = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Numero de factura o remision del proveedor"
    )
    usuario = models.CharField(max_length=100, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def numero_factura(self):
        """Numero de factura de entrada generado automaticamente: ENT-00001"""
        return f"ENT-{self.id:05d}"

    def __str__(self):
        return f"Entrada {self.numero_factura()} - {self.proveedor}"


class DetalleEntradaInventario(models.Model):

    entrada = models.ForeignKey(
        EntradaInventario,
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    producto = models.ForeignKey(
        'productos.Producto',
        on_delete=models.CASCADE,
        related_name='entradas'
    )
    cantidad = models.PositiveIntegerField()
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad}"
