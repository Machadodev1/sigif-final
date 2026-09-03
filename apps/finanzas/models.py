from django.db import models


class Gasto(models.Model):
    CATEGORIAS = [
        ('ARRIENDO', 'Arriendo'), ('SERVICIOS', 'Servicios públicos'),
        ('REPUESTOS', 'Compra de repuestos'), ('INSUMOS', 'Insumos'),
        ('NOMINA', 'Nómina'), ('TRANSPORTE', 'Transporte'),
        ('PUBLICIDAD', 'Publicidad'), ('IMPUESTOS', 'Impuestos'),
        ('MANTENIMIENTO', 'Mantenimiento'), ('OTROS', 'Otros'),
    ]
    METODOS_PAGO = [('EFECTIVO', 'Efectivo'), ('TRANSFERENCIA', 'Transferencia'), ('TARJETA', 'Tarjeta'), ('CREDITO', 'Crédito'), ('OTRO', 'Otro')]
    concepto = models.CharField(max_length=150)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    fecha = models.DateField()
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, default='EFECTIVO')
    proveedor = models.CharField(max_length=150, blank=True)
    descripcion = models.TextField(blank=True)
    usuario = models.CharField(max_length=100)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha', '-id']

    def __str__(self):
        return self.concepto


class CuentaPorPagar(models.Model):
    ESTADOS = [('PENDIENTE', 'Pendiente'), ('PARCIAL', 'Parcialmente pagada'), ('PAGADA', 'Pagada'), ('VENCIDA', 'Vencida')]
    proveedor = models.CharField(max_length=150)
    concepto = models.CharField(max_length=150)
    fecha = models.DateField()
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    valor_pagado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha_vencimiento = models.DateField(null=True, blank=True)

    @property
    def saldo_pendiente(self):
        return max(self.valor - self.valor_pagado, 0)

    @property
    def estado(self):
        from django.utils import timezone
        if self.saldo_pendiente <= 0:
            return 'PAGADA'
        if self.fecha_vencimiento and self.fecha_vencimiento < timezone.localdate():
            return 'VENCIDA'
        if self.valor_pagado:
            return 'PARCIAL'
        return 'PENDIENTE'
