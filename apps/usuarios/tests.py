from django.test import TestCase
from django.urls import reverse

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
        session = self.client.session
        session['logueado'] = {'id': 1, 'nombre': 'Admin', 'rol': 'Admin'}
        session.save()

        response = self.client.post(reverse('crear_usuarios'), data={})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Falta información obligatoria para crear el usuario.')
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
