from django.contrib.auth.hashers import identify_hasher, make_password
from django.db import migrations, models


def proteger_contrasenas_existentes(apps, schema_editor):
    Usuarios = apps.get_model('usuarios', 'Usuarios')
    for usuario in Usuarios.objects.exclude(contra='').iterator():
        try:
            identify_hasher(usuario.contra)
        except (ValueError, TypeError):
            usuario.contra = make_password(usuario.contra)
            usuario.save(update_fields=['contra'])


class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0012_security'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuarios',
            name='documento',
            field=models.CharField(
                max_length=15,
                unique=True,
                verbose_name='Documento de identidad',
            ),
        ),
        migrations.AlterField(
            model_name='usuarios',
            name='telefono',
            field=models.CharField(
                max_length=12,
                unique=True,
                verbose_name='Teléfono',
            ),
        ),
        migrations.RunPython(proteger_contrasenas_existentes),
    ]