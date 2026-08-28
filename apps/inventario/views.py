from django.shortcuts import render, get_object_or_404
from apps.productos.models import Producto

from apps.configuracion.models import EmpresaConfig
from core.decoradores import requerir_rol
from apps.facturacion.models import DetalleFactura



@requerir_rol(["Admin", "Empleado"])
def inv_configuracion(request):
    config = EmpresaConfig.objects.all()
    print(config)
    print (type(config))
    print("123")
    return render(request, 'configuracion/configuracion.html', {'config': config})



@requerir_rol(["SuperAdmin","Admin", "Empleado"])
def inventario(request):

    productos = Producto.objects.filter(activo=True).order_by('-stock', 'nombre')

    contexto = {
        'producto': productos
    }

    return render(request, "inventario/inventario.html", contexto)

@requerir_rol(["SuperAdmin","Admin", "Empleado"])
def inv_historial(request):
    movimientos = Producto.objects.all()

    for movimiento in movimientos:
        movimiento.valor_total = movimiento.precio * movimiento.stock

    salidas = DetalleFactura.objects.select_related(
        'producto',
        'factura',
        'factura__cliente'
    ).order_by('-factura__fecha')[:20]

    return render(
        request,
        'inventario/inv_historial.html',
        {
            'movimientos': movimientos,
            'salidas': salidas
        }
    )

@requerir_rol(["SuperAdmin","Admin", "Empleado"])
def inv_control(request):
    producto = Producto.objects.all()

    contexto = {
        'producto': producto
    }

    return render(request, "inventario/inv_control.html", contexto)

# ============================================================
# INGRESOS AL INVENTARIO (ENTRADAS)
# ============================================================

import json
from decimal import Decimal, InvalidOperation
from io import BytesIO

from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.views.decorators.http import require_POST

from apps.inventario.models import EntradaInventario, DetalleEntradaInventario
from apps.auditoria.models import Auditoria


@requerir_rol(["SuperAdmin", "Admin", "Empleado"])
def inv_ingresos(request):
    productos = Producto.objects.filter(activo=True).order_by('nombre')
    entradas = EntradaInventario.objects.prefetch_related('detalles__producto')

    productos_serializados = [
        {'id': p.id, 'nombre': p.nombre, 'stock': p.stock, 'precio': str(p.precio)}
        for p in productos
    ]

    contexto = {
        'productos': productos,
        'entradas': entradas,
        'productos_serializados': json.dumps(productos_serializados, ensure_ascii=False),
    }
    return render(request, 'inventario/inv_ingresos.html', contexto)


