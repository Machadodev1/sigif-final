import pytest
from django.core.exceptions import ValidationError

from apps.auditoria.models import Auditoria
from apps.productos.models import Producto


@pytest.mark.django_db
def test_crear_producto_correctamente():
    producto = Producto(
        nombre="Filtro de aceite",
        descripcion="Filtro para motor",
        precio=25000,
        stock=10,
        categoria="Filtros",
    )

    producto.full_clean()
    producto.save()

    assert producto.id is not None
    assert producto.nombre == "Filtro de aceite"
    assert producto.precio == 25000
    assert producto.stock == 10
    assert producto.categoria == "Filtros"
    assert producto.activo is True


@pytest.mark.django_db
def test_precio_cero_no_es_valido():
    producto = Producto(
        nombre="Filtro",
        precio=0,
        stock=10,
        categoria="Filtros",
    )

    with pytest.raises(ValidationError):
        producto.full_clean()


@pytest.mark.django_db
def test_precio_negativo_no_es_valido():
    producto = Producto(
        nombre="Filtro",
        precio=-5000,
        stock=10,
        categoria="Filtros",
    )

    with pytest.raises(ValidationError):
        producto.full_clean()


@pytest.mark.django_db
def test_stock_negativo_no_es_valido():
    producto = Producto(
        nombre="Filtro",
        precio=25000,
        stock=-1,
        categoria="Filtros",
    )

    with pytest.raises(ValidationError):
        producto.full_clean()


@pytest.mark.django_db
def test_stock_cero_es_valido():
    producto = Producto(
        nombre="Filtro",
        precio=25000,
        stock=0,
        categoria="Filtros",
    )

    producto.full_clean()
    producto.save()

    assert producto.stock == 0


@pytest.mark.django_db
def test_sanitiza_html_del_nombre():
    producto = Producto(
        nombre="<script>Filtro</script>",
        precio=25000,
        stock=10,
        categoria="Filtros",
    )

    producto.save()

    assert producto.nombre == "scriptFiltro/script"


@pytest.mark.django_db
def test_sanitiza_html_de_la_descripcion():
    producto = Producto(
        nombre="Filtro",
        descripcion="<script>alert('x')</script>",
        precio=25000,
        stock=10,
        categoria="Filtros",
    )

    producto.save()

    assert producto.descripcion == "scriptalert('x')/script"


@pytest.mark.django_db
def test_sanitiza_html_de_la_categoria():
    producto = Producto(
        nombre="Filtro",
        precio=25000,
        stock=10,
        categoria="<Filtros>",
    )

    producto.save()

    assert producto.categoria == "Filtros"


@pytest.mark.django_db
def test_producto_inactivo():
    producto = Producto(
        nombre="Filtro",
        precio=25000,
        stock=10,
        categoria="Filtros",
        activo=False,
    )

    producto.save()

    assert producto.activo is False


@pytest.mark.django_db
def test_fecha_creacion_se_genera():
    producto = Producto.objects.create(
        nombre="Filtro",
        precio=25000,
        stock=10,
        categoria="Filtros",
    )

    assert producto.fecha_creacion is not None
    assert producto.fecha_actualizacion is not None


@pytest.mark.django_db
def test_listar_productos_requiere_login(client):
    response = client.get('/productos/')
    assert response.status_code == 302


@pytest.mark.django_db
def test_listar_productos_muestra_registros(client_admin):
    Producto.objects.create(nombre='Filtro', precio=25000, stock=5, categoria='Filtros')

    response = client_admin.get('/productos/')

    assert response.status_code == 200
    assert 'Filtro' in response.content.decode()


@pytest.mark.django_db
def test_listar_productos_filtra_por_busqueda(client_admin):
    Producto.objects.create(nombre='Aceite 10W-40', precio=45000, stock=8, categoria='Lubricantes y Fluidos')
    Producto.objects.create(nombre='Bujía', precio=15000, stock=20, categoria='Motor')

    response = client_admin.get('/productos/?q=aceite')

    assert response.status_code == 200
    contenido = response.content.decode()
    assert 'Aceite 10W-40' in contenido
    assert 'Bujía' not in contenido


@pytest.mark.django_db
def test_crear_producto_valido(client_admin):
    response = client_admin.post('/productos/crear_productos/', {
        'nombre': 'Freno de disco',
        'categoria': 'Frenos',
        'precio': '120000',
        'stock': '4',
        'descripcion': 'Repuesto original',
    })

    assert response.status_code == 302
    producto = Producto.objects.get(nombre='Freno de disco')
    assert producto.precio == 120000
    assert producto.stock == 4
    assert Auditoria.objects.filter(modulo='PRODUCTOS').exists()


@pytest.mark.django_db
def test_crear_producto_invalido_no_guarda(client_admin):
    response = client_admin.post('/productos/crear_productos/', {
        'nombre': '',
        'categoria': 'Frenos',
        'precio': '120000',
        'stock': '4',
    })

    assert response.status_code == 200
    assert not Producto.objects.filter(nombre='').exists()


@pytest.mark.django_db
def test_crear_producto_con_html_es_rechazado_por_formulario(client_admin):
    response = client_admin.post('/productos/crear_productos/', {
        'nombre': '<script>alert(1)</script>',
        'categoria': 'Frenos',
        'precio': '120000',
        'stock': '4',
    })

    assert response.status_code == 200
    assert not Producto.objects.exists()


@pytest.mark.django_db
def test_actualizar_producto(client_admin):
    producto = Producto.objects.create(
        nombre='Filtro', precio=25000, stock=5, categoria='Filtros'
    )

    response = client_admin.post(
        f'/productos/actualizar_productos/{producto.id}/',
        {
            'nombre': 'Filtro premium',
            'categoria': 'Filtros',
            'precio': '30000',
            'descripcion': 'Actualizado',
        },
    )

    assert response.status_code == 302
    producto.refresh_from_db()
    assert producto.nombre == 'Filtro premium'
    assert producto.precio == 30000


@pytest.mark.django_db
def test_activar_desactivar_producto(client_admin):
    producto = Producto.objects.create(
        nombre='Filtro', precio=25000, stock=5, categoria='Filtros'
    )

    response = client_admin.post(f'/productos/activar-desactivar/{producto.id}/')

    assert response.status_code == 302
    producto.refresh_from_db()
    assert producto.activo is False

    client_admin.post(f'/productos/activar-desactivar/{producto.id}/')
    producto.refresh_from_db()
    assert producto.activo is True


@pytest.mark.django_db
def test_empleado_no_puede_desactivar_producto(client_empleado):
    producto = Producto.objects.create(
        nombre='Filtro', precio=25000, stock=5, categoria='Filtros'
    )

    response = client_empleado.post(f'/productos/activar-desactivar/{producto.id}/')

    assert response.status_code == 302
    producto.refresh_from_db()
    assert producto.activo is True