from django.db import migrations, models
from django.db.models.functions import Lower
from django.core.validators import RegexValidator


class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0013_security_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuarios',
            name='nombre',
            field=models.CharField(
                max_length=100,
                validators=[RegexValidator(r'^[^\W\d_]+(?:[ \t]+[^\W\d_]+)*$')],
                verbose_name='Nombre del empleado',
            ),
        ),
        migrations.AlterField(
            model_name='usuarios',
            name='documento',
            field=models.CharField(
                max_length=15,
                unique=True,
                validators=[RegexValidator(r'^\d+$')],
                verbose_name='Documento de identidad',
            ),
        ),
        migrations.AlterField(
            model_name='usuarios',
            name='telefono',
            field=models.CharField(
                max_length=12,
                unique=True,
                validators=[RegexValidator(r'^\d+$')],
                verbose_name='Teléfono',
            ),
        ),
        migrations.AddConstraint(
            model_name='usuarios',
            constraint=models.UniqueConstraint(
                Lower('correo'),
                name='unico_correo_sin_mayusculas',
            ),
        ),
    ]