@require_POST
@requerir_rol(["SuperAdmin", "Admin", "Empleado"])
def registrar_entrada(request):
    """Registra una entrada al inventario.

    Espera JSON:
    {
        "proveedor": "...",
        "documento": "...",           # opcional
        "observaciones": "...",       # opcional
        "items": [
            {"producto_id": 1, "cantidad": 5},                        # existente
            {"nombre": "...", "categoria": "...", "precio": 1000,
             "cantidad": 5, "descripcion": "..."}                     # nuevo
        ]
    }
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({
            "success": False,
            "message": "Los datos enviados no son válidos."
        }, status=400)

    proveedor = str(data.get("proveedor", "")).strip()
    documento = str(data.get("documento", "")).strip() or None
    observaciones = str(data.get("observaciones", "")).strip() or None
    items = data.get("items", [])

    # ---------------- VALIDACIONES ----------------
    errores = []

    if not proveedor:
        errores.append("El proveedor es obligatorio.")
    elif len(proveedor) > 150:
        errores.append("El nombre del proveedor es demasiado largo.")

    if not items or not isinstance(items, list):
        errores.append("Debes agregar al menos un producto a la entrada.")

    items_validos = []

    for idx, item in enumerate(items, start=1):
        producto_id = item.get("producto_id")
        nombre = str(item.get("nombre", "")).strip()
        categoria = str(item.get("categoria", "")).strip()
        descripcion = str(item.get("descripcion", "")).strip() or None
        activo = bool(item.get("activo", True))

        try:
            precio_venta = Decimal(str(item.get("precio_venta", 0) or 0))
        except (InvalidOperation, TypeError, ValueError):
            errores.append(f"Producto {idx}: el precio de venta no es válido.")
            continue

        try:
            cantidad = int(item.get("cantidad", 0))
        except (TypeError, ValueError):
            errores.append(f"Producto {idx}: la cantidad debe ser un número entero.")
            continue

        try:
            precio = Decimal(str(item.get("precio", 0)))
        except (InvalidOperation, TypeError, ValueError):
            errores.append(f"Producto {idx}: el precio no es válido.")
            continue

        if cantidad <= 0:
            errores.append(f"Producto {idx}: la cantidad debe ser mayor a cero.")
            continue

        if cantidad > 100000:
            errores.append(f"Producto {idx}: la cantidad es demasiado grande.")
            continue

        if precio <= 0:
            errores.append(f"Producto {idx}: el precio debe ser mayor a cero.")
            continue

        if producto_id:
            producto = Producto.objects.filter(id=producto_id, activo=True).first()
            if not producto:
                errores.append(f"Producto {idx}: el producto seleccionado no existe.")
                continue
        else:
            if not nombre:
                errores.append(f"Producto {idx}: el nombre es obligatorio para un producto nuevo.")
                continue
            if len(nombre) > 100:
                errores.append(f"Producto {idx}: el nombre es demasiado largo.")
                continue
            if not categoria:
                errores.append(f"Producto {idx}: la categoría es obligatoria para un producto nuevo.")
                continue

            if precio_venta <= 0:
                errores.append(f"Producto {idx}: el precio de venta debe ser mayor a cero.")
                continue

            producto = Producto.objects.filter(
                nombre__iexact=nombre, activo=True
            ).first()
            if producto:
                errores.append(
                    f"Producto {idx}: ya existe un producto llamado '{nombre}'. "
                    "Selecciónalo de la lista en lugar de crearlo de nuevo."
                )
                continue

            producto = Producto(
                nombre=nombre,
                categoria=categoria,
                descripcion=descripcion,
                precio=int(precio_venta),
                stock=0,
                activo=activo,
            )

        subtotal = precio * cantidad
        items_validos.append({
            "producto": producto,
            "cantidad": cantidad,
            "precio": precio,
            "subtotal": subtotal,
        })

    if errores:
        return JsonResponse({
            "success": False,
            "message": " ".join(errores)
        }, status=400)

    # ---------------- REGISTRO ----------------
    try:
        with transaction.atomic():
            total = sum(i["subtotal"] for i in items_validos)

            usuario = request.session.get("logueado", {}).get("nombre", "Usuario")

            entrada = EntradaInventario.objects.create(
                proveedor=proveedor,
                documento=documento,
                usuario=usuario,
                observaciones=observaciones,
                total=total,
            )

            for item in items_validos:
                producto = item["producto"]
                producto.save()  # guarda el producto nuevo si aplica

                DetalleEntradaInventario.objects.create(
                    entrada=entrada,
                    producto=producto,
                    cantidad=item["cantidad"],
                    precio=item["precio"],
                    subtotal=item["subtotal"],
                )

                # Aumentar stock
                producto.stock += item["cantidad"]
                producto.save(update_fields=["stock"])

            Auditoria.objects.create(
                usuario=usuario,
                accion=f"REGISTRO UNA ENTRADA AL INVENTARIO {entrada.numero_factura()} (proveedor: {proveedor})",
                modulo="INVENTARIO"
            )

        return JsonResponse({
            "success": True,
            "message": f"Entrada {entrada.numero_factura()} registrada correctamente. Stock actualizado.",
            "entrada_id": entrada.id,
            "pdf_url": f"/inventario/entrada/pdf/{entrada.id}/",
        })

    except Exception as e:
        print(f"Error registrando entrada: {e}")
        return JsonResponse({
            "success": False,
            "message": "Ocurrió un error al registrar la entrada."
        }, status=500)


# ============================================================
# PDF DE FACTURA DE ENTRADA
# ============================================================

def generar_pdf_entrada(entrada):

    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    import os
    from django.conf import settings

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=35, bottomMargin=35
    )
    elementos = []
    estilos = getSampleStyleSheet()

    azul_sigif = colors.HexColor("#1E2A44")
    azul_tabla = colors.HexColor("#2F70B7")
    verde_sigif = colors.HexColor("#05A77B")
    gris_fondo = colors.HexColor("#F5F7FA")
    gris_borde = colors.HexColor("#D9E0E8")

    ruta_logo = os.path.join(settings.BASE_DIR, "static", "img", "logo123.png")
    if os.path.exists(ruta_logo):
        logo = Image(ruta_logo, width=90, height=45)
        logo.hAlign = "LEFT"
        tabla_logo = Table([[logo]], colWidths=[120], rowHeights=[60])
        tabla_logo.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elementos.append(tabla_logo)
        elementos.append(Spacer(1, 8))

    estilo_titulo = ParagraphStyle(
        "TituloEntrada", parent=estilos["Heading1"],
        fontSize=16, spaceAfter=12, textColor=azul_sigif
    )
    elementos.append(Paragraph(f"Factura de Entrada {entrada.numero_factura()}", estilo_titulo))

    fecha_local = timezone.localtime(entrada.fecha)
    elementos.append(Paragraph(f"<b>Proveedor:</b> {entrada.proveedor}", estilos["Normal"]))
    if entrada.documento:
        elementos.append(Paragraph(f"<b>Documento:</b> {entrada.documento}", estilos["Normal"]))
    elementos.append(Paragraph(f"<b>Fecha:</b> {fecha_local.strftime('%d/%m/%Y %H:%M')}", estilos["Normal"]))
    elementos.append(Paragraph(f"<b>Registrada por:</b> {entrada.usuario}", estilos["Normal"]))
    if entrada.observaciones:
        elementos.append(Paragraph(f"<b>Observaciones:</b> {entrada.observaciones}", estilos["Normal"]))
    elementos.append(Spacer(1, 15))

    data = [["Producto", "Cantidad", "Precio Unit.", "Subtotal"]]
    for detalle in entrada.detalles.all():
        precio = Decimal(str(detalle.precio))
        subtotal = Decimal(str(detalle.subtotal))
        data.append([
            detalle.producto.nombre,
            str(detalle.cantidad),
            f"$ {precio:,.0f} COP",
            f"$ {subtotal:,.0f} COP",
        ])

    total = Decimal(str(entrada.total))
    data.append(["", "", "TOTAL:", f"$ {total:,.0f} COP"])

    tabla = Table(data, colWidths=[200, 70, 100, 100])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), azul_tabla),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), gris_fondo),
        ("GRID", (0, 0), (-1, -1), 0.5, gris_borde),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (2, -1), (-1, -1), verde_sigif),
        ("TEXTCOLOR", (2, -1), (-1, -1), colors.white),
        ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (2, -1), (-1, -1), 11),
        ("TOPPADDING", (2, -1), (-1, -1), 8),
        ("BOTTOMPADDING", (2, -1), (-1, -1), 8),
    ]))
    elementos.append(tabla)
    elementos.append(Spacer(1, 35))

    estilo_pie = ParagraphStyle(
        "PieEntrada", parent=estilos["Normal"], fontSize=9,
        textColor=colors.HexColor("#718096"), alignment=1
    )
    elementos.append(Paragraph("Documento interno de ingreso de mercancía.", estilo_pie))
    elementos.append(Paragraph("SIGIF - Sistema Integral de Gestión de Inventarios y Facturación", estilo_pie))

    doc.build(elementos)
    buffer.seek(0)
    return buffer.getvalue()


@requerir_rol(["SuperAdmin", "Admin", "Empleado"])
def exportar_entrada_pdf(request, pk):
    entrada = get_object_or_404(EntradaInventario, pk=pk)
    pdf = generar_pdf_entrada(entrada)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{entrada.numero_factura()}.pdf"'
    return response
