from django.contrib import admin
from .models import *

@admin.register(Usuarios)
class UsuariosAdmin(admin.ModelAdmin):
    list_display = ["id", "nombre", "telefono", "activo", "fecha_inicio", "cargo"]
    list_filter = ["cargo"]
    search_fields = ["nombre", "telefono", "fecha_inicio"]
    # list_editable = ["rol"]

    # readonly_fields = ["activo"]

    def has_delete_permission(self, request, obj=None):
        # SEGURIDAD: el SuperAdmin principal no puede eliminarse desde admin.
        if obj is not None and (obj.es_superadmin_principal or obj.cargo == "SuperAdmin"):
            return False

        return super().has_delete_permission(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if obj is not None and obj.es_superadmin_principal:
            return [field.name for field in self.model._meta.fields if field.name != 'id']
        return super().get_readonly_fields(request, obj)

    # # Mantener el estado activo/inactivo original
    # def save_model(self, request, obj, form, change):
    #     if change:
    #         usuario_original = Usuarios.objects.get(pk=obj.pk)
    #         obj.activo = usuario_original.activo

    #     super().save_model(request, obj, form, change)

