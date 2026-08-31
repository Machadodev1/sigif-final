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
from core.decoradores import requerir_rol, impedir_crear_superadmin



def login_view(request):
    if request.method == "POST":
        correo = (request.POST.get("correo") or "").strip().lower()
        contra = request.POST.get("clave")
        try:
            t = Usuarios.objects.get(
                correo__iexact=correo,
                contra=contra
            )

            # Verificar si el usuario está activo
            if not t.activo:
                messages.error(
                    request,
                    "Tu usuario está inactivo. Comunícate con un administrador."
                )
                request.session["logueado"] = None
                return redirect("login")

            messages.success(request, "Bienvenido al sistema")

            request.session["logueado"] = {
                "id": t.id,
                "nombre": t.nombre,
                "rol": t.cargo
            }

            return redirect("dashboard")

        except Usuarios.DoesNotExist:
            messages.error(
                request,
                "Usuario o contraseña incorrecto"
            )
            request.session["logueado"] = None
            return redirect("login")

    else:
        if request.session.get("logueado", False):
            return redirect("dashboard")
        else:
            return render(request, "usuarios/login.html")



@requerir_rol(["SuperAdmin", "Admin"])
def cambiar_estado_usuario(request, id):
    usuario = get_object_or_404(Usuarios, id=id)

    # El SuperAdmin no se puede desactivar
    if usuario.cargo == "SuperAdmin":
        messages.error(
            request,
            "El SuperAdmin no puede ser desactivado."
        )
        return redirect("usuarios")

    # No permitir que el usuario se desactive a sí mismo
    if usuario.id == request.session["logueado"]["id"]:
        messages.error(
            request,
            "No puedes desactivar tu propio usuario."
        )
        return redirect("usuarios")

    if request.method == "POST":
        usuario.activo = not usuario.activo
        usuario.save()

        estado = "ACTIVO" if usuario.activo else "INACTIVO"

        Auditoria.objects.create(
            usuario=request.session["logueado"]["nombre"],
            accion=f"CAMBIO ESTADO USUARIO: {usuario.nombre} → {estado}",
            modulo="USUARIOS"
        )

        if usuario.activo:
         messages.success(
        request,
        f"El usuario {usuario.nombre} ahora está activo."
    )
        else:
            messages.error(
        request,
        f"El usuario {usuario.nombre} ahora está inactivo."
    )

    return redirect("usuarios")


@requerir_rol(["SuperAdmin", "Admin"])
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


@requerir_rol(["SuperAdmin", "Admin"])
@impedir_crear_superadmin
def crear_usuarios(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            usuarios = form.save()
            Auditoria.objects.create(
                usuario=request.session["logueado"]["nombre"],
                accion=f"CREO USUARIO: {usuarios.nombre}",
                modulo="USUARIOS"
            )
            return redirect('usuarios')

        messages.error(request, "Falta información obligatoria para crear el usuario.")
        return render(request, "usuarios/crear_usuarios.html", {'form': form})

    form = UsuarioForm()
    return render(request, "usuarios/crear_usuarios.html", {'form': form})


@requerir_rol(["SuperAdmin", "Admin", "Empleado"])
def editar_usuarios(request, id):

    usuario = get_object_or_404(Usuarios, id=id)

    # Usuario que está realizando la acción
    usuario_actual_id = request.session["logueado"]["id"]
    rol_actual = request.session["logueado"]["rol"]

    # Restringir a Empleado para que solo pueda editar su propio perfil
    if rol_actual == "Empleado" and usuario.id != usuario_actual_id:
        messages.error(request, "Solo tienes permiso para editar tu propio perfil.")
        return redirect("dashboard")

    # Cargo original del usuario que estamos editando
    cargo_original = usuario.cargo

    if request.method == "POST":

        form = UsuarioForm(
            request.POST,
            instance=usuario
        )

        if form.is_valid():

            usuario_editado = form.save(commit=False)

            nuevo_cargo = usuario_editado.cargo

            # ==========================================
            # 1. NADIE PUEDE CAMBIAR SU PROPIO ROL / EMPLEADO NO PUEDE ALTERAR CARGO
            # ==========================================

            if usuario.id == usuario_actual_id or rol_actual == "Empleado":
                usuario_editado.cargo = cargo_original

            # ==========================================
            # 2. ADMIN NO PUEDE MODIFICAR AL SUPERADMIN
            # ==========================================

            if (
                rol_actual == "Admin"
                and cargo_original == "SuperAdmin" 
            ):

                messages.error(
                    request,
                    "Un Administrador no puede modificar al SuperAdmin."
                )

                return render(
                    request,
                    "usuarios/editar_usuarios.html",
                    {"form": form}
                )

            # ==========================================
            # 3. ADMIN NO PUEDE CREAR OTRO SUPERADMIN
            # ==========================================

            if (
                rol_actual == "Admin"
                and nuevo_cargo == "SuperAdmin"
                and cargo_original != "SuperAdmin"
            ):

                messages.error(
                    request,
                    "Un Administrador no puede asignar el rol de SuperAdmin."
                )

                return render(
                    request,
                    "usuarios/editar_usuarios.html",
                    {"form": form}
                )

            # ==========================================
            # 4. GUARDAR CAMBIOS
            # ==========================================

            usuario_editado.save()

            # Actualizar nombre en la sesión actual si editó su propio usuario
            if usuario_editado.id == usuario_actual_id:
                request.session["logueado"]["nombre"] = usuario_editado.nombre
                request.session.modified = True

            Auditoria.objects.create(
                usuario=request.session["logueado"]["nombre"],
                accion=f"ACTUALIZÓ PERFIL/USUARIO: {usuario_editado.nombre}",
                modulo="USUARIOS"
            )

            messages.success(
                request,
                f"El usuario {usuario_editado.nombre} fue actualizado correctamente."
            )

            if rol_actual == "Empleado":
                return redirect("dashboard")

            return redirect("usuarios")

        messages.error(
            request,
            "Falta información obligatoria para actualizar el usuario."
        )

        return render(
            request,
            "usuarios/editar_usuarios.html",
            {"form": form}
        )

    form = UsuarioForm(instance=usuario)

    return render(
        request,
        "usuarios/editar_usuarios.html",
        {"form": form}
    )

@requerir_rol(["SuperAdmin", "Admin"])
def eliminar_usuario(request, id):
    usuario = get_object_or_404(Usuarios, id=id)


    if usuario.cargo == "SuperAdmin":
        messages.error(
            request,
            "No se puede eliminar al Superadmin."
        )
        return redirect("usuarios")

    if usuario.nombre == request.session["logueado"]["nombre"]:
        messages.error(
            request,
            "No puedes eliminar tu propio usuario."
        )
        return redirect("usuarios")

    if request.method == 'POST':
        nombre = usuario.nombre 
        usuario.delete()
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
#prueba