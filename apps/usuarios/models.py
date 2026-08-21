from django.db import models


class Usuarios(models.Model):
    nombre = models.CharField(max_length=100, verbose_name='Nombre del empleado')
    contra = models.CharField(max_length=15, verbose_name='Contraseña')
    telefono = models.CharField(max_length=12, verbose_name='Teléfono')
    correo = models.EmailField(max_length=100, unique=True, verbose_name='Correo electrónico')
    activo = models.BooleanField(default=True, verbose_name='Activo')
    fecha_inicio = models.DateField(null=True, blank=True, verbose_name='Fecha de inicio')
    CARGOS = (
        ("SuperAdmin", "SUPERADMIN"),
        ("Admin", "ADMIN"),
        ("Empleado", "EMPLEADO"),
    )
    cargo = models.CharField(
        max_length=15,
        choices=CARGOS,
        default='Empleado',
        verbose_name='Cargo',
    )

    def __str__(self):
        return self.nombre