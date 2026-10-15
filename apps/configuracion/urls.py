from django.urls import path
from . import views
urlpatterns = [
    path('', views.configuracion, name='configuracion'),
    path('backupypermisos/', views.backupypermisos, name='backupypermisos'),
    path('backup/descargar/<int:backup_id>/', views.descargar_backup, name='descargar_backup'),
    path('backup/restaurar/<int:backup_id>/', views.restaurar_backup, name='restaurar_backup'),
    path('backup/lista/', views.lista_backups_api, name='lista_backups_api'),
]
