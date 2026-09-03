from collections import defaultdict
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib import messages
from django.db.models import Sum, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.auditoria.models import Auditoria
from apps.facturacion.models import DetalleFactura, Factura
from apps.inventario.models import DetalleEntradaInventario
from core.decoradores import requerir_rol, requerir_rol_accion
from .models import Gasto


def _periodo(request):
    hoy = timezone.localdate()
    # El año ofrece una visión útil al entrar al módulo, incluso cuando las
    # últimas ventas pertenecen al mes anterior.
    opcion = request.GET.get('periodo', 'ano')
    inicio, fin = hoy.replace(day=1), hoy
    if opcion == 'hoy': inicio = fin = hoy
    elif opcion == 'semana': inicio = hoy - timedelta(days=hoy.weekday())
    elif opcion == 'ano': inicio = hoy.replace(month=1, day=1)
    elif opcion == 'personalizado':
        try:
            inicio = datetime.strptime(request.GET.get('desde'), '%Y-%m-%d').date()
            fin = datetime.strptime(request.GET.get('hasta'), '%Y-%m-%d').date()
        except (TypeError, ValueError): opcion = 'mes'
    return inicio, fin, opcion


def _costos_detalles(detalles):
    """Costo unitario desde inventario; usa el costo conocido más reciente.

    En SIGIF algunas ventas históricas se registraron antes de que existiera
    el módulo de entradas. Para no reportarlas artificialmente sin costo, se
    usa la última compra disponible como costo de referencia en ese caso.
    """
    costo, productos = Decimal('0'), defaultdict(lambda: {'producto': None, 'cantidad': 0, 'ingresos': Decimal('0'), 'costos': Decimal('0')})
    for detalle in detalles:
        compras = DetalleEntradaInventario.objects.filter(producto=detalle.producto)
        compra = compras.filter(entrada__fecha__lte=detalle.factura.fecha).order_by('-entrada__fecha', '-id').first()
        if not compra:
            compra = compras.order_by('-entrada__fecha', '-id').first()
        unitario = compra.precio if compra else Decimal('0')
        subtotal_costo = unitario * detalle.cantidad
        costo += subtotal_costo
        item = productos[detalle.producto_id]
        item['producto'], item['cantidad'] = detalle.producto, item['cantidad'] + detalle.cantidad
        item['ingresos'], item['costos'] = item['ingresos'] + detalle.subtotal, item['costos'] + subtotal_costo
    for item in productos.values():
        item['ganancia'] = item['ingresos'] - item['costos']
        item['margen'] = (item['ganancia'] / item['ingresos'] * 100) if item['ingresos'] else Decimal('0')
    return costo, list(productos.values())


def _resumen(inicio, fin):
    # Evita ``fecha__date``: SQLite ejecuta una función Python para extraer la
    # fecha y registros heredados con valores no normalizados pueden hacerla
    # fallar. El rango directo sobre DateTimeField es portable y seguro.
    desde = timezone.make_aware(datetime.combine(inicio, time.min))
    hasta = timezone.make_aware(datetime.combine(fin + timedelta(days=1), time.min))
    facturas = Factura.objects.filter(fecha__gte=desde, fecha__lt=hasta).select_related('cliente')
    detalles = DetalleFactura.objects.filter(factura__in=facturas).select_related('producto', 'factura')
    gastos = Gasto.objects.filter(fecha__range=(inicio, fin))
    # Solo el valor efectivamente pagado es ingreso; las ventas a crédito
    # quedan disponibles en Cuentas por cobrar.
    ingresos = sum((f.valor_pagado for f in facturas), Decimal('0'))
    total_gastos = gastos.aggregate(valor=Sum('valor'))['valor'] or Decimal('0')
    costos, productos = _costos_detalles(detalles)
    bruta, neta = ingresos - costos, ingresos - costos - total_gastos
    dias, metodos = defaultdict(lambda: Decimal('0')), defaultdict(lambda: Decimal('0'))
    for factura in facturas:
        dias[timezone.localtime(factura.fecha).strftime('%d/%m')] += factura.valor_pagado
        metodos[factura.get_metodo_pago_display()] += factura.valor_pagado
    for gasto in gastos:
        dias[gasto.fecha.strftime('%d/%m')] -= gasto.valor
    return {'facturas': facturas, 'detalles': detalles, 'gastos': gastos, 'ingresos': ingresos, 'costos': costos, 'gastos_total': total_gastos, 'utilidad_bruta': bruta, 'utilidad_neta': neta, 'margen': (neta / ingresos * 100) if ingresos else Decimal('0'), 'ventas': facturas.count(), 'ticket': ingresos / facturas.count() if facturas.exists() else Decimal('0'), 'productos': productos, 'dias': dict(dias), 'metodos_pago': dict(metodos)}


