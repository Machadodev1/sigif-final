import json
import os

from decimal import Decimal
from io import BytesIO
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db import transaction
from django.core.mail import EmailMessage
from django.conf import settings
from apps.auditoria.models import Auditoria
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from apps.facturacion.models import (
    Factura,
    Cliente,
    DetalleFactura
)

from apps.productos.models import Producto

from apps.inventario.models import EntradaInventario, DetalleEntradaInventario

from core.decoradores import requerir_rol


# ============================================================
# FORMATO DE DINERO - PESOS COLOMBIANOS
# ============================================================

def formato_cop(valor):

    valor = Decimal(str(valor))

    valor = valor.quantize(
        Decimal('1')
    )

    valor_formateado = f"{valor:,.0f}".replace(",", ".")

    return f"$ {valor_formateado} COP"


# ============================================================
# LISTADO DE FACTURAS
# ============================================================

class FacturaListView(ListView):
    model = Factura
    template_name = 'facturacion/facturacion.html'
    context_object_name = 'facturas'

    def dispatch(self, request, *args, **kwargs):
        return requerir_rol(
            ["SuperAdmin", "Admin", "Empleado"]
        )(super().dispatch)(request, *args, **kwargs)

    def get_queryset(self):
        facturas = Factura.objects.select_related(
            'cliente'
        ).prefetch_related(
            'detalles__producto'
        ).order_by('-id')

        usuario = self.request.session.get("logueado", {})

        rol = usuario.get("rol")
        nombre_usuario = usuario.get("nombre")

        # SuperAdmin y Admin pueden ver TODAS las facturas
        if rol in ["SuperAdmin", "Admin"]:
            return facturas

        # Empleado solamente puede ver las facturas
        # que él mismo realizó
        if rol == "Empleado":
            return facturas.filter(
                usuario=nombre_usuario
            )

        # Si por alguna razón no tiene un rol válido,
        # no mostrar ninguna factura
        return Factura.objects.none()


# ============================================================
# DETALLE DE FACTURA
# ============================================================

class FacturaDetailView(DetailView):

    model = Factura

    template_name = 'facturacion/facturacion.html'

    context_object_name = 'factura'

    def dispatch(self, request, *args, **kwargs):

        return requerir_rol(
            ["Admin", "Empleado"]
        )(
            super().dispatch
        )(request, *args, **kwargs)


# ============================================================
# CLIENTES
# ============================================================

@requerir_rol(["SuperAdmin", "Admin", "Empleado"])
def clientes_view(request):

    clientes = Cliente.objects.all()

    return render(
        request,
        'facturacion/cliente.html',
        {
            'clientes': clientes
        }
    )


# ============================================================
# PRODUCTOS VENDIDOS
# ============================================================

@requerir_rol(["SuperAdmin", "Admin", "Empleado"])
def productos_facturacion_view(request):

    detalles = DetalleFactura.objects.select_related(
        'producto',
        'factura',
        'factura__cliente'
    ).order_by(
        '-factura__fecha'
    )

    # Agrupar los movimientos por producto
    productos = {}

    for detalle in detalles:
        producto_id = detalle.producto_id

        if producto_id not in productos:
            productos[producto_id] = {
                'producto': detalle.producto,
                'movimientos': [],
                'total_vendido': 0,
                'total_ingresos': 0,
            }

        productos[producto_id]['movimientos'].append(detalle)
        productos[producto_id]['total_vendido'] += detalle.cantidad
        productos[producto_id]['total_ingresos'] += detalle.subtotal

    productos_lista = sorted(
        productos.values(),
        key=lambda p: p['total_ingresos'],
        reverse=True
    )

    return render(
        request,
        'facturacion/productos_facturacion.html',
        {
            'productos': productos_lista,
            'detalles': detalles
        }
    )


# ============================================================
# FACTURA GENERADA
# ============================================================

@requerir_rol(["SuperAdmin", "Admin", "Empleado"])
def factura_generada(request, pk):

    factura = get_object_or_404(
        Factura,
        pk=pk
    )

    return render(
        request,
        'facturacion/factura_generada.html',
        {
            'factura': factura
        }
    )


# ============================================================
# PÁGINA DE PAGO
# ============================================================

@requerir_rol(["SuperAdmin", "Admin", "Empleado"])
def pago(request):

    clientes = Cliente.objects.all()

    return render(
        request,
        'facturacion/pago.html',
        {
            'clientes': clientes
        }
    )



