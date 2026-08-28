from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Producto)

class ProductosAdmin(admin.ModelAdmin):
    list_display = ["id", "nombre", "descripcion", "precio", "stock", "categoria", "activo", "fecha_creacion", "fecha_actualizacion", "total"]
    list_filter = ["categoria"]
    search_fields = ["nombre", "descripcion"]