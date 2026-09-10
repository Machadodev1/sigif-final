from django.test import TestCase
from django.urls import reverse

from apps.usuarios.models import Usuarios

from .models import EmpresaConfig


def _loguear_admin(client, admin):
    session = client.session
    session['logueado'] = {'id': admin.id, 'nombre': admin.nombre, 'rol': admin.cargo}
    session.save()


class ConfiguracionEmpresaTests(TestCase):
    def setUp(self):
        self.admin = Usuarios.objects.create(
            nombre='Admin',
            documento='11111111',
            contra='secret123',
            telefono='3001112234',
            correo='admin2@empresa.com',
            cargo='Admin',
            activo=True,
        )
        _loguear_admin(self.client, self.admin)

    def test_correo_invalido_no_guarda_configuracion(self):
        self._seed_config(impuesto='19')
        config = EmpresaConfig.objects.first()
        self.assertNotEqual(config.correo_contacto, '')

        response = self.client.post(reverse('configuracion'), {
            'moneda': 'COP ($) - Pesos Colombianos',
            'impuesto': '19',
            'correo_contacto': 'correo-no-valido',
        })
        self.assertEqual(response.status_code, 200)
        # Se conserva el valor previo (el save no debe ejecutarse con datos inválidos).
        EmpresaConfig.objects.get(pk=config.pk)

    def test_correo_valido_guarda_configuracion(self):
        self._seed_config(impuesto='19')
        response = self.client.post(reverse('configuracion'), {
            'moneda': 'COP ($) - Pesos Colombianos',
            'impuesto': '19',
            'correo_contacto': 'nuevo@soporte.com',
        })
        self.assertEqual(response.status_code, 200)
        config = EmpresaConfig.objects.get()
        self.assertEqual(config.correo_contacto, 'nuevo@soporte.com')
        self.assertEqual(config.impuesto, '19')

    def test_datos_empresa_sin_nombre_no_cambian(self):
        self._seed_config(nombre_comercial='SIGIF')
        response = self.client.post(reverse('configuracion'), {
            'nombre_comercial': '   ',
            'nit': '900.123.456-7',
            'direccion': 'Calle 10',
        })
        self.assertEqual(response.status_code, 200)
        config = EmpresaConfig.objects.get()
        self.assertEqual(config.nombre_comercial, 'SIGIF')

    def test_nombre_empresa_con_html_se_sanea(self):
        self._seed_config(nombre_comercial='SIGIF')
        response = self.client.post(reverse('configuracion'), {
            'nombre_comercial': '<b>SumiRepuestos</b>',
            'nit': '900.123.456-7',
            'direccion': 'Calle 10 # 20-30',
        })
        self.assertEqual(response.status_code, 200)
        config = EmpresaConfig.objects.get()
        self.assertNotIn('<', config.nombre_comercial)
        self.assertNotIn('>', config.nombre_comercial)

    def _seed_config(self, **overrides):
        datos = {
            'nombre_comercial': 'SIGIF',
            'nit': '900.123.456-7',
            'direccion': 'CASA DE MOYA "LA AURORA"',
            'moneda': 'COP ($) - Pesos Colombianos',
            'impuesto': '19%',
            'correo_contacto': 'soporte@sigif.com',
        }
        datos.update(overrides)
        EmpresaConfig.objects.create(**datos)


class BackupyPermisosTests(TestCase):
    def setUp(self):
        self.superadmin = Usuarios.objects.create(
            nombre='Super',
            documento='22222222',
            contra='secret123',
            telefono='3001112235',
            correo='super@empresa.com',
            cargo='SuperAdmin',
            activo=True,
        )
        self.empleado = Usuarios.objects.create(
            nombre='Empleado',
            documento='33333333',
            contra='secret123',
            telefono='3001112236',
            correo='empleado@empresa.com',
            cargo='Empleado',
            activo=True,
        )
        _loguear_admin(self.client, self.superadmin)

    def test_cargo_invalido_no_cambia_rol(self):
        response = self.client.post(reverse('backupypermisos'), {
            'user_id': self.empleado.id,
            'rol_asignar': 'Presidente',
        })
        self.assertEqual(response.status_code, 302)
        self.empleado.refresh_from_db()
        self.assertEqual(self.empleado.cargo, 'Empleado')

    def test_cargo_valido_cambia_rol(self):
        response = self.client.post(reverse('backupypermisos'), {
            'user_id': self.empleado.id,
            'rol_asignar': 'Admin',
        })
        self.assertEqual(response.status_code, 302)
        self.empleado.refresh_from_db()
        self.assertEqual(self.empleado.cargo, 'Admin')

    def test_user_id_no_numerico_no_cambia_rol(self):
        response = self.client.post(reverse('backupypermisos'), {
            'user_id': 'abc',
            'rol_asignar': 'SuperAdmin',
        })
        self.assertEqual(response.status_code, 302)
        self.empleado.refresh_from_db()
        self.assertEqual(self.empleado.cargo, 'Empleado')