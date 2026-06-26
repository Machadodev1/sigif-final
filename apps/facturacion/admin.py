# Register your models here.
from django.contrib import admin
from .models import Cliente, Factura

admin.site.register(Cliente)
admin.site.register(Factura)

