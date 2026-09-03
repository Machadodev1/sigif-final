# Generated manually for the Finanzas module.
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name='CuentaPorPagar',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('proveedor', models.CharField(max_length=150)),
                ('concepto', models.CharField(max_length=150)),
                ('fecha', models.DateField()),
                ('valor', models.DecimalField(decimal_places=2, max_digits=12)),
                ('valor_pagado', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('fecha_vencimiento', models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Gasto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('concepto', models.CharField(max_length=150)),
                ('categoria', models.CharField(choices=[('ARRIENDO', 'Arriendo'), ('SERVICIOS', 'Servicios públicos'), ('REPUESTOS', 'Compra de repuestos'), ('INSUMOS', 'Insumos'), ('NOMINA', 'Nómina'), ('TRANSPORTE', 'Transporte'), ('PUBLICIDAD', 'Publicidad'), ('IMPUESTOS', 'Impuestos'), ('MANTENIMIENTO', 'Mantenimiento'), ('OTROS', 'Otros')], max_length=20)),
                ('valor', models.DecimalField(decimal_places=2, max_digits=12)),
                ('fecha', models.DateField()),
                ('metodo_pago', models.CharField(choices=[('EFECTIVO', 'Efectivo'), ('TRANSFERENCIA', 'Transferencia'), ('TARJETA', 'Tarjeta'), ('CREDITO', 'Crédito'), ('OTRO', 'Otro')], default='EFECTIVO', max_length=20)),
                ('proveedor', models.CharField(blank=True, max_length=150)),
                ('descripcion', models.TextField(blank=True)),
                ('usuario', models.CharField(max_length=100)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-fecha', '-id']},
        ),
    ]
