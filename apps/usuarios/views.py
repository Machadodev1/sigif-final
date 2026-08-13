# pyrefly: ignore [missing-import]
from django.shortcuts import render, redirect, get_object_or_404
# pyrefly: ignore [missing-import]
from django.contrib import messages
# pyrefly: ignore [missing-import]
from django.db.models import Q
from .forms import UsuarioForm
from .models import Usuarios
# pyrefly: ignore [missing-import]
from apps.auditoria.models import Auditoria
from core.decoradores import requerir_rol



def login_view(request):
    if request.method == "POST":
        usuario = request.POST.get("user")
        contra = request.POST.get("clave")
        try:
            t = Usuarios.objects.get(nombre = usuario, contra = contra)
            messages.success(request, "Bienvenido al sistema")
            request.session["logueado"] = {
                "id":t.id,
                "nombre": f"{t.nombre}",
                "rol":t.cargo
            }
            return redirect("dashboard")  
        except Usuarios.DoesNotExist:
            messages.error(request, "Usuario o contraseña incorrecto")
            request.session["logueado"] = None
            return redirect('login')     
    else:
        if request.session.get("logueado", False):
            return redirect('dashboard')
        else:
            return render(request, "usuarios/login.html")

@requerir_rol(["Admin"])
def usuarios(request):
    user = Usuarios.objects.all()
    q = request.GET.get('q', '').strip()
    if q:
        user = user.filter(
            Q(nombre__icontains=q) | 
            Q(cargo__icontains=q) | 
            Q(telefono__icontains=q)
        )
    return render(request, 'usuarios/usuarios.html', {'user': user, 'q': q})


@requerir_rol(["Admin"])
def crear_usuarios(request):
    if request.method == 'POST':
        form = UsuarioForm (request.POST)
        if form.is_valid():
            usuarios = form.save()
            Auditoria.objects.create(
                usuario=request.session["logueado"]["nombre"],
                accion=f"CREO USUARIO: {usuarios.nombre}",
                modulo="USUARIOS"
            )

            return redirect('usuarios')
    else:
        form = UsuarioForm ()
    return render(request, "usuarios/crear_usuarios.html",  {'form': form})


@requerir_rol(["Admin"])
def editar_usuarios(request, id):
    usuarios = get_object_or_404(Usuarios, id=id)
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuarios)
        if  form.is_valid():
            usuarios = form.save()
            Auditoria.objects.create(
                usuario=request.session["logueado"]["nombre"],
                accion=f"ACTUALIZO USUARIO: {usuarios.nombre}",
                modulo="USUARIOS"
            )
            return redirect('usuarios')
    else:
        form = UsuarioForm(instance=usuarios)
    return render(request, 'usuarios/editar_usuarios.html', {'form': form})

@requerir_rol(["Admin"])
def eliminar_usuario(request, id):
    usuarios = get_object_or_404(Usuarios, id=id)
    if request.method == 'POST':
        nombre = usuarios.nombre 
        usuarios.delete()
        Auditoria.objects.create(
                usuario=request.session["logueado"]["nombre"],
                accion=f"ELIMINO USUARIO: {nombre}",
                modulo="USUARIOS"
            )
        return redirect('usuarios')
    else:
        return render(request, 'usuarios/eliminar_usuario.html', {'usuarios': usuarios})


def logout_view(request):
    logueado = request.session.get("logueado")
    if logueado:
        Auditoria.objects.create(
            usuario=logueado.get("nombre", ""),
            accion="CERRO SESION",
            modulo="USUARIOS",
        )

    request.session.flush()
    messages.success(request, "Sesion cerrada")
    return redirect('login')
