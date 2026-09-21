import pytest
from datetime import timedelta

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIClient

from apps.api.authentication import ExpiringTokenAuthentication
from apps.auditoria.models import Auditoria
from apps.productos.models import Producto


class ApiIndexTests(TestCase):
    def setUp(self):
        # La API exige autenticación (token) desde la corrección de seguridad.
        self.usuario = User.objects.create_user(
            username='api_admin',
            password='ClaveSegura123',
            is_staff=True,
        )
        self.token = Token.objects.get(user=self.usuario)

    def test_api_index_returns_available_endpoints(self):
        response = self.client.get(
            '/api/',
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '/api/auditoria/')
        self.assertContains(response, '/api/clientes/')
        self.assertContains(response, '/api/productos/')

    def test_auditoria_endpoint_returns_records(self):
        Auditoria.objects.create(usuario='admin', accion='crear', modulo='USUARIOS')

        response = self.client.get(
            '/api/auditoria/',
            HTTP_AUTHORIZATION=f'Token {self.token.key}',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]['usuario'], 'admin')

    def test_api_index_public_but_data_requires_auth(self):
        # La raíz de la API es pública: lista las rutas, pero no expone datos.
        response = self.client.get('/api/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'productos')
        self.assertContains(response, 'clientes')

        # Los endpoints de datos sí exigen autenticación.
        clientes = self.client.get('/api/clientes/')
        self.assertNotEqual(clientes.status_code, 200)


@pytest.mark.django_db
def test_productos_son_de_lectura_publica():
    Producto.objects.create(nombre='Filtro', precio=25000, stock=5, categoria='Filtros')

    response = APIClient().get('/api/productos/')

    assert response.status_code == 200
    assert 'Filtro' in response.content.decode()


@pytest.mark.django_db
def test_escritura_sin_rol_denegada():
    response = APIClient().post('/api/productos/', {
        'nombre': 'Filtro',
        'precio': 25000,
        'stock': 5,
        'categoria': 'Filtros',
    }, format='json')

    assert response.status_code == 403


@pytest.mark.django_db
def test_productos_bajo_stock():
    cliente = APIClient()
    staff = User.objects.create_user(
        username='api_staff', password='ClaveSegura123', is_staff=True,
    )
    token = Token.objects.get(user=staff)
    cliente.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    Producto.objects.create(nombre='Escaso', precio=25000, stock=2, categoria='Filtros')
    Producto.objects.create(nombre='Abundante', precio=25000, stock=50, categoria='Filtros')

    response = cliente.get('/api/productos/bajo_stock/')

    assert response.status_code == 200
    nombres = [p['nombre'] for p in response.json()]
    assert 'Escaso' in nombres
    assert 'Abundante' not in nombres


@pytest.mark.django_db
def test_token_invalido_rechazado():
    response = APIClient().get(
        '/api/clientes/', HTTP_AUTHORIZATION='Token clave-inexistente'
    )

    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_token_expirado_es_invalido():
    staff = User.objects.create_user(
        username='api_viejo', password='ClaveSegura123', is_staff=True,
    )
    token = Token.objects.get(user=staff)
    token.created = timezone.now() - timedelta(hours=24)
    token.save()

    auth = ExpiringTokenAuthentication()
    with pytest.raises(AuthenticationFailed):
        auth.authenticate_credentials(token.key)


@pytest.mark.django_db
def test_admin_con_token_puede_crear_cliente():
    cliente = APIClient()
    staff = User.objects.create_user(
        username='api_admin2', password='ClaveSegura123', is_staff=True,
    )
    token = Token.objects.get(user=staff)
    cliente.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    response = cliente.post('/api/clientes/', {
        'nombre': 'Cliente API',
        'correo': 'api@cliente.com',
    }, format='json')

    assert response.status_code == 201
    assert response.json()['nombre'] == 'Cliente API'


@pytest.mark.django_db
def test_empleado_con_token_no_puede_escribir():
    cliente = APIClient()
    empleado = User.objects.create_user(
        username='api_empleado', password='ClaveSegura123', is_staff=False,
    )
    token = Token.objects.get(user=empleado)
    cliente.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    response = cliente.post('/api/clientes/', {
        'nombre': 'Cliente API',
        'correo': 'api@cliente.com',
    }, format='json')

    assert response.status_code == 403


@pytest.mark.django_db
def test_logout_destruye_token():
    staff = User.objects.create_user(
        username='api_logout', password='ClaveSegura123', is_staff=True,
    )
    token = Token.objects.get(user=staff)
    cliente = APIClient()
    cliente.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    response = cliente.post('/api/auth/logout/')

    assert response.status_code == 200
    assert not Token.objects.filter(user=staff).exists()


@pytest.mark.django_db
def test_login_token_obtiene_credenciales():
    User.objects.create_user(
        username='api_login', password='ClaveSegura123', is_staff=True,
    )

    response = APIClient().post('/api/api-token-auth/', {
        'username': 'api_login',
        'password': 'ClaveSegura123',
    }, format='json')

    assert response.status_code == 200
    assert response.json()['token']
