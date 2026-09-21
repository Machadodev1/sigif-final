from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from apps.auditoria.models import Auditoria

from .forms import UsuarioForm
from .models import Usuarios


class UsuarioAuthFormTests(TestCase):
    def test_labels_del_formulario_muestran_nombre_del_empleado_y_correo(self):
        form = UsuarioForm()

        self.assertEqual(form.fields['nombre'].label, 'Nombre del empleado')
        self.assertEqual(form.fields['correo'].label, 'Correo electrónico')

    def test_formulario_muestra_mensaje_de_campo_obligatorio(self):
        form = UsuarioForm(data={})

        self.assertFalse(form.is_valid())
        self.assertIn('El nombre del empleado es obligatorio para continuar.', form.errors['nombre'])
        self.assertIn('El correo electrónico es obligatorio para continuar.', form.errors['correo'])

    def test_crear_usuario_con_datos_invalidos_muestra_alerta(self):
        Usuarios.objects.create(
            nombre='Admin',
            contra='secret123',
            telefono='3001234567',
            correo='admin@empresa.com',
            cargo='Admin',
            activo=True,
        )

        session = self.client.session
        session['logueado'] = {'id': 1, 'nombre': 'Admin', 'rol': 'Admin'}
        session.save()

        response = self.client.post(reverse('crear_usuarios'), data={})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'El nombre del empleado es obligatorio para continuar.')

    def test_editar_usuario_muestra_campo_correo_en_el_formulario(self):
        usuario = Usuarios.objects.create(
            nombre='Ana García',
            contra='secret123',
            telefono='3001234567',
            correo='ana@empresa.com',
            cargo='Empleado',
            activo=True,
        )

        session = self.client.session
        session['logueado'] = {'id': 1, 'nombre': 'Admin', 'rol': 'Admin'}
        session.save()

        response = self.client.get(reverse('editar_usuarios', args=[usuario.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Correo')
        self.assertContains(response, 'name="correo"')


class LoginVistaTests(TestCase):
    def setUp(self):
        self.usuario = Usuarios.objects.create(
            nombre='Carlos Pérez',
            documento='1010101010',
            contra='secret123',
            telefono='3101010101',
            correo='carlos@empresa.com',
            cargo='Admin',
            activo=True,
        )

    def test_login_correcto_redirige_al_dashboard(self):
        response = self.client.post(reverse('login'), {
            'correo': 'CARLOS@EMPRESA.COM',
            'clave': 'secret123',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))
        self.assertEqual(
            self.client.session['logueado']['nombre'],
            'Carlos Pérez',
        )
        self.assertEqual(self.client.session['logueado']['rol'], 'Admin')

    def test_login_incorrecto_muestra_error(self):
        response = self.client.post(reverse('login'), {
            'correo': 'carlos@empresa.com',
            'clave': 'incorrecta',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login'))
        self.assertEqual(self.client.session.get('logueado'), None)

    def test_login_correo_no_existe(self):
        response = self.client.post(reverse('login'), {
            'correo': 'nadie@empresa.com',
            'clave': 'secret123',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login'))

    def test_login_usuario_inactivo_rechazado(self):
        self.usuario.activo = False
        self.usuario.save()

        response = self.client.post(reverse('login'), {
            'correo': 'carlos@empresa.com',
            'clave': 'secret123',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login'))

    def test_login_bloquea_despues_de_muchos_intentos_fallidos(self):
        cache.clear()

        for _ in range(5):
            self.client.post(reverse('login'), {
                'correo': 'carlos@empresa.com',
                'clave': 'incorrecta',
            })

        response = self.client.post(reverse('login'), {
            'correo': 'carlos@empresa.com',
            'clave': 'incorrecta',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login'))
        result = self.client.post(reverse('login'), {
            'correo': 'carlos@empresa.com',
            'clave': 'secret123',
        })
        # Incluso con la clave correcta se sigue bloqueado por IP.
        self.assertEqual(result.url, reverse('login'))

        # No deja el contador sucio para los demás tests (cache compartida).
        cache.clear()

    def test_logout_limpia_sesion_y_audita(self):
        self.client.post(reverse('login'), {
            'correo': 'carlos@empresa.com',
            'clave': 'secret123',
        })

        response = self.client.post(reverse('logout'))

        self.assertEqual(response.status_code, 302)
        self.assertNotIn('logueado', self.client.session)
        self.assertTrue(Auditoria.objects.filter(accion='CERRO SESION').exists())


class GestionUsuariosVistaTests(TestCase):
    def setUp(self):
        self.admin = Usuarios.objects.create(
            nombre='Admin',
            documento='2020202020',
            contra='secret123',
            telefono='3102020202',
            correo='admin@empresa.com',
            cargo='Admin',
            activo=True,
        )
        session = self.client.session
        session['logueado'] = {'id': self.admin.id, 'nombre': 'Admin', 'rol': 'Admin'}
        session.save()

    def test_crear_usuario_valido(self):
        response = self.client.post(reverse('crear_usuarios'), {
            'nombre': 'Lucía Gómez',
            'documento': '3030303030',
            'contra': 'ClaveSegura123',
            'telefono': '3103030303',
            'correo': 'lucia@empresa.com',
            'cargo': 'Empleado',
            'activo': 'on',
        })

        self.assertEqual(response.status_code, 302)
        usuario = Usuarios.objects.get(correo='lucia@empresa.com')
        self.assertTrue(usuario.check_password('ClaveSegura123'))
        self.assertTrue(
            Auditoria.objects.filter(modulo='USUARIOS').filter(
                accion__icontains='CREO USUARIO'
            ).exists()
        )

    def test_crear_usuario_con_documento_repetido_no_guarda(self):
        Usuarios.objects.create(
            nombre='Otra Persona',
            documento='4040404040',
            contra='secret123',
            telefono='3104040404',
            correo='otra@empresa.com',
            cargo='Empleado',
            activo=True,
        )

        response = self.client.post(reverse('crear_usuarios'), {
            'nombre': 'Nuevo Usuario',
            'documento': '4040404040',
            'contra': 'ClaveSegura123',
            'telefono': '3105050505',
            'correo': 'nuevo@empresa.com',
            'cargo': 'Empleado',
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Usuarios.objects.filter(correo='nuevo@empresa.com').exists())

    def test_editar_usuario_valido(self):
        empleado = Usuarios.objects.create(
            nombre='Empleado',
            documento='5050505050',
            contra='secret123',
            telefono='3106060606',
            correo='empleado@empresa.com',
            cargo='Empleado',
            activo=True,
        )

        response = self.client.post(reverse('editar_usuarios', args=[empleado.id]), {
            'nombre': 'Empleado Actualizado',
            'documento': '5050505050',
            'telefono': '3106060606',
            'correo': 'empleado@empresa.com',
            'cargo': 'Empleado',
            'activo': 'on',
        })

        self.assertEqual(response.status_code, 302)
        empleado.refresh_from_db()
        self.assertEqual(empleado.nombre, 'Empleado Actualizado')

    def test_admin_no_puede_editar_a_superadmin(self):
        superadmin_principal = Usuarios.objects.create(
            nombre='Principal',
            documento='6060606060',
            contra='secret123',
            telefono='3107070707',
            correo='principal@empresa.com',
            cargo='SuperAdmin',
            activo=True,
            es_superadmin_principal=True,
        )

        response = self.client.post(reverse('editar_usuarios', args=[superadmin_principal.id]), {
            'nombre': 'Hackeado',
            'documento': '6060606060',
            'telefono': '3107070707',
            'correo': 'principal@empresa.com',
            'cargo': 'SuperAdmin',
        })

        self.assertEqual(response.status_code, 302)
        superadmin_principal.refresh_from_db()
        self.assertEqual(superadmin_principal.nombre, 'Principal')

    def test_superadmin_cambia_estado_de_empleado(self):
        superadmin = Usuarios.objects.create(
            nombre='Super',
            documento='7070707070',
            contra='secret123',
            telefono='3108080808',
            correo='super@empresa.com',
            cargo='SuperAdmin',
            activo=True,
        )
        session = self.client.session
        session['logueado'] = {'id': superadmin.id, 'nombre': 'Super', 'rol': 'SuperAdmin'}
        session.save()

        empleado = Usuarios.objects.create(
            nombre='Empleado',
            documento='8080808080',
            contra='secret123',
            telefono='3109090909',
            correo='empleado2@empresa.com',
            cargo='Empleado',
            activo=True,
        )

        response = self.client.post(reverse('cambiar_estado_usuario', args=[empleado.id]))

        self.assertEqual(response.status_code, 302)
        empleado.refresh_from_db()
        self.assertFalse(empleado.activo)
        self.assertTrue(
            Auditoria.objects.filter(modulo='USUARIOS').filter(
                accion__icontains='CAMBIO ESTADO USUARIO'
            ).exists()
        )

    def test_no_puede_desactivarse_a_si_mismo(self):
        response = self.client.post(reverse('cambiar_estado_usuario', args=[self.admin.id]))

        self.assertEqual(response.status_code, 302)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.activo)
