from django.urls import path
from . import views

app_name = 'finanzas'
urlpatterns = [
    # 1. Estado de resultados (P&G)
    path('', views.dashboard, name='finanzas_dashboard'),
    
    # 2. Reporte de ventas por categoría
    path('ventas-categoria/', views.ventas_categoria, name='ventas_categoria'),
    path('ingresos/', views.ventas_categoria, name='ingresos'),
    
    # 3. Historial de gastos operativos
    path('gastos/', views.gastos, name='gastos'),
    path('gastos/nuevo/', views.editar_gasto, name='nuevo_gasto'),
    path('gastos/<int:pk>/editar/', views.editar_gasto, name='editar_gasto'),
    path('gastos/<int:pk>/eliminar/', views.eliminar_gasto, name='eliminar_gasto'),
    
    # 4. Rentabilidad de inventario
    path('rentabilidad/', views.rentabilidad, name='rentabilidad'),
    
    # 5. Reporte de caja y conciliación
    path('caja-conciliacion/', views.caja_conciliacion, name='caja_conciliacion'),
    path('reportes/', views.caja_conciliacion, name='reportes'),
]
