from django.apps import AppConfig


class AuditoriaConfig(AppConfig):
    name = 'apps.auditoria'
    verbose_name = 'Auditoría'

    def ready(self):
        # registrar señales para apps críticas
        try:
            from . import signals as auditoria_signals
            targets = ['usuarios', 'productos', 'inventario', 'facturacion', 'configuracion']
            for t in targets:
                auditoria_signals.register_signals_for_app(t)
        except Exception:
            # no bloquear la carga si algo falla
            pass
