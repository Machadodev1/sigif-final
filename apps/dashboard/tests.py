from decimal import Decimal

import pytest

from apps.auditoria.models import Auditoria
from apps.facturacion.models import Cliente, Factura
from apps.productos.models import Producto


@pytest.fixture
def datos_dashboard(db):
    Producto.objects.create(nombre='Filtro', precio=25000, stock=2, categoria='Filtros')
    Producto.objects.create(nombre='Bujía', precio=15000, stock=0, categoria='Motor')
    Producto.objects.create(nombre='Aceite', precio=45000, stock=50, categoria='Lubricantes y Fluidos')

    cliente = Cliente.objects.create(nombre='Cliente A', correo='clientea@mail.com')
    Factura.objects.create(cliente=cliente, total=Decimal('100000'))

    Auditoria.objects.create(usuario='admin', accion='Creó Producto (id=1)', modulo='PRODUCTOS')
    Auditoria.objects.create(usuario='admin', accion='Creó Usuario (id=1)', modulo='USUARIOS')
    Auditoria.objects.create(usuario='admin', accion='Creó Factura (id=1)', modulo='FACTURACION')
    Auditoria.objects.create(usuario='admin', accion='Creó Gasto (id=1)', modulo='FINANZAS')


def test_dashboard_es_accesible_sin_sesion(client, datos_dashboard):
    response = client.get('/inicio/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_dashboard_muestra_totales(client, datos_dashboard):
    response = client.get('/inicio/')
    contenido = response.content.decode()

    assert response.status_code == 200
    assert 'con stock bajo' in contenido
    assert 'agotado' in contenido


@pytest.mark.django_db
def test_dashboard_muestra_ventas_del_mes(client, datos_dashboard):
    response = client.get('/inicio/')
    contenido = response.content.decode()

    assert response.status_code == 200
    assert '100,000' in contenido


@pytest.mark.django_db
def test_dashboard_muestra_actividades_recientes(client, datos_dashboard):
    response = client.get('/inicio/')
    contenido = response.content.decode()

    assert response.status_code == 200
    assert 'Creó Producto (id=1)' in contenido


@pytest.mark.django_db
def test_dashboard_sin_datos_no_falla(client):
    response = client.get('/inicio/')
    assert response.status_code == 200