@requerir_rol(['SuperAdmin', 'Admin', 'Empleado'])
def dashboard(request):
    """1. Estado de resultados (P&G): Pérdidas y ganancias consolidado."""
    inicio, fin, opcion = _periodo(request)
    data = _resumen(inicio, fin)
    data.update({'inicio': inicio, 'fin': fin, 'periodo': opcion})
    data['gastos_categoria'] = list(data['gastos'].values('categoria').annotate(total=Sum('valor')).order_by('-total'))
    return render(request, 'finanzas/dashboard.html', data)


@requerir_rol(['SuperAdmin', 'Admin', 'Empleado'])
def ventas_categoria(request):
    """2. Reporte de ventas por categoría: Identifica qué categoría genera más dinero y rentabilidad."""
    inicio, fin, opcion = _periodo(request)
    data = _resumen(inicio, fin)
    
    # Agrupación profunda por categoría de producto
    cat_map = defaultdict(lambda: {
        'categoria': '', 'ingresos': Decimal('0'), 'costos': Decimal('0'),
        'unidades': 0, 'facturas': set(), 'productos': set()
    })
    
    for det in data['detalles']:
        cat = det.producto.categoria or 'Repuestos Generales'
        entry = cat_map[cat]
        entry['categoria'] = cat
        entry['ingresos'] += det.subtotal
        
        compras = DetalleEntradaInventario.objects.filter(producto=det.producto)
        compra = compras.filter(entrada__fecha__lte=det.factura.fecha).order_by('-entrada__fecha', '-id').first()
        if not compra:
            compra = compras.order_by('-entrada__fecha', '-id').first()
        unitario = compra.precio if compra else Decimal('0')
        costo_sub = unitario * det.cantidad
        
        entry['costos'] += costo_sub
        entry['unidades'] += det.cantidad
        entry['facturas'].add(det.factura_id)
        entry['productos'].add(det.producto.nombre)
        
    categorias_resumen = []
    total_unidades = 0
    for cat, item in cat_map.items():
        ganancia = item['ingresos'] - item['costos']
        margen = (ganancia / item['ingresos'] * 100) if item['ingresos'] else Decimal('0')
        total_unidades += item['unidades']
        categorias_resumen.append({
            'categoria': cat,
            'ingresos': item['ingresos'],
            'costos': item['costos'],
            'ganancia': ganancia,
            'margen': margen,
            'unidades': item['unidades'],
            'transacciones': len(item['facturas']),
            'total_skus': len(item['productos'])
        })
        
    categorias_resumen.sort(key=lambda x: x['ingresos'], reverse=True)
    
    data.update({
        'inicio': inicio,
        'fin': fin,
        'periodo': opcion,
        'categorias_resumen': categorias_resumen,
        'total_unidades': total_unidades,
        'categoria_lider': categorias_resumen[0] if categorias_resumen else None,
        'categoria_rentable': sorted(categorias_resumen, key=lambda x: x['ganancia'], reverse=True)[0] if categorias_resumen else None,
    })
    return render(request, 'finanzas/ventas_categoria.html', data)


