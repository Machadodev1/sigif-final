import os
import sys
import threading
import time

from django.db import connection


_INTERVALO_SEGUNDOS = int(os.getenv('BACKUP_SCHEDULER_INTERVAL', '3600'))
_hilo_iniciado = False


def ejecutar_revision_backup():
    from apps.configuracion.models import EmpresaConfig, Backup
    from apps.configuracion.management.commands.backup_automatico import (
        FRECUENCIAS_DIAS,
    )
    from apps.configuracion.views import _crear_backup_db, _enviar_backup_email

    try:
        config = EmpresaConfig.objects.first()
        if not config or config.backup_frecuencia == 'nunca':
            return

        ultimo = Backup.objects.filter(tipo='automatico').first()
        if ultimo:
            dias = FRECUENCIAS_DIAS.get(config.backup_frecuencia, 7)
            transcurridos = (timezone_now() - ultimo.fecha_creacion).days
            if transcurridos < dias:
                return

        backup, error = _crear_backup_db(tipo='automatico')
        if error or not backup:
            return

        if config.backup_email:
            _enviar_backup_email(backup, config.backup_email)
    except Exception:
        pass


def timezone_now():
    from django.utils import timezone
    return timezone.now()


def _bucle():
    while True:
        try:
            ejecutar_revision_backup()
        except Exception:
            pass
        finally:
            try:
                connection.close()
            except Exception:
                pass
        time.sleep(_INTERVALO_SEGUNDOS)


def iniciar_scheduler():
    global _hilo_iniciado

    if _hilo_iniciado:
        return

    if os.getenv('BACKUP_SCHEDULER_ENABLED', 'True').lower() not in ('1', 'true', 'yes', 'on'):
        return

    argv = ' '.join(sys.argv)
    comandos_excluidos = (
        'migrate', 'makemigrations', 'collectstatic', 'test', 'pytest',
        'shell', 'dbshell', 'loaddata', 'dumpdata', 'createsuperuser',
        'backup_automatico', 'check', 'spectacular',
    )
    if any(cmd in argv for cmd in comandos_excluidos):
        return

    if 'runserver' in argv and os.environ.get('RUN_MAIN') != 'true':
        return

    _hilo_iniciado = True
    hilo = threading.Thread(target=_bucle, name='sigif-backup-scheduler', daemon=True)
    hilo.start()
