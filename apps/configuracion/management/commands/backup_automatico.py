from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.configuracion.models import EmpresaConfig, Backup
from apps.configuracion.views import _crear_backup_db, _enviar_backup_email


FRECUENCIAS_DIAS = {
    'diario': 1,
    'semanal': 7,
    'mensual': 30,
}


class Command(BaseCommand):
    help = 'Genera un backup automático de la base de datos según la frecuencia configurada.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--forzar',
            action='store_true',
            help='Genera el backup sin importar la frecuencia configurada.',
        )

    def handle(self, *args, **options):
        config = EmpresaConfig.objects.first() or EmpresaConfig()
        frecuencia = config.backup_frecuencia

        if frecuencia == 'nunca' and not options['forzar']:
            self.stdout.write(self.style.WARNING('La automatización de backups está desactivada.'))
            return

        if not options['forzar']:
            ultimo = Backup.objects.filter(tipo='automatico').first()
            if ultimo:
                dias = FRECUENCIAS_DIAS.get(frecuencia, 7)
                transcurridos = (timezone.now() - ultimo.fecha_creacion).days
                if transcurridos < dias:
                    self.stdout.write(
                        self.style.NOTICE(
                            f'Aún no corresponde generar backup ({transcurridos} de {dias} días).'
                        )
                    )
                    return

        backup, error = _crear_backup_db(tipo='automatico')

        if error:
            self.stderr.write(self.style.ERROR(f'Error al generar backup: {error}'))
            return

        self.stdout.write(self.style.SUCCESS(f'Backup generado: {backup.nombre} ({backup.get_tamaño_mb()} MB)'))

        if config.backup_email:
            exito, error = _enviar_backup_email(backup, config.backup_email)
            if exito:
                self.stdout.write(self.style.SUCCESS(f'Backup enviado a {config.backup_email}'))
            else:
                self.stderr.write(self.style.ERROR(f'Error al enviar backup: {error}'))
        else:
            self.stdout.write(self.style.WARNING('No hay correo configurado para envío de backups.'))
