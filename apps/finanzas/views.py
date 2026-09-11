from collections import defaultdict
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib import messages
from django.db.models import Sum, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.auditoria.models import Auditoria
from apps.configuracion.models import EmpresaConfig
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
    """Costo unitario desde inventario; usa el costo conocido más reciente."""
    # Precarga compras por producto para evitar N+1
    producto_ids = {d.producto_id for d in detalles}
    compras_por_producto = defaultdict(list)
    for c in DetalleEntradaInventario.objects.filter(producto_id__in=producto_ids).select_related('entrada').order_by('producto_id', '-entrada__fecha', '-id'):
        compras_por_producto[c.producto_id].append(c)

    costo, productos = Decimal('0'), defaultdict(lambda: {'producto': None, 'cantidad': 0, 'ingresos': Decimal('0'), 'costos': Decimal('0')})
    for detalle in detalles:
        compras = compras_por_producto.get(detalle.producto_id, [])
        compra = None
        for comp in compras:
            if comp.entrada.fecha <= detalle.factura.fecha:
                compra = comp
                break
        if not compra and compras:
            compra = compras[0]
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
    ingresos = facturas.aggregate(v=Sum('valor_pagado'))['v'] or Decimal('0')
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


@requerir_rol(['SuperAdmin', 'Admin'])
def dashboard(request):
    """1. Estado de resultados (P&G): Pérdidas y ganancias consolidado."""
    inicio, fin, opcion = _periodo(request)
    data = _resumen(inicio, fin)
    data.update({'inicio': inicio, 'fin': fin, 'periodo': opcion})
    data['gastos_categoria'] = list(data['gastos'].values('categoria').annotate(total=Sum('valor')).order_by('-total'))
    return render(request, 'finanzas/dashboard.html', data)


@requerir_rol(['SuperAdmin', 'Admin'])
def ventas_categoria(request):
    """2. Reporte de ventas por categoría: Identifica qué categoría genera más dinero y rentabilidad."""
    inicio, fin, opcion = _periodo(request)
    data = _resumen(inicio, fin)

    detalles = data['detalles']
    # Un solo recorrido para asociar facturas y SKUs únicos a cada categoría.
    cat_facturas = defaultdict(set)
    cat_productos = defaultdict(set)
    for det in detalles:
        cat = det.producto.categoria or 'Repuestos Generales'
        cat_facturas[cat].add(det.factura_id)
        cat_productos[cat].add(det.producto.nombre)

    # Los agregados por producto ya fueron calculados en _resumen() con la
    # misma lógica de costos; aquí solo se agrupan por categoría (sin N+1).
    cat_map = defaultdict(lambda: {
        'categoria': '', 'ingresos': Decimal('0'), 'costos': Decimal('0'),
        'unidades': 0
    })
    for item in data['productos']:
        producto = item['producto']
        if not producto:
            continue
        cat = producto.categoria or 'Repuestos Generales'
        entry = cat_map[cat]
        entry['categoria'] = cat
        entry['ingresos'] += item['ingresos']
        entry['costos'] += item['costos']
        entry['unidades'] += item['cantidad']

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
            'transacciones': len(cat_facturas.get(cat, ())),
            'total_skus': len(cat_productos.get(cat, ()))
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


@requerir_rol(['SuperAdmin', 'Admin'])
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

    # SEGURIDAD: solo se aceptan POST; se valida que no haya CSRF.
    if request.method != 'POST':
        return redirect('finanzas:gastos')

    try:
        def _limpiar_texto(valor, maximo):
            valor = (valor or '').strip()
            # SEGURIDAD: elimina marcado HTML/JS antes de guardar.
            valor = valor.replace('<', '').replace('>', '')
            return valor[:maximo]

        concepto = _limpiar_texto(request.POST.get('concepto'), 150)
        proveedor = _limpiar_texto(request.POST.get('proveedor'), 150)
        descripcion = _limpiar_texto(request.POST.get('descripcion'), 2000)
        categoria = (request.POST.get('categoria') or '').strip()
        metodo_pago = (request.POST.get('metodo_pago') or '').strip()
        valor = Decimal(request.POST['valor'])

        fecha_raw = (request.POST.get('fecha') or '').strip()
        try:
            fecha = datetime.strptime(fecha_raw, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError('fecha inválida')

        # Validaciones mínimas de negocio para evitar datos corruptos.
        if not concepto:
            raise ValueError('concepto vacío')
        if len(concepto) < 4:
            raise ValueError('concepto demasiado corto')
        # evita "a", "aaa", etc.
        if len(set(concepto.lower())) < 2 and len(concepto) < 5:
            raise ValueError('concepto no válido')
        if proveedor and len(proveedor) < 3:
            raise ValueError('proveedor demasiado corto')
        if valor <= 0:
            raise ValueError('valor inválido')
        # max_digits=12 con 2 decimales => hasta 99.999.999.999,99 COP.
        if valor > Decimal('99999999999.99'):
            raise ValueError('valor demasiado grande')
        categorias_validas = [c[0] for c in Gasto.CATEGORIAS]
        metodos_validos = [m[0] for m in Gasto.METODOS_PAGO]
        if categoria not in categorias_validas:
            categoria = categorias_validas[0] if categorias_validas else ''
        if metodo_pago not in metodos_validos:
            metodo_pago = metodos_validos[0] if metodos_validos else ''

        campos = {
            'concepto': concepto,
            'categoria': categoria,
            'fecha': fecha,
            'metodo_pago': metodo_pago,
            'proveedor': proveedor,
            'descripcion': descripcion,
            'valor': valor,
            'usuario': request.session.get('logueado', {}).get('nombre', 'Usuario'),
        }
        if gasto:
            for key, value in campos.items():
                setattr(gasto, key, value)
            gasto.save();
            accion = 'ACTUALIZÓ'
        else:
            gasto = Gasto.objects.create(**campos)
            accion = 'REGISTRÓ'
        Auditoria.objects.create(usuario=campos['usuario'], accion=f'{accion} GASTO: {gasto.concepto}', modulo='FINANZAS')
        messages.success(request, 'Gasto operativo registrado correctamente.', extra_tags='module-finanzas')
    except (KeyError, ValueError, ArithmeticError):
        messages.error(request, 'Verifica los datos del gasto ingresado.', extra_tags='module-finanzas')
    return redirect('finanzas:gastos')


@requerir_rol_accion(['SuperAdmin', 'Admin'], 'finanzas:gastos')
def eliminar_gasto(request, pk):
    if request.method == 'POST':
        gasto = get_object_or_404(Gasto, pk=pk)
        nombre = gasto.concepto
        gasto.delete()
        messages.success(request, f'Gasto “{nombre}” eliminado correctamente.', extra_tags='module-finanzas')
    return redirect('finanzas:gastos')


@requerir_rol(['SuperAdmin', 'Admin'])
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


@requerir_rol(['SuperAdmin', 'Admin'])
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
        'fecha_generacion': timezone.now(),
        'config_empresa': EmpresaConfig.objects.first() or EmpresaConfig(),
    })
    return render(request, 'finanzas/caja_conciliacion.html', data)


# Mantener compatibilidad con llamadas anteriores a reportes
reportes = caja_conciliacion


