from django.db import models
from django.core.validators import MinValueValidator

CATEGORIAS = [
    ('Frenos', 'Frenos'),
    ('Motor', 'Motor'),
    ('Transmisión', 'Transmisión'),
    ('Lubricantes y Fluidos', 'Lubricantes y Fluidos'),
    ('Suspensión', 'Suspensión'),
    ('Eléctrico', 'Eléctrico'),
    ('Llantas y Ruedas', 'Llantas y Ruedas'),
    ('Dirección', 'Dirección'),
    ('Carrocería', 'Carrocería'),
    ('Accesorios', 'Accesorios'),
    ('Filtros', 'Filtros'),
    ('Repuestos Generales', 'Repuestos Generales'),
    ('Insumos de Taller', 'Insumos de Taller'),
]


def _sanitizar_texto(valor):
    """Elimina caracteres que permitirían inyección de HTML/JS en el frontend."""
    if valor is None:
        return valor
    return str(valor).replace('<', '').replace('>', '')

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
    validators=[MinValueValidator(0,message="El stock no puede ser negativo.")])
    categoria = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # SEGURIDAD: se sanean los campos de texto antes de persistir para
        # impedir XSS almacenado (nombres/categorías que contengan HTML/JS).
        self.nombre = _sanitizar_texto(self.nombre)
        self.categoria = _sanitizar_texto(self.categoria)
        self.descripcion = _sanitizar_texto(self.descripcion)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre