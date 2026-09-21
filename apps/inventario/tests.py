from decimal import Decimal

import pytest

from apps.auditoria.models import Auditoria
from apps.configuracion.models import EmpresaConfig
from apps.finanzas.models import Gasto
from apps.inventario.models import DetalleEntradaInventario, EntradaInventario
from apps.productos.models import Producto


@pytest.mark.django_db
def test_listar_inventario_requiere_login(client):
    response = client.get('/inventario/')
    assert response.status_code == 302


@pytest.mark.django_db
def test_listar_inventario_muestra_productos(client_empleado):
    Producto.objects.create(nombre='Filtro', precio=25000, stock=5, categoria='Filtros')

    response = client_empleado.get('/inventario/')

    assert response.status_code == 200
    assert 'Filtro' in response.content.decode()


@pytest.mark.django_db
def test_historial_inventario(client_admin):
    Producto.objects.create(nombre='Filtro', precio=25000, stock=5, categoria='Filtros')

    response = client_admin.get('/inventario/inv_historial/')

    assert response.status_code == 200


@pytest.mark.django_db
def test_control_inventario(client_admin):
    Producto.objects.create(nombre='Filtro', precio=25000, stock=5, categoria='Filtros')

    response = client_admin.get('/inventario/inv_control/')

    assert response.status_code == 200


@pytest.mark.django_db
def test_ingresos_inventario(client_admin):
    Producto.objects.create(nombre='Filtro', precio=25000, stock=5, categoria='Filtros')

    response = client_admin.get('/inventario/inv_ingresos/')

    assert response.status_code == 200


@pytest.mark.django_db
def test_configuracion_inventario(client_admin):
    EmpresaConfig.objects.create(nombre_comercial='SIGIF')

    response = client_admin.get('/inventario/inv_configuracion/')

    assert response.status_code == 200
    assert 'SIGIF' in response.content.decode()


@pytest.mark.django_db
def test_registrar_entrada_producto_existente_actualiza_stock(client_admin):
    producto = Producto.objects.create(
        nombre='Filtro', precio=25000, stock=10, categoria='Filtros'
    )

    response = client_admin.post(
        '/inventario/registrar-entrada/',
        data={
            'proveedor': 'Proveedor SA',
            'documento': 'REM-001',
            'items': [
                {
                    'producto_id': producto.id,
                    'cantidad': 5,
                    'precio': 10000,
                    'precio_venta': 18000,
                }
            ],
        },
        content_type='application/json',
    )

    assert response.status_code == 200
    body = response.json()
    assert body['success'] is True

    entrada = EntradaInventario.objects.get(pk=body['entrada_id'])
    assert entrada.total == Decimal('50000')
    assert entrada.numero_factura() == f'ENT-{entrada.id:05d}'

    detalle = DetalleEntradaInventario.objects.get(entrada=entrada)
    assert detalle.cantidad == 5

    producto.refresh_from_db()
    assert producto.stock == 15
    assert producto.precio == 18000

    assert Gasto.objects.filter(categoria='REPUESTOS', valor=Decimal('50000')).exists()
    assert Auditoria.objects.filter(modulo='INVENTARIO').exists()


@pytest.mark.django_db
def test_registrar_entrada_producto_nuevo(client_admin):
    response = client_admin.post(
        '/inventario/registrar-entrada/',
        data={
            'proveedor': 'Proveedor SA',
            'items': [
                {
                    'nombre': 'Aceite 10W-40',
                    'categoria': 'Lubricantes y Fluidos',
                    'cantidad': 8,
                    'precio': 20000,
                    'precio_venta': 32000,
                }
            ],
        },
        content_type='application/json',
    )

    assert response.status_code == 200
    body = response.json()
    assert body['success'] is True

    producto = Producto.objects.get(nombre='Aceite 10W-40')
    assert producto.stock == 8
    assert producto.precio == 32000

    entrada = EntradaInventario.objects.get(pk=body['entrada_id'])
    assert entrada.detalles.count() == 1


@pytest.mark.django_db
def test_registrar_entrada_proveedor_obligatorio(client_admin):
    response = client_admin.post(
        '/inventario/registrar-entrada/',
        data={'items': [{'producto_id': 1, 'cantidad': 1, 'precio': 100, 'precio_venta': 200}]},
        content_type='application/json',
    )

    assert response.status_code == 400
    assert response.json()['success'] is False
    assert EntradaInventario.objects.count() == 0


@pytest.mark.django_db
def test_registrar_entrada_cantidad_invalida(client_admin):
    producto = Producto.objects.create(
        nombre='Filtro', precio=25000, stock=10, categoria='Filtros'
    )

    response = client_admin.post(
        '/inventario/registrar-entrada/',
        data={
            'proveedor': 'Proveedor SA',
            'items': [
                {
                    'producto_id': producto.id,
                    'cantidad': 0,
                    'precio': 10000,
                    'precio_venta': 18000,
                }
            ],
        },
        content_type='application/json',
    )

    assert response.status_code == 400
    assert EntradaInventario.objects.count() == 0
    producto.refresh_from_db()
    assert producto.stock == 10


@pytest.mark.django_db
def test_registrar_entrada_precio_venta_menor_al_compra(client_admin):
    producto = Producto.objects.create(
        nombre='Filtro', precio=25000, stock=10, categoria='Filtros'
    )

    response = client_admin.post(
        '/inventario/registrar-entrada/',
        data={
            'proveedor': 'Proveedor SA',
            'items': [
                {
                    'producto_id': producto.id,
                    'cantidad': 5,
                    'precio': 10000,
                    'precio_venta': 9000,
                }
            ],
        },
        content_type='application/json',
    )

    assert response.status_code == 400
    assert EntradaInventario.objects.count() == 0


@pytest.mark.django_db
def test_registrar_entrada_json_invalido(client_admin):
    response = client_admin.post(
        '/inventario/registrar-entrada/',
        data='{"proveedor":',
        content_type='application/json',
    )

    assert response.status_code == 400
    assert response.json()['success'] is False


@pytest.mark.django_db
def test_registrar_entrada_requiere_login(client):
    response = client.post(
        '/inventario/registrar-entrada/',
        data={'proveedor': 'X', 'items': []},
        content_type='application/json',
    )
    assert response.status_code == 302


@pytest.mark.django_db
def test_exportar_entrada_pdf(client_admin):
    entrada = EntradaInventario.objects.create(proveedor='Proveedor SA')
    producto = Producto.objects.create(
        nombre='Filtro', precio=18000, stock=5, categoria='Filtros'
    )
    DetalleEntradaInventario.objects.create(
        entrada=entrada, producto=producto, cantidad=5, precio=10000, subtotal=50000
    )

    response = client_admin.get(f'/inventario/entrada/pdf/{entrada.id}/')

    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
    assert 'ENT-' in response['Content-Disposition']