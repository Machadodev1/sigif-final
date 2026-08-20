from django.db import models
from django.core.validators import MinValueValidator

class Producto (models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(
    max_digits=100,
    decimal_places=0,
    default=0,
    validators=[MinValueValidator(1,message="El precio debe ser mayor que cero.")]
)
    stock = models.IntegerField(
    default=0,
    validators=[MinValueValidator(0,message="Debe haber minimo un producto en el stock")])
    categoria = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre