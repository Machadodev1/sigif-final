from django.db import migrations, models
from django.db.models import Q


def marcar_superadmin_principal(apps, schema_editor):
    Usuarios = apps.get_model('usuarios', 'Usuarios')
    principal = Usuarios.objects.filter(cargo='SuperAdmin').order_by('id').first()
    if principal:
        principal.es_superadmin_principal = True
        principal.activo = True
        principal.save(update_fields=['es_superadmin_principal', 'activo'])


def desmarcar_superadmin_principal(apps, schema_editor):
    Usuarios = apps.get_model('usuarios', 'Usuarios')
    Usuarios.objects.filter(es_superadmin_principal=True).update(
        es_superadmin_principal=False
    )


class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0011_usuarios_documento'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuarios',
            name='es_superadmin_principal',
            field=models.BooleanField(default=False, editable=False, verbose_name='SuperAdmin principal'),
        ),
        migrations.AlterField(
            model_name='usuarios',
            name='contra',
            field=models.CharField(max_length=128, verbose_name='Contraseña'),
        ),
        migrations.AddConstraint(
            model_name='usuarios',
            constraint=models.UniqueConstraint(
                condition=Q(es_superadmin_principal=True),
                fields=('es_superadmin_principal',),
                name='unico_superadmin_principal',
            ),
        ),
        migrations.RunPython(
            marcar_superadmin_principal,
            desmarcar_superadmin_principal,
        ),
    ]