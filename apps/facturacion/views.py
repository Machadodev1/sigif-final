from django.shortcuts import render
from django.views.generic import ListView, DetailView
from apps.facturacion.models import Factura
from apps.productos.models import Producto
from apps.facturacion.models import Cliente
from core.decoradores import requerir_rol


class FacturaListView(ListView):
    model = Factura
    template_name = 'facturacion/facturacion.html'
    context_object_name = 'facturas'

    def dispatch(self, request, *args, **kwargs):
        # Facturación es admin y empleado
        return requerir_rol(["Admin", "Empleado"])(super().dispatch)(request, *args, **kwargs)


class FacturaDetailView(DetailView):
    model = Factura
    template_name = 'facturacion/facturacion.html'
    context_object_name = 'factura'

    def dispatch(self, request, *args, **kwargs):
        # Facturación es admin y empleado
        return requerir_rol(["Admin", "Empleado"])(super().dispatch)(request, *args, **kwargs)


@requerir_rol(["Admin", "Empleado"])
def clientes_view(request):
    clientes = Cliente.objects.all()
    return render(request, 'facturacion/cliente.html', {'clientes': clientes})


@requerir_rol(["Admin", "Empleado"])
def productos_facturacion_view(request):
    productos = Producto.objects.all()

    return render(request, 'facturacion/productos_facturacion.html', {'productos': productos})


# Esta parte de la funcion es de los clientes ficticos para probar el diseño listo calisto
def clientes_view(request):
    # Intentamos traer los clientes reales de la base de datos
    clientes = Cliente.objects.all()
    
    # SI NO HAY CLIENTES EN LA BASE DE DATOS, CREAMOS UNOS EN MEMORIA PARA PROBAR EL DISEÑO:
    if not clientes.exists():
        # Creamos objetos ficticios usando el modelo para que el HTML no se rompa
        cliente1 = Cliente(nombre="Juan Pérez", correo="juan@email.com")
        cliente2 = Cliente(nombre="María Gómez", correo="maria@email.com")
        
        #  colocamos informacion para simular la base de datos
        cliente1.get_total_gastado = lambda: "150,000.00"
        cliente1.get_ultima_fecha = lambda: "2024-06-01"
        
        cliente2.get_total_gastado = lambda: "200,000.00"
        cliente2.get_ultima_fecha = lambda: "2024-06-02"
        
        clientes = [cliente1, cliente2] 

    return render(request, 'facturacion/cliente.html', {'clientes': clientes})



def productos_facturacion_view(request):
    # Intentamos ver si hay algo real en la base de datos
    productos = Producto.objects.all()
    
    # Si está vacía, inyectamos las autopartes con su desglose de ventas simulado
    if not productos.exists():
        prod1 = Producto(nombre="Kit Pastillas de Freno (Moto Yamaha NMAX)", precio=150000.00, stock=25)
        prod2 = Producto(nombre="Filtro de Aceite Sintético (Carro Chevrolet Sail)", precio=100000.00, stock=40)
        prod3 = Producto(nombre="Juego de Bujías de Iridium (Universal Carro)", precio=85000.00, stock=15)
        prod4 = Producto(nombre="Kit de Arrastre Racing (Moto Pulsar NS200)", precio=180000.00, stock=10)
        
        # --- Datos para el desglose tipo recibo ---
        prod1.comprador = "Juan Pérez"
        prod1.cantidad_vendida = 1
        prod1.subtotal_venta = 150000.00
        prod1.fecha_venta = "2024-06-01"
        prod1.num_factura = "001"

        prod2.comprador = "María Gómez"
        prod2.cantidad_vendida = 2
        prod2.subtotal_venta = 200000.00
        prod2.fecha_venta = "2024-06-02"
        prod2.num_factura = "002"
        
        productos = [prod1, prod2, prod3, prod4]

    return render(request, 'facturacion/productos_facturacion.html', {'productos': productos})