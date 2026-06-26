from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Usuarios)

class UsuariosAdmin(admin.ModelAdmin):
    list_display = ["id", "nombre", "contra", "telefono", "activo", "fecha_inicio",  "cargo"]
    list_filter = ["cargo"]
    search_fields = ["nombre", "telefono", "fecha_inicio"]
    # list_editable = ["rol"]
