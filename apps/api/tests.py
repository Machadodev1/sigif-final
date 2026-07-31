from django.test import TestCase
from django.urls import reverse
from apps.auditoria.models import Auditoria


class ApiIndexTests(TestCase):
    def test_api_index_returns_available_endpoints(self):
        response = self.client.get(reverse('api:index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'auditoria')
        self.assertContains(response, 'cliente')
        self.assertContains(response, 'producto')

    def test_auditoria_endpoint_returns_records(self):
        Auditoria.objects.create(usuario='admin', accion='crear', modulo='USUARIOS')

        response = self.client.get('/api/auditoria/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]['usuario'], 'admin')
