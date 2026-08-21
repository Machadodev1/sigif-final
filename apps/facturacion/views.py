import json
from decimal import Decimal
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from apps.facturacion.models import Factura, Cliente, DetalleFactura
from apps.productos.models import Producto
from core.decoradores import requerir_rol


class FacturaListView(ListView):
    model = Factura
    template_name = 'facturacion/facturacion.html'
    context_object_name = 'facturas'

    def dispatch(self, request, *args, **kwargs):
        return requerir_rol(["SuperAdmin","Admin", "Empleado"])(super().dispatch)(request, *args, **kwargs)


class FacturaDetailView(DetailView):
    model = Factura
    template_name = 'facturacion/facturacion.html'
    context_object_name = 'factura'

    def dispatch(self, request, *args, **kwargs):
        return requerir_rol(["Admin", "Empleado"])(super().dispatch)(request, *args, **kwargs)


@requerir_rol(["SuperAdmin","Admin", "Empleado"])
def clientes_view(request):
    clientes = Cliente.objects.all()
    return render(request, 'facturacion/cliente.html', {'clientes': clientes})


@requerir_rol(["SuperAdmin","Admin", "Empleado"])
def productos_facturacion_view(request):
    detalles = DetalleFactura.objects.select_related(
        'producto',
        'factura',
        'factura__cliente'
    ).order_by('-factura__fecha')

    return render(
        request,
        'facturacion/productos_facturacion.html',
        {'detalles': detalles}
    )


@requerir_rol(["SuperAdmin","Admin", "Empleado"])
def factura_generada(request, pk):
    factura = get_object_or_404(Factura, pk=pk)
    return render(
        request,
        'facturacion/factura_generada.html',
        {'factura': factura}
    )


@requerir_rol(["SuperAdmin","Admin", "Empleado"])
def pago(request):
    return render(request, 'facturacion/pago.html')


@requerir_rol(["SuperAdmin","Admin", "Empleado"])
def confirmar_venta(request):
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Método no permitido'
        }, status=405)

    try:
        data = json.loads(request.body)

        productos = data.get('productos', [])

        descuento = Decimal(
            str(data.get('descuento', 0))
        )

        nombre = data.get('nombre', '').strip()
        correo = data.get('correo', '').strip()

        if not productos:
            return JsonResponse({
                'success': False,
                'message': 'El carrito está vacío'
            })

        if not nombre:
            nombre = 'Cliente general'

        if not correo:
            correo = 'cliente@general.com'

        with transaction.atomic():

            cliente, creado = Cliente.objects.get_or_create(
                correo=correo,
                defaults={
                    'nombre': nombre
                }
            )

            total = Decimal('0.00')
            productos_validos = []

            for item in productos:

                producto = Producto.objects.get(
                    id=item['id']
                )

                cantidad = int(
                    item['cantidad']
                )

                if cantidad <= 0:
                    return JsonResponse({
                        'success': False,
                        'message': f'Cantidad inválida para {producto.nombre}'
                    })

                if cantidad > producto.stock:
                    return JsonResponse({
                        'success': False,
                        'message': f'No hay suficiente stock de {producto.nombre}. Stock disponible: {producto.stock}'
                    })

                precio = Decimal(
                    str(producto.precio)
                )

                subtotal = precio * cantidad

                total += subtotal

                productos_validos.append({
                    'producto': producto,
                    'cantidad': cantidad,
                    'precio': precio,
                    'subtotal': subtotal
                })

            valor_descuento = (
                total *
                descuento /
                Decimal('100')
            )

            total_final = total - valor_descuento

            usuario = request.session.get(
                "logueado",
                {}
            ).get(
                "nombre",
                "Usuario"
            )

            factura = Factura.objects.create(
                cliente=cliente,
                usuario=usuario,
                total=total_final,
                descuento=valor_descuento
            )

            for item in productos_validos:

                producto = item['producto']

                DetalleFactura.objects.create(
                    factura=factura,
                    producto=producto,
                    cantidad=item['cantidad'],
                    precio=item['precio'],
                    subtotal=item['subtotal']
                )

                producto.stock -= item['cantidad']
                producto.save()

        return JsonResponse({
            'success': True,
            'message': 'Venta realizada correctamente',
            'factura_id': factura.id
        })

    except Producto.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Uno de los productos ya no existe'
        }, status=400)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@requerir_rol(["SuperAdmin","Admin", "Empleado"])
def exportar_factura_pdf(request, pk):
    # 1. Obtener la factura o retornar 404 si no existe
    factura = get_object_or_404(Factura, pk=pk)
    
    # 2. Configurar la respuesta HTTP para PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="factura_{factura.id}.pdf"'
    
    # 3. Configurar el documento PDF
    doc = SimpleDocTemplate(response, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elementos = []
    
    estilos = getSampleStyleSheet()
    
    # Estítulo personalizado

    estilo_titulo = ParagraphStyle(
        'TituloFactura',
        parent=estilos['Heading1'] if 'Heading1' in estilos else estilos['Normal'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.HexColor('#1A365D')
    )
    
    # Datos generales de la factura
    elementos.append(Paragraph(f"Factura de Venta N° {factura.id}", estilo_titulo))
    elementos.append(Paragraph(f"<b>Cliente:</b> {factura.cliente.nombre}", estilos['Normal']))
    elementos.append(Paragraph(f"<b>Correo:</b> {factura.cliente.correo}", estilos['Normal']))
    elementos.append(Paragraph(f"<b>Fecha:</b> {factura.fecha if hasattr(factura, 'fecha') else 'N/A'}", estilos['Normal']))
    elementos.append(Paragraph(f"<b>Atendido por:</b> {factura.usuario}", estilos['Normal']))
    elementos.append(Spacer(1, 15))
    
    # 4. Construir los datos de la tabla de productos
    data = [["Producto", "Cantidad", "Precio Unit.", "Subtotal"]]
    
    # Obtenemos los detalles relacionados a esta factura
    detalles = factura.detallefactura_set.all() if hasattr(factura, 'detallefactura_set') else DetalleFactura.objects.filter(factura=factura)
    
    for detalle in detalles:
        data.append([
            detalle.producto.nombre,
            str(detalle.cantidad),
            f"${detalle.precio}",
            f"${detalle.subtotal}"
        ])
        
    # Añadir filas de totales
    data.append(["", "", "Descuento:", f"${factura.descuento}"])
    data.append(["", "", "Total Final:", f"${factura.total}"])

    # 5. Estilizar la tabla
    tabla = Table(data, colWidths=[200, 70, 100, 100])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2B6CB0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F7FAFC')),
        ('GRID', (0, 0), (-1, -3), 0.5, colors.HexColor('#CBD5E0')),
        ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'), # Resaltar totales
    ]))

    elementos.append(tabla)

    # 6. Compilar y retornar el PDF
    doc.build(elementos)
    return response        