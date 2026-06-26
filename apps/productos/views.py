from .models import Producto
from django.shortcuts import render, redirect, get_object_or_404
from .form import ProductoForm
from core.decoradores import requerir_rol


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
            form.save()
            return redirect('productos')
    else:
        form = ProductoForm()
    return render(request, 'productos/crear_productos.html', {'form': form})

@requerir_rol(["Admin", "Empleado"])
def actualizar_producto(request, id):
    product = get_object_or_404(Producto, id=id)

    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('productos') 
    else:
        form = ProductoForm(instance=product)

    return render(request, 'productos/actualizar_productos.html', {'form': form})

@requerir_rol(["Admin", "Empleado"])
def eliminar_producto(request, id):
    product = get_object_or_404(Producto, id = id)
    if request.method == "POST":
        product.delete()
        return redirect('productos')
    else:
        return render(request, 'productos/eliminar_productos.html', {'producto': product})
