from .models import Producto
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .form import ProductoForm
from core.decoradores import requerir_rol
from apps.auditoria.models import Auditoria


@requerir_rol(["Admin", "Empleado"])
def productos(request):
    productos = Producto.objects.all()
    q = request.GET.get('q', '').strip()
    if q:
        productos = productos.filter(
            Q(nombre__icontains=q) | 
            Q(descripcion__icontains=q) | 
            Q(categoria__icontains=q)
        )
    return render(request, 'productos/productos.html', {'productos': productos, 'q': q})


@requerir_rol(["Admin", "Empleado"])
def crear_producto(request): 
    if request.method == "POST":
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save()
            Auditoria.objects.create(
                usuario=request.session["logueado"]["nombre"],
                accion=f"CREO UN PRODUCTO: {producto.nombre}",
                modulo="PRODUCTOS"
            )
            return redirect('productos')
    else:
        form = ProductoForm()
    return render(request, 'productos/crear_productos.html', {'form': form})

@requerir_rol(["Admin", "Empleado"])
def actualizar_producto(request, id):
    producto = get_object_or_404(Producto, id=id)

    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            producto = form.save()
            Auditoria.objects.create(
                usuario=request.session["logueado"]["nombre"],
                accion=f"ACTUALIZO UN PRODUCTO: {producto.nombre}",
                modulo="PRODUCTOS"
            )
            return redirect('productos') 
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'productos/actualizar_productos.html', {'form': form})

@requerir_rol(["Admin", "Empleado"])
def activar_desactivar_producto(request, id):

    producto = get_object_or_404(Producto, id=id)

    if request.method == "POST":

        producto.activo = not producto.activo
        producto.save()

        estado = "ACTIVÓ" if producto.activo else "DESACTIVÓ"

        Auditoria.objects.create(
            usuario=request.session["logueado"]["nombre"],
            accion=f"{estado} EL PRODUCTO: {producto.nombre}",
            modulo="PRODUCTOS"
        )

    return redirect('productos')