@requerir_rol(['SuperAdmin', 'Admin', 'Empleado'])
def gastos(request):
    """3. Historial de gastos operativos: Desglose y registro de en qué se gasta el dinero."""
    inicio, fin, opcion = _periodo(request)
    gastos_qs = Gasto.objects.filter(fecha__range=(inicio, fin))
    
    cat_filtro = request.GET.get('categoria', '')
    met_filtro = request.GET.get('metodo_pago', '')
    if cat_filtro:
        gastos_qs = gastos_qs.filter(categoria=cat_filtro)
    if met_filtro:
        gastos_qs = gastos_qs.filter(metodo_pago=met_filtro)
        
    data = _resumen(inicio, fin)
    
    # Agrupación de gastos por categoría para métricas y gráficos
    gastos_por_categoria = list(
        Gasto.objects.filter(fecha__range=(inicio, fin))
        .values('categoria')
        .annotate(total=Sum('valor'), cantidad=Count('id'))
        .order_by('-total')
    )
    
    # Gastos pagados en efectivo vs otros medios
    gastos_efectivo = Gasto.objects.filter(fecha__range=(inicio, fin), metodo_pago='EFECTIVO').aggregate(total=Sum('valor'))['total'] or Decimal('0')
    gastos_bancos = data['gastos_total'] - gastos_efectivo
    
    dias_periodo = max((fin - inicio).days + 1, 1)
    promedio_diario = data['gastos_total'] / Decimal(str(dias_periodo))
    
    data.update({
        'inicio': inicio,
        'fin': fin,
        'periodo': opcion,
        'gastos': gastos_qs,
        'gastos_por_categoria': gastos_por_categoria,
        'categoria_mayor_gasto': gastos_por_categoria[0] if gastos_por_categoria else None,
        'gastos_efectivo': gastos_efectivo,
        'gastos_bancos': gastos_bancos,
        'promedio_diario_gasto': promedio_diario,
        'categorias_opciones': Gasto.CATEGORIAS,
        'metodos_opciones': Gasto.METODOS_PAGO,
        'filtro_categoria_actual': cat_filtro,
        'filtro_metodo_actual': met_filtro,
    })
    return render(request, 'finanzas/gastos.html', data)


@requerir_rol_accion(['SuperAdmin', 'Admin'], 'finanzas:gastos')
def editar_gasto(request, pk=None):
    gasto = get_object_or_404(Gasto, pk=pk) if pk else None
    if request.method == 'POST':
        try:
            campos = {k: request.POST[k].strip() for k in ('concepto', 'categoria', 'fecha', 'metodo_pago', 'proveedor', 'descripcion')}
            campos['valor'] = Decimal(request.POST['valor'])
            campos['usuario'] = request.session.get('logueado', {}).get('nombre', 'Usuario')
            if gasto:
                for key, value in campos.items(): setattr(gasto, key, value)
                gasto.save(); accion = 'ACTUALIZÓ'
            else:
                gasto = Gasto.objects.create(**campos); accion = 'REGISTRÓ'
            Auditoria.objects.create(usuario=campos['usuario'], accion=f'{accion} GASTO: {gasto.concepto}', modulo='FINANZAS')
            messages.success(request, 'Gasto operativo registrado correctamente.')
        except (KeyError, ValueError, ArithmeticError):
            messages.error(request, 'Verifica los datos del gasto ingresado.')
    return redirect('finanzas:gastos')


@requerir_rol_accion(['SuperAdmin', 'Admin'], 'finanzas:gastos')
def eliminar_gasto(request, pk):
    if request.method == 'POST':
        gasto = get_object_or_404(Gasto, pk=pk)
        nombre = gasto.concepto
        gasto.delete()
        messages.success(request, f'Gasto “{nombre}” eliminado correctamente.')
    return redirect('finanzas:gastos')


@requerir_rol(['SuperAdmin', 'Admin', 'Empleado'])
def rentabilidad(request):
    """4. Rentabilidad de inventario: Márgenes de ganancia obtenidos por rotación de repuestos."""
    inicio, fin, opcion = _periodo(request)
    data = _resumen(inicio, fin)
    productos = data['productos']
    
    # Calcular rotación de inventario para cada producto
    for item in productos:
        prod = item['producto']
        total_unidades = (prod.stock + item['cantidad']) if prod else item['cantidad']
        item['rotacion'] = (item['cantidad'] / total_unidades * 100) if total_unidades > 0 else 0
        
    data.update({
        'inicio': inicio,
        'fin': fin,
        'periodo': opcion,
        'productos_rentabilidad': sorted(productos, key=lambda x: x['ganancia'], reverse=True),
        'mas_vendidos': sorted(productos, key=lambda x: x['cantidad'], reverse=True)[:5],
        'mayor_margen': sorted(productos, key=lambda x: x['margen'], reverse=True)[:5]
    })
    return render(request, 'finanzas/rentabilidad.html', data)


