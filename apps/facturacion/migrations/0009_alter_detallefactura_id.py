class Migration(migrations.Migration):

    dependencies = [
        ('facturacion', '0008_merge_20260813_1534'),
    ]

    operations = [
        migrations.AlterField(
            model_name='detallefactura',
            name='id',
            field=models.BigAutoField(
                auto_created=True,
                primary_key=True,
                serialize=False,
                verbose_name='ID'
            ),
        ),
    ]

