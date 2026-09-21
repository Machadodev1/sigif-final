import pytest

from apps.auditoria.models import Auditoria


@pytest.mark.django_db
def test_ver_auditoria_requiere_inicio_sesion(client):
    response = client.get('/auditoria/')
    assert response.status_code == 302
    assert response.url.startswith('/inicio/')


@pytest.mark.django_db
def test_empleado_no_puede_ver_auditoria(client_empleado):
    Auditoria.objects.create(usuario='admin', accion='crear', modulo='USUARIOS')

    response = client_empleado.get('/auditoria/')

    assert response.status_code == 302
    assert response.url.startswith('/inicio/')


@pytest.mark.django_db
def test_admin_ve_lista_de_registros(client_admin):
    Auditoria.objects.create(usuario='admin', accion='Creó Producto (id=1)', modulo='PRODUCTOS')

    response = client_admin.get('/auditoria/')

    assert response.status_code == 200
    contenido = response.content.decode()
    assert 'Creó Producto (id=1)' in contenido


@pytest.mark.django_db
def test_filtro_por_modulo(client_admin):
    Auditoria.objects.create(usuario='admin', accion='creo-usuario-x', modulo='USUARIOS')
    Auditoria.objects.create(usuario='admin', accion='vende-factura-y', modulo='FACTURACION')

    response = client_admin.get('/auditoria/?modulo=FACTURACION')

    assert response.status_code == 200
    contenido = response.content.decode()
    assert 'vende-factura-y' in contenido
    assert 'creo-usuario-x' not in contenido


@pytest.mark.django_db
def test_filtro_por_usuario(client_admin):
    Auditoria.objects.create(usuario='ana', accion='crear', modulo='USUARIOS')
    Auditoria.objects.create(usuario='luis', accion='crear', modulo='USUARIOS')

    response = client_admin.get('/auditoria/?usuario=ana')

    assert response.status_code == 200
    contenido = response.content.decode()
    assert 'ana' in contenido
    assert 'luis' not in contenido


@pytest.mark.django_db
def test_filtro_por_rango_de_fechas(client_admin):
    Auditoria.objects.create(usuario='admin', accion='ayer', modulo='USUARIOS')

    response = client_admin.get('/auditoria/?fecha_desde=2026-09-20&fecha_hasta=2026-09-21')

    assert response.status_code == 200


@pytest.mark.django_db
def test_exportar_excel(client_admin):
    Auditoria.objects.create(usuario='admin', accion='crear', modulo='USUARIOS')

    response = client_admin.get('/auditoria/exportar/excel/')

    assert response.status_code == 200
    assert response['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    assert 'informe_auditoria.xlsx' in response['Content-Disposition']


@pytest.mark.django_db
def test_exportar_pdf(client_admin):
    Auditoria.objects.create(usuario='admin', accion='crear', modulo='USUARIOS')

    response = client_admin.get('/auditoria/exportar/pdf/')

    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'
    assert 'informe_auditoria.pdf' in response['Content-Disposition']


@pytest.mark.django_db
def test_exportar_excel_sin_registros(client_admin):
    response = client_admin.get('/auditoria/exportar/excel/')
    assert response.status_code == 200