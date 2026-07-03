from .models import Producto
from django.shortcuts import render, redirect, get_object_or_404
from .form import ProductoForm
from core.decoradores import requerir_rol
from apps.auditoria.models import Auditoria


# haidhasdhuyhasd
@requerir_rol(["Admin", "Empleado"])
def productos(request):
    productos = Producto.objects.all()
    return render(request, 'productos/productos.html',  {'productos': productos})


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
def eliminar_producto(request, id):
    producto = get_object_or_404(Producto, id = id)
    if request.method == "POST":
        nombre = producto.nombre
        producto.delete()
        Auditoria.objects.create(
                usuario=request.session["logueado"]["nombre"],
                accion=f"ELIMINO UN PRODUCTO: {nombre}",
                modulo="PRODUCTOS"
            )
        return redirect('productos')
    else:
        return render(request, 'productos/eliminar_productos.html', {'producto': producto})
