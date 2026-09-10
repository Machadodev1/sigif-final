from django.contrib.auth.hashers import check_password, identify_hasher, make_password
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Lower


class Usuarios(models.Model):
    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre del empleado',
        validators=[RegexValidator(r'^[^\W\d_]+(?:[ \t]+[^\W\d_]+)*$')],
    )
    documento = models.CharField(
        max_length=15,
        verbose_name='Documento de identidad',
        unique=True,
        validators=[RegexValidator(r'^\d+$')],
    )
    contra = models.CharField(max_length=128, verbose_name='Contraseña')
    telefono = models.CharField(
        max_length=12,
        verbose_name='Teléfono',
        unique=True,
        validators=[RegexValidator(r'^\d+$')],
    )
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
    es_superadmin_principal = models.BooleanField(
        default=False,
        editable=False,
        verbose_name='SuperAdmin principal',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['es_superadmin_principal'],
                condition=models.Q(es_superadmin_principal=True),
                name='unico_superadmin_principal',
            ),
            models.UniqueConstraint(
                Lower('correo'),
                name='unico_correo_sin_mayusculas',
            ),
        ]

    def set_password(self, raw_password):
        self.contra = make_password(raw_password)

    def check_password(self, raw_password):
        # SEGURIDAD: se admite temporalmente la contraseña heredada en texto
        # plano solo para poder migrarla a hash en el siguiente guardado.
        try:
            return check_password(raw_password, self.contra)
        except (ValueError, TypeError):
            return self.contra == raw_password

    def save(self, *args, **kwargs):
        # SEGURIDAD: la unicidad del correo no depende de cómo lo escriba el
        # cliente ni de la sensibilidad a mayúsculas de la base de datos.
        if self.correo:
            self.correo = self.correo.strip().lower()

        # SEGURIDAD: nunca se persiste una contraseña nueva en texto plano,
        # incluso si llega desde un formulario o una petición manipulada.
        try:
            identify_hasher(self.contra)
        except (ValueError, TypeError):
            self.contra = make_password(self.contra)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre