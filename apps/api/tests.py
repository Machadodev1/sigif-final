from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from apps.auditoria.models import Auditoria


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

    def test_api_index_rejects_anonymous(self):
        response = self.client.get('/api/')

        self.assertNotEqual(response.status_code, 200)
