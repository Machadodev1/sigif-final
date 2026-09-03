from collections import defaultdict
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib import messages
from django.db.models import Sum
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
    inicio, fin, opcion = _periodo(request)
    data = _resumen(inicio, fin)
    data.update({'inicio': inicio, 'fin': fin, 'periodo': opcion})
    # Facturas vigentes son ventas cobradas al confirmarse; no se crean ingresos paralelos.
    data['gastos_categoria'] = list(data['gastos'].values('categoria').annotate(total=Sum('valor')).order_by('-total'))
    return render(request, 'finanzas/dashboard.html', data)


@requerir_rol(['SuperAdmin', 'Admin', 'Empleado'])
def movimientos(request, tipo='gastos'):
    inicio, fin, opcion = _periodo(request)
    gastos = Gasto.objects.filter(fecha__range=(inicio, fin))
    for campo in ('categoria', 'metodo_pago'):
        if request.GET.get(campo): gastos = gastos.filter(**{campo: request.GET[campo]})
    data = _resumen(inicio, fin)
    data.update({'inicio': inicio, 'fin': fin, 'periodo': opcion, 'gastos': gastos, 'categorias': Gasto.CATEGORIAS, 'metodos': Gasto.METODOS_PAGO, 'tipo': tipo})
    return render(request, 'finanzas/movimientos.html', data)


@requerir_rol_accion(['SuperAdmin', 'Admin'], 'finanzas:movimientos')
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
            messages.success(request, 'Gasto guardado correctamente.')
        except (KeyError, ValueError, ArithmeticError): messages.error(request, 'Verifica los datos del gasto.')
    return redirect('finanzas:gastos')


@requerir_rol_accion(['SuperAdmin', 'Admin'], 'finanzas:gastos')
def eliminar_gasto(request, pk):
    if request.method == 'POST':
        gasto = get_object_or_404(Gasto, pk=pk); nombre = gasto.concepto; gasto.delete()
        messages.success(request, f'Gasto “{nombre}” eliminado.')
    return redirect('finanzas:gastos')


@requerir_rol(['SuperAdmin', 'Admin', 'Empleado'])
def rentabilidad(request):
    inicio, fin, opcion = _periodo(request); data = _resumen(inicio, fin)
    productos = data['productos']
    data.update({'inicio': inicio, 'fin': fin, 'periodo': opcion, 'productos_rentabilidad': sorted(productos, key=lambda x: x['ganancia'], reverse=True), 'mas_vendidos': sorted(productos, key=lambda x: x['cantidad'], reverse=True)[:5], 'mayor_margen': sorted(productos, key=lambda x: x['margen'], reverse=True)[:5]})
    return render(request, 'finanzas/rentabilidad.html', data)


@requerir_rol(['SuperAdmin', 'Admin', 'Empleado'])
def reportes(request):
    inicio, fin, opcion = _periodo(request); data = _resumen(inicio, fin)
    data.update({'inicio': inicio, 'fin': fin, 'periodo': opcion, 'productos_rentabilidad': sorted(data['productos'], key=lambda x: x['ganancia'], reverse=True)[:5], 'gastos_categoria': data['gastos'].values('categoria').annotate(total=Sum('valor')).order_by('-total')})
    return render(request, 'finanzas/reportes.html', data)
