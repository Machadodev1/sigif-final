from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import apps as django_apps
from django.db import models

from core.middleware import get_current_user

_registered = set()


def register_signals_for_app(app_label):
    """Register post_save and post_delete handlers for all models in the given app label.

    `app_label` should be the short label (e.g., 'facturacion', 'inventario').
    """
    if app_label in _registered:
        return
    try:
        app_config = django_apps.get_app_config(app_label)
    except LookupError:
        return

    # find the valid modulo choices from Auditoria model if available
    Auditoria = None
    try:
        Auditoria = django_apps.get_model('apps.auditoria', 'Auditoria')
        valid_modulos = {k for k, _ in Auditoria.MODULOS}
    except Exception:
        valid_modulos = set()

    def _modulo_for_label(label):
        lab = label.upper()
        return lab if lab in valid_modulos else (list(valid_modulos)[0] if valid_modulos else lab)

    modulo_value = _modulo_for_label(app_config.label)

    for model in app_config.get_models():
        sender = model

        # define handlers in closure to capture sender and modulo_value
        def make_save(sender_model):
            @receiver(post_save, sender=sender_model)
            def _on_save(sender, instance, created, **kwargs):
                try:
                    AuditoriaModel = django_apps.get_model('apps.auditoria', 'Auditoria')
                    user = get_current_user()
                    usuario = user.username if user and getattr(user, 'is_authenticated', False) else 'system'
                    action = 'Creó' if created else 'Actualizó'
                    AuditoriaModel.objects.create(
                        usuario=usuario,
                        accion=f"{action} {sender.__name__} (id={getattr(instance, 'pk', '')})",
                        modulo=modulo_value,
                    )
                except Exception:
                    # Do not let audit failures break the main flow
                    return
            return _on_save

        def make_delete(sender_model):
            @receiver(post_delete, sender=sender_model)
            def _on_delete(sender, instance, **kwargs):
                try:
                    AuditoriaModel = django_apps.get_model('apps.auditoria', 'Auditoria')
                    user = get_current_user()
                    usuario = user.username if user and getattr(user, 'is_authenticated', False) else 'system'
                    AuditoriaModel.objects.create(
                        usuario=usuario,
                        accion=f"Eliminó {sender.__name__} (id={getattr(instance, 'pk', '')})",
                        modulo=modulo_value,
                    )
                except Exception:
                    return
            return _on_delete

        make_save(sender)
        make_delete(sender)

    _registered.add(app_label)