@requerir_rol(["SuperAdmin", "Admin", "Empleado"])
def confirmar_venta(request):

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "message": "Método no permitido"
        }, status=405)

    try:
        data = json.loads(request.body)

        productos = data.get("productos", [])
        descuento = Decimal(str(data.get("descuento", 0)))
        metodo_pago = str(data.get("metodo_pago", "efectivo")).upper()
        if metodo_pago not in dict(Factura.METODOS_PAGO):
            metodo_pago = 'EFECTIVO'

        cliente_id = data.get("cliente_id")
        nombre = data.get("nombre", "").strip()
        correo = data.get("correo", "").strip()

        # ==========================================
        # VALIDACIONES INICIALES
        # ==========================================

        if not productos:
            return JsonResponse({
                "success": False,
                "message": "El carrito está vacío"
            })

        if not nombre:
            nombre = "Cliente general"

        # Evitar descuentos inválidos
        if descuento < 0:
            descuento = Decimal("0")

        if descuento > 100:
            descuento = Decimal("100")

        # ==========================================
        # CREAR VENTA
        # ==========================================

        with transaction.atomic():

            # --------------------------------------
            # CLIENTE
            # --------------------------------------

            if cliente_id:

                cliente = Cliente.objects.get(
                    pk=int(cliente_id)
                )

            else:

                if correo:

                    cliente, creado = Cliente.objects.get_or_create(
                        correo=correo,
                        defaults={
                            "nombre": nombre
                        }
                    )

                else:

                    cliente = Cliente.objects.create(
                        nombre=nombre,
                        correo=""
                    )

            # --------------------------------------
            # PRODUCTOS
            # --------------------------------------

            total = Decimal("0.00")

            productos_validos = []

            for item in productos:

                producto = Producto.objects.get(
                    id=item["id"]
                )

                cantidad = int(
                    item["cantidad"]
                )

                # Validar cantidad
                if cantidad <= 0:

                    return JsonResponse({
                        "success": False,
                        "message": (
                            f"Cantidad inválida para "
                            f"{producto.nombre}"
                        )
                    })

                # Validar stock
                if cantidad > producto.stock:

                    return JsonResponse({
                        "success": False,
                        "message": (
                            f"No hay suficiente stock de "
                            f"{producto.nombre}. "
                            f"Stock disponible: "
                            f"{producto.stock}"
                        )
                    })

                # Precio actual del producto
                precio = Decimal(
                    str(producto.precio)
                )

                subtotal = precio * cantidad

                total += subtotal

                productos_validos.append({
                    "producto": producto,
                    "cantidad": cantidad,
                    "precio": precio,
                    "subtotal": subtotal
                })

            # --------------------------------------
            # DESCUENTO
            # --------------------------------------

            valor_descuento = (
                total *
                descuento /
                Decimal("100")
            )

            total_final = total - valor_descuento

            # --------------------------------------
            # USUARIO LOGUEADO
            # --------------------------------------

            usuario = request.session.get(
                "logueado",
                {}
            ).get(
                "nombre",
                "Usuario"
            )

            # --------------------------------------
            # CREAR FACTURA
            # --------------------------------------

            factura = Factura.objects.create(
                cliente=cliente,
                usuario=usuario,
                total=total_final,
                descuento=valor_descuento,
                metodo_pago=metodo_pago,
                valor_pagado=total_final if metodo_pago != 'CREDITO' else Decimal('0'),
            )
            Auditoria.objects.create(
                usuario=request.session["logueado"]["nombre"],
                accion=f"CREÓ FACTURA #{factura.id} - CLIENTE: {cliente.nombre} - TOTAL: {formato_cop(total_final)}",
                modulo="FACTURACION"
            )
            # --------------------------------------
            # DETALLES + INVENTARIO
            # --------------------------------------

            for item in productos_validos:

                producto = item["producto"]

                DetalleFactura.objects.create(
                    factura=factura,
                    producto=producto,
                    cantidad=item["cantidad"],
                    precio=item["precio"],
                    subtotal=item["subtotal"]
                )

                # Descontar inventario
                producto.stock -= item["cantidad"]

                producto.save(
                    update_fields=["stock"]
                )

        # ==========================================
        # ENVÍO DEL CORREO EN SEGUNDO PLANO
        # ==========================================

        if factura.cliente.correo:

            import threading

            def enviar_correo():

                try:

                    enviar_factura_correo(factura)

                    print(
                        f"Factura #{factura.id} "
                        f"enviada correctamente a "
                        f"{factura.cliente.correo}"
                    )

                except Exception as e:

                    print(
                        f"Error enviando factura "
                        f"#{factura.id}: {e}"
                    )

            hilo = threading.Thread(
                target=enviar_correo,
                daemon=True
            )

            hilo.start()

        # ==========================================
        # RESPUESTA INMEDIATA
        # ==========================================

        return JsonResponse({
            "success": True,
            "message": (
                "Venta realizada correctamente. "
                "La factura fue registrada y "
                "se está enviando al correo del cliente."
            ),
            "factura_id": factura.id
        })

    # ==============================================
    # ERRORES
    # ==============================================

    except Cliente.DoesNotExist:

        return JsonResponse({
            "success": False,
            "message": "El cliente seleccionado no existe"
        }, status=400)

    except Producto.DoesNotExist:

        return JsonResponse({
            "success": False,
            "message": "Uno de los productos ya no existe"
        }, status=400)

    except ValueError:

        return JsonResponse({
            "success": False,
            "message": "Los datos enviados no son válidos"
        }, status=400)

    except Exception as e:

        print(
            f"Error confirmando venta: {e}"
        )

        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=400)