@requerir_rol(['SuperAdmin', 'Admin', 'Empleado'])
def caja_conciliacion(request):
    """5. Reporte de caja y conciliación: Cortes de caja y balance de entradas/salidas diarias."""
    inicio, fin, opcion = _periodo(request)
    data = _resumen(inicio, fin)
    facturas = data['facturas']
    gastos_qs = data['gastos']
    
    # Agrupación por fecha para balance y cortes diarios
    dias_caja = defaultdict(lambda: {
        'fecha': None,
        'ventas_efectivo': Decimal('0'),
        'ventas_tarjeta': Decimal('0'),
        'ventas_transferencia': Decimal('0'),
        'ventas_credito': Decimal('0'),
        'total_entradas': Decimal('0'),
        'gastos_efectivo': Decimal('0'),
        'gastos_otros': Decimal('0'),
        'total_salidas': Decimal('0'),
        'saldo_caja_efectivo': Decimal('0'),
        'total_neto': Decimal('0'),
        'num_ventas': 0,
        'num_gastos': 0
    })
    
    total_efectivo_ventas = Decimal('0')
    total_tarjeta_ventas = Decimal('0')
    total_transf_ventas = Decimal('0')
    total_credito_ventas = Decimal('0')
    
    for fac in facturas:
        f_date = timezone.localtime(fac.fecha).date()
        entry = dias_caja[f_date]
        entry['fecha'] = f_date
        entry['total_entradas'] += fac.valor_pagado
        entry['num_ventas'] += 1
        
        if fac.metodo_pago == 'EFECTIVO':
            entry['ventas_efectivo'] += fac.valor_pagado
            total_efectivo_ventas += fac.valor_pagado
        elif fac.metodo_pago == 'TARJETA':
            entry['ventas_tarjeta'] += fac.valor_pagado
            total_tarjeta_ventas += fac.valor_pagado
        elif fac.metodo_pago == 'TRANSFERENCIA':
            entry['ventas_transferencia'] += fac.valor_pagado
            total_transf_ventas += fac.valor_pagado
        else:
            entry['ventas_credito'] += fac.valor_pagado
            total_credito_ventas += fac.valor_pagado
            
    total_gastos_efectivo = Decimal('0')
    total_gastos_otros = Decimal('0')
    
    for g in gastos_qs:
        g_date = g.fecha
        entry = dias_caja[g_date]
        entry['fecha'] = g_date
        entry['total_salidas'] += g.valor
        entry['num_gastos'] += 1
        
        if g.metodo_pago == 'EFECTIVO':
            entry['gastos_efectivo'] += g.valor
            total_gastos_efectivo += g.valor
        else:
            entry['gastos_otros'] += g.valor
            total_gastos_otros += g.valor
            
    # Calcular saldos y arqueo de caja
    cortes_diarios = []
    for f_date, entry in sorted(dias_caja.items(), key=lambda x: x[0], reverse=True):
        entry['saldo_caja_efectivo'] = entry['ventas_efectivo'] - entry['gastos_efectivo']
        entry['total_neto'] = entry['total_entradas'] - entry['total_salidas']
        cortes_diarios.append(entry)
        
    saldo_efectivo_en_caja = total_efectivo_ventas - total_gastos_efectivo
    cuentas_pendientes = sum((f.saldo_pendiente for f in facturas), Decimal('0'))
    
    data.update({
        'inicio': inicio,
        'fin': fin,
        'periodo': opcion,
        'cortes_diarios': cortes_diarios,
        'total_efectivo_ventas': total_efectivo_ventas,
        'total_tarjeta_ventas': total_tarjeta_ventas,
        'total_transf_ventas': total_transf_ventas,
        'total_credito_ventas': total_credito_ventas,
        'total_gastos_efectivo': total_gastos_efectivo,
        'total_gastos_otros': total_gastos_otros,
        'saldo_efectivo_en_caja': saldo_efectivo_en_caja,
        'cuentas_pendientes': cuentas_pendientes,
        'fecha_generacion': timezone.now()
    })
    return render(request, 'finanzas/caja_conciliacion.html', data)


# Mantener compatibilidad con llamadas anteriores a reportes
reportes = caja_conciliacion


