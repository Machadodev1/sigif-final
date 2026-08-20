from django.db import models

class Usuarios (models.Model):
    nombre = models.CharField(max_length=100)
    contra = models.CharField(max_length=15)
    telefono = models.CharField(max_length=12)
    activo = models.BooleanField(default=True)
    fecha_inicio = models.DateField(null=True, blank=True)
    CARGOS = (
        ("SuperAdmin", "SUPERADMIN"),
        ("Admin", "ADMIN"),
        ("Empleado", "EMPLEADO"),
    )
    cargo = models.CharField(max_length=15, choices=CARGOS, default = "Empleado")

    def __str__(self):
        return self.nombre