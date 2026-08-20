import json
from decimal import Decimal

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
        return requerir_rol(["Admin", "Empleado"])(super().dispatch)(request, *args, **kwargs)


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