# ============================================================
# GENERAR PDF DE FACTURA
# ============================================================

def generar_pdf_factura(factura):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=35,
        bottomMargin=35
    )

    elementos = []

    estilos = getSampleStyleSheet()

    # ==========================================
    # COLORES SIGIF
    # ==========================================

    azul_sigif = colors.HexColor("#1E2A44")
    azul_tabla = colors.HexColor("#2F70B7")
    verde_sigif = colors.HexColor("#05A77B")
    gris_fondo = colors.HexColor("#F5F7FA")
    gris_borde = colors.HexColor("#D9E0E8")

    # ==========================================
    # LOGO
    # ==========================================

    ruta_logo = os.path.join(
        settings.BASE_DIR,
        "static",
        "img",
        "logo123.png"
    )

    if os.path.exists(ruta_logo):

        logo = Image(
            ruta_logo,
            width=90,
            height=45
        )

        # Alinear a la izquierda
        logo.hAlign = "LEFT"

        # Crear espacio alrededor del logo
        tabla_logo = Table(
            [[logo]],
            colWidths=[120],
            rowHeights=[60]
        )

        tabla_logo.setStyle(
            TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ])
        )

        elementos.append(tabla_logo)

        elementos.append(
            Spacer(1, 8)
        )

    # ==========================================
    # TÍTULO
    # ==========================================

    estilo_titulo = ParagraphStyle(
        "TituloFactura",
        parent=estilos["Heading1"],
        fontSize=16,
        spaceAfter=12,
        textColor=azul_sigif
    )

    elementos.append(
        Paragraph(
            f"Factura de Venta N° {factura.id}",
            estilo_titulo
        )
    )

    # ==========================================
    # INFORMACIÓN DEL CLIENTE
    # ==========================================

    # Convertir la fecha de UTC a la zona horaria
    # configurada en Django
    fecha_local = timezone.localtime(factura.fecha)

    elementos.append(
        Paragraph(
            f"<b>Cliente:</b> {factura.cliente.nombre}",
            estilos["Normal"]
        )
    )

    elementos.append(
        Paragraph(
            f"<b>Correo:</b> {factura.cliente.correo}",
            estilos["Normal"]
        )
    )

    elementos.append(
        Paragraph(
            f"<b>Fecha:</b> {fecha_local.strftime('%d/%m/%Y %H:%M')}",
            estilos["Normal"]
        )
    )

    elementos.append(
        Paragraph(
            f"<b>Atendido por:</b> {factura.usuario}",
            estilos["Normal"]
        )
    )

    elementos.append(
        Spacer(1, 15)
    )

    # ==========================================
    # TABLA DE PRODUCTOS
    # ==========================================

    data = [
        [
            "Producto",
            "Cantidad",
            "Precio Unit.",
            "Subtotal"
        ]
    ]

    for detalle in factura.detalles.all():

        precio = Decimal(str(detalle.precio))
        subtotal = Decimal(str(detalle.subtotal))

        data.append([
            detalle.producto.nombre,
            str(detalle.cantidad),
            f"$ {precio:,.0f} COP",
            f"$ {subtotal:,.0f} COP"
        ])

    # ==========================================
    # TOTALES DE RESUMEN
    # ==========================================

    descuento = Decimal(str(factura.descuento or 0))
    total = Decimal(str(factura.total))

    subtotal_bruto = total + descuento
    base_gravable = factura.base_gravable
    iva = factura.iva

    data.append([
        "",
        "",
        "Subtotal Bruto:",
        f"$ {subtotal_bruto:,.0f} COP"
    ])

    data.append([
        "",
        "",
        "Descuento:",
        f"$ {descuento:,.0f} COP"
    ])

    data.append([
        "",
        "",
        "Base Gravable:",
        f"$ {base_gravable:,.0f} COP"
    ])

    data.append([
        "",
        "",
        "IVA (19%):",
        f"$ {iva:,.0f} COP"
    ])

    data.append([
        "",
        "",
        "TOTAL:",
        f"$ {total:,.0f} COP"
    ])

    # ==========================================
    # TABLA
    # ==========================================

    tabla = Table(
        data,
        colWidths=[
            200,
            70,
            100,
            100
        ]
    )

    tabla.setStyle(
        TableStyle([

            # Encabezado
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                azul_tabla
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, 0),
                10
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, 0),
                8
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, 0),
                8
            ),

            # Cuerpo
            (
                "BACKGROUND",
                (0, 1),
                (-1, -1),
                gris_fondo
            ),

            (
                "GRID",
                (0, 0),
                (-1, -6),
                0.5,
                gris_borde
            ),

            (
                "ALIGN",
                (1, 0),
                (-1, -1),
                "CENTER"
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            # Filas de Resumen (Subtotal, Descuento, Base Gravable, IVA)
            (
                "TEXTCOLOR",
                (2, -5),
                (-1, -2),
                azul_sigif
            ),

            (
                "FONTNAME",
                (2, -5),
                (-1, -2),
                "Helvetica-Bold"
            ),

            (
                "TEXTCOLOR",
                (2, -4), # Descuento en color azul_tabla
                (-1, -4),
                azul_tabla
            ),

            # Total
            (
                "BACKGROUND",
                (2, -1),
                (-1, -1),
                verde_sigif
            ),

            (
                "TEXTCOLOR",
                (2, -1),
                (-1, -1),
                colors.white
            ),

            (
                "FONTNAME",
                (2, -1),
                (-1, -1),
                "Helvetica-Bold"
            ),

            (
                "FONTSIZE",
                (2, -1),
                (-1, -1),
                11
            ),

            (
                "TOPPADDING",
                (2, -1),
                (-1, -1),
                8
            ),

            (
                "BOTTOMPADDING",
                (2, -1),
                (-1, -1),
                8
            ),
        ])
    )

    elementos.append(tabla)

    elementos.append(
        Spacer(1, 35)
    )

    # ==========================================
    # PIE DE FACTURA
    # ==========================================

    estilo_pie = ParagraphStyle(
        "PieFactura",
        parent=estilos["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#718096"),
        alignment=1
    )

    elementos.append(
        Paragraph(
            "Gracias por tu compra.",
            estilo_pie
        )
    )

    elementos.append(
        Paragraph(
            "SIGIF - Sistema Integral de Gestión de Inventarios y Facturación",
            estilo_pie
        )
    )

    # ==========================================
    # GENERAR PDF
    # ==========================================

    doc.build(elementos)

    buffer.seek(0)

    return buffer.getvalue()

# ============================================================
# ENVIAR FACTURA POR CORREO
# ============================================================

def enviar_factura_correo(factura):

    pdf = generar_pdf_factura(
        factura
    )

    email = EmailMessage(

        subject=(
            f'Factura #{factura.id} - SIGIF'
        ),

        body=(
            f'Hola {factura.cliente.nombre},\n\n'

            f'Adjunto encontrarás tu factura '
            f'#{factura.id} generada en SIGIF.\n\n'

            f'Total: '
            f'{formato_cop(factura.total)}\n\n'

            f'Gracias por tu compra.\n\n'

            f'SIGIF - Sistema Integral de '
            f'Gestión de Inventarios y Facturación'
        ),

        from_email=settings.DEFAULT_FROM_EMAIL,

        to=[
            factura.cliente.correo
        ],
    )

    # ========================================================
    # ADJUNTAR PDF
    # ========================================================

    email.attach(
        f'factura_{factura.id}.pdf',
        pdf,
        'application/pdf'
    )

    # ========================================================
    # ENVIAR
    # ========================================================

    email.send(
        fail_silently=False
    )


# ============================================================
# EXPORTAR FACTURA PDF
# ============================================================

@requerir_rol(
    ["SuperAdmin", "Admin", "Empleado"]
)
def exportar_factura_pdf(request, pk):

    factura = get_object_or_404(
        Factura,
        pk=pk
    )

    pdf = generar_pdf_factura(
        factura
    )

    response = HttpResponse(
        pdf,
        content_type='application/pdf'
    )

    response['Content-Disposition'] = (
        f'attachment; '
        f'filename="factura_{factura.id}.pdf"'
    )

    return response

# ============================================================
# FACTURAS DE ENTRADA (INGRESOS AL INVENTARIO)
# ============================================================

@requerir_rol(["SuperAdmin", "Admin", "Empleado"])
def facturas_entrada_view(request):
    entradas = EntradaInventario.objects.prefetch_related(
        'detalles__producto'
    ).order_by('-fecha')

    return render(
        request,
        'facturacion/facturas_entrada.html',
        {'entradas': entradas}
    )


@requerir_rol(["SuperAdmin", "Admin", "Empleado"])
def registro_entradas_view(request):
    """Registro linea por linea de todos los productos ingresados."""
    detalles = DetalleEntradaInventario.objects.select_related(
        'producto',
        'entrada'
    ).order_by('-entrada__fecha')

    return render(
        request,
        'facturacion/registro_entradas.html',
        {'detalles': detalles}
    )
