from decimal import Decimal
from unittest.mock import patch

import pytest

from apps.auditoria.models import Auditoria
from apps.facturacion.models import Cliente, DetalleFactura, Factura
from apps.productos.models import Producto


@pytest.fixture(autouse=True)
def _sin_envio_correo(monkeypatch):
    monkeypatch.setattr(
        'apps.facturacion.views.enviar_factura_correo',
        lambda factura: None,
    )


@pytest.mark.django_db
def test_listar_facturas_requiere_login(client):
    response = client.get('/facturacion/facturas/')
    assert response.status_code == 302


@pytest.mark.django_db
def test_listar_facturas_con_sesion(client_admin):
    cliente = Cliente.objects.create(nombre='Cliente A', correo='clientea@mail.com')
    Factura.objects.create(cliente=cliente, total=Decimal('50000'))

    response = client_admin.get('/facturacion/facturas/')

    assert response.status_code == 200
    assert 'Cliente A' in response.content.decode()


@pytest.mark.django_db
def test_listar_clientes(client_admin):
    Cliente.objects.create(nombre='Cliente A', correo='clientea@mail.com')

    response = client_admin.get('/facturacion/clientes/')

    assert response.status_code == 200
    assert 'Cliente A' in response.content.decode()


@pytest.mark.django_db
def test_pago_muestra_clientes(client_admin):
    Cliente.objects.create(nombre='Cliente A', correo='clientea@mail.com')

    response = client_admin.get('/facturacion/pago/')

    assert response.status_code == 200
    assert 'Cliente A' in response.content.decode()


@pytest.mark.django_db
def test_confirmar_venta_registra_factura_y_descuenta_stock(client_admin):
    producto = Producto.objects.create(
        nombre='Filtro', precio=25000, stock=10, categoria='Filtros'
    )

    response = client_admin.post('/facturacion/confirmar-venta/', data={
        'productos': [{'id': producto.id, 'cantidad': 3}],
        'metodo_pago': 'EFECTIVO',
        'nombre': 'Cliente A',
        'correo': 'clientea@mail.com',
    }, content_type='application/json')

    assert response.status_code == 200
    body = response.json()
    assert body['success'] is True

    factura = Factura.objects.get(pk=body['factura_id'])
    assert factura.total == Decimal('75000')
    assert factura.valor_pagado == Decimal('75000')
    assert factura.metodo_pago == 'EFECTIVO'

    detalle = DetalleFactura.objects.get(factura=factura)
    assert detalle.cantidad == 3
    assert detalle.subtotal == Decimal('75000')

    producto.refresh_from_db()
    assert producto.stock == 7
    assert Auditoria.objects.filter(modulo='FACTURACION').exists()


@pytest.mark.django_db
def test_confirmar_venta_con_descuento_codigo(client_admin):
    producto = Producto.objects.create(
        nombre='Filtro', precio=25000, stock=10, categoria='Filtros'
    )

    response = client_admin.post('/facturacion/confirmar-venta/', data={
        'productos': [{'id': producto.id, 'cantidad': 2}],
        'codigo_descuento': 'DESC10',
        'nombre': 'Cliente A',
    }, content_type='application/json')

    assert response.status_code == 200
    body = response.json()
    factura = Factura.objects.get(pk=body['factura_id'])
    assert factura.total == Decimal('45000')
    assert factura.descuento == Decimal('5000')


@pytest.mark.django_db
def test_confirmar_venta_descuenta_atomico_sin_modificar_si_falla_stock(client_admin):
    producto = Producto.objects.create(
        nombre='Filtro', precio=25000, stock=2, categoria='Filtros'
    )

    response = client_admin.post('/facturacion/confirmar-venta/', data={
        'productos': [{'id': producto.id, 'cantidad': 5}],
        'nombre': 'Cliente A',
    }, content_type='application/json')

    assert response.status_code == 400
    body = response.json()
    assert body['success'] is False
    assert Factura.objects.count() == 0

    producto.refresh_from_db()
    assert producto.stock == 2


@pytest.mark.django_db
def test_confirmar_venta_rechaza_metodo_no_post(client_admin):
    response = client_admin.get('/facturacion/confirmar-venta/')
    assert response.status_code == 405


@pytest.mark.django_db
def test_confirmar_venta_con_carrito_vacio(client_admin):
    response = client_admin.post('/facturacion/confirmar-venta/', data={
        'productos': [],
        'nombre': 'Cliente A',
    }, content_type='application/json')

    assert response.status_code == 200
    assert response.json()['success'] is False


@pytest.mark.django_db
def test_exportar_factura_pdf(client_admin):
    cliente = Cliente.objects.create(nombre='Cliente A', correo='clientea@mail.com')
    factura = Factura.objects.create(cliente=cliente, total=Decimal('50000'))

    response = client_admin.get(f'/facturacion/factura/pdf/{factura.id}/')

    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
    assert f'factura_{factura.id}.pdf' in response['Content-Disposition']


@pytest.mark.django_db
def test_empleado_solo_ve_sus_facturas(client_empleado, admin):
    cliente = Cliente.objects.create(nombre='Cliente A', correo='clientea@mail.com')
    mía = Factura.objects.create(cliente=cliente, total=Decimal('15000'), usuario='Empleado Test')
    ajena = Factura.objects.create(cliente=cliente, total=Decimal('99999'), usuario='Admin Tester')

    response = client_empleado.get('/facturacion/facturas/')

    assert response.status_code == 200
    contenido = response.content.decode()
    assert f'#{mía.id}' in contenido
    assert f'#{ajena.id}' not in contenido