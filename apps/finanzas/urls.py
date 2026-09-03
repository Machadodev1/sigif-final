from django.urls import path
from . import views

app_name = 'finanzas'
urlpatterns = [
    path('', views.dashboard, name='finanzas_dashboard'),
    path('ingresos/', views.movimientos, {'tipo': 'ingresos'}, name='ingresos'),
    path('gastos/', views.movimientos, {'tipo': 'gastos'}, name='gastos'),
    path('gastos/nuevo/', views.editar_gasto, name='nuevo_gasto'),
    path('gastos/<int:pk>/editar/', views.editar_gasto, name='editar_gasto'),
    path('gastos/<int:pk>/eliminar/', views.eliminar_gasto, name='eliminar_gasto'),
    path('rentabilidad/', views.rentabilidad, name='rentabilidad'),
    path('reportes/', views.reportes, name='reportes'),
]
