from django.apps import AppConfig


class ConfiguracionConfig(AppConfig):
    name = 'apps.configuracion'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        from . import scheduler
        scheduler.iniciar_scheduler()
