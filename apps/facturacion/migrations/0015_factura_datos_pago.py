from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('facturacion', '0014_alter_detallefactura_id')]

    operations = [
        migrations.AddField(model_name='factura', name='metodo_pago', field=models.CharField(choices=[('EFECTIVO', 'Efectivo'), ('TARJETA', 'Tarjeta'), ('TRANSFERENCIA', 'Transferencia'), ('CREDITO', 'Crédito')], default='EFECTIVO', max_length=20)),
        migrations.AddField(model_name='factura', name='valor_pagado', field=models.DecimalField(decimal_places=2, default=0, max_digits=10)),
        migrations.AddField(model_name='factura', name='fecha_vencimiento', field=models.DateField(blank=True, null=True)),
        migrations.RunSQL("UPDATE facturacion_factura SET valor_pagado = total WHERE metodo_pago != 'CREDITO'", migrations.RunSQL.noop),
    ]
