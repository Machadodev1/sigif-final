import pytest
from django.test import Client

from apps.usuarios.models import Usuarios


def crear_usuario(nombre, documento, telefono, correo, cargo):
    usuario = Usuarios(
        nombre=nombre,
        documento=documento,
        telefono=telefono,
        correo=correo,
        cargo=cargo,
        activo=True,
    )
    usuario.set_password('ClaveSegura123')
    usuario.save()
    return usuario


def loguear_usuario(client, usuario):
    session = client.session
    session['logueado'] = {
        'id': usuario.id,
        'nombre': usuario.nombre,
        'rol': usuario.cargo,
    }
    session.save()


@pytest.fixture
def superadmin(db):
    return crear_usuario('Super Admin', '1111111111', '3111111111', 'super@empresa.com', 'SuperAdmin')


@pytest.fixture
def admin(db):
    return crear_usuario('Admin Tester', '2222222222', '3122222222', 'admin@empresa.com', 'Admin')


@pytest.fixture
def empleado(db):
    return crear_usuario('Empleado Test', '3333333333', '3133333333', 'empleado@empresa.com', 'Empleado')


@pytest.fixture
def client_admin(admin):
    cliente = Client()
    loguear_usuario(cliente, admin)
    return cliente


@pytest.fixture
def client_superadmin(superadmin):
    cliente = Client()
    loguear_usuario(cliente, superadmin)
    return cliente


@pytest.fixture
def client_empleado(empleado):
    cliente = Client()
    loguear_usuario(cliente, empleado)
    return cliente