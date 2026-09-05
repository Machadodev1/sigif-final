from django.db import migrations


def establecer_superadmin_principal(apps, schema_editor):
    Usuarios = apps.get_model('usuarios', 'Usuarios')
    Usuarios.objects.update(es_superadmin_principal=False)
    Usuarios.objects.filter(id=10, cargo='SuperAdmin').update(
        es_superadmin_principal=True,
        activo=True,
    )


def revertir_superadmin_principal(apps, schema_editor):
    Usuarios = apps.get_model('usuarios', 'Usuarios')
    Usuarios.objects.filter(es_superadmin_principal=True).update(
        es_superadmin_principal=False,
    )


class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0014_model_validators_and_email'),
    ]

    operations = [
        migrations.RunPython(
            establecer_superadmin_principal,
            revertir_superadmin_principal,
        ),
    ]