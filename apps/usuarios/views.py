# pyrefly: ignore [missing-import]
from urllib import request

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



@requerir_rol(["SuperAdmin", "Admin", "Empleado" ])
def cambiar_estado_usuario(request, id):
    usuario = get_object_or_404(Usuarios, id=id)

    rol_actual = request.session["logueado"]["rol"]

    # Un Empleado no puede cambiar estados
    if rol_actual == "Empleado":
        messages.error(
            request,
            "No tienes permiso para cambiar el estado de los usuarios."
        )
        return redirect("usuarios")
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


@requerir_rol(["SuperAdmin", "Admin", "Empleado"])
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

    usuario_actual_id = request.session["logueado"]["id"]
    rol_actual = request.session["logueado"]["rol"]

    if rol_actual == "Empleado" and usuario.id != usuario_actual_id:
        messages.error(
        request,
        "Solo tienes permiso para editar tu propio perfil."
    )
        return redirect("usuarios")


    cargo_original = usuario.cargo
    estado_original = usuario.activo

    if request.method == "POST":

        form = UsuarioForm(
            request.POST,
            instance=usuario
        )

        if form.is_valid():

            usuario_editado = form.save(commit=False)

            nuevo_cargo = usuario_editado.cargo


            if usuario.id == usuario_actual_id or rol_actual == "Empleado":
                usuario_editado.cargo = cargo_original

            usuario_editado.activo = estado_original


            print("USUARIO EDITADO:", usuario)
            print("USUARIO LOGUEADO:", request.user)
            print("ID EDITADO:", usuario.id)
            print("ID LOGUEADO:", request.user.id)
            print("ROL ACTUAL:", rol_actual)
            print("CARGO ORIGINAL:", cargo_original)

            usuario_logueado = request.session.get("logueado")

            # ==========================================
            # 3. ADMIN NO PUEDE MODIFICAR AL SUPERADMIN
            # ==========================================

            if (
                rol_actual == "Admin"
                and cargo_original == "SuperAdmin" 
            ):

                messages.error(
                    request,
                    "Un Admin no puede modificar al SuperAdmin."
                )

                return render(
                    request,
                    "usuarios/editar_usuarios.html",
                    {"form": form}
                )

            if (
                 rol_actual == "Admin"
                and cargo_original == "Admin" 
                and usuario_logueado
                and usuario.id != usuario_logueado["id"]
            ):
            
                messages.error(
                    request,
                    "Un Admin no puede modificar al Admin."
                )
            
                return render(
                    request,
                    "usuarios/editar_usuarios.html",
                    {"form": form}
                )
            

            # ==========================================
            # 4. ADMIN NO PUEDE CREAR OTRO SUPERADMIN
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
            # 5. GUARDAR
            # ==========================================

            usuario_editado.save()

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
                return redirect("usuarios")

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
    messages.error(request, "Sesion cerrada")
    return redirect('login')
#prueba