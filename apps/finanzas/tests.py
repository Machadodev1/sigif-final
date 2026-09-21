from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.facturacion.models import Cliente, Factura
from apps.productos.models import Producto
from apps.usuarios.models import Usuarios

from .models import Gasto


def _loguear(client, usuario):
    session = client.session
    session['logueado'] = {'id': usuario.id, 'nombre': usuario.nombre, 'rol': usuario.cargo}
    session.save()


class RegistrarGastoTests(TestCase):
    """Validación server-side del registro/edición de gastos operativos."""

    def setUp(self):
        self.admin = Usuarios.objects.create(
            nombre='Admin',
            documento='44444444',
            contra='secret123',
            telefono='3001112233',
            correo='admin@empresa.com',
            cargo='Admin',
            activo=True,
        )
        session = self.client.session
        session['logueado'] = {'id': self.admin.id, 'nombre': 'Admin', 'rol': 'Admin'}
        session.save()

    def _post_gasto(self, **overrides):
        datos = {
            'concepto': 'Arriendo local',
            'categoria': 'ARRIENDO',
            'fecha': '2026-09-01',
            'metodo_pago': 'EFECTIVO',
            'proveedor': 'Proveedor SA',
            'descripcion': 'Pago mensual',
            'valor': '1500000',
        }
        datos.update(overrides)
        return self.client.post(reverse('finanzas:nuevo_gasto'), datos)

    def test_gasto_valido_se_registra(self):
        response = self._post_gasto()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Gasto.objects.count(), 1)
        gasto = Gasto.objects.get()
        self.assertEqual(gasto.valor, Decimal('1500000'))
        self.assertEqual(gasto.categoria, 'ARRIENDO')
        self.assertEqual(gasto.metodo_pago, 'EFECTIVO')

    def test_concepto_vacio_no_se_registra(self):
        self._post_gasto(concepto='   ')
        self.assertEqual(Gasto.objects.count(), 0)

    def test_valor_cero_no_se_registra(self):
        self._post_gasto(valor='0')
        self.assertEqual(Gasto.objects.count(), 0)

    def test_valor_negativo_no_se_registra(self):
        self._post_gasto(valor='-500')
        self.assertEqual(Gasto.objects.count(), 0)

    def test_valor_demasiado_grande_no_se_registra(self):
        self._post_gasto(valor='100000000000000')
        self.assertEqual(Gasto.objects.count(), 0)

    def test_fecha_invalida_no_se_registra(self):
        self._post_gasto(fecha='fecha-no-valida')
        self.assertEqual(Gasto.objects.count(), 0)

    def test_concepto_largo_se_trunca(self):
        self._post_gasto(concepto='x' * 300)
        self.assertEqual(Gasto.objects.count(), 1)
        self.assertLessEqual(len(Gasto.objects.get().concepto), 150)

    def test_concepto_con_html_se_sanea(self):
        self._post_gasto(concepto='<script>alert(1)</script>Compra')
        self.assertEqual(Gasto.objects.count(), 1)
        self.assertNotIn('<', Gasto.objects.get().concepto)
        self.assertNotIn('>', Gasto.objects.get().concepto)

    def test_categoria_via_post_se_origina_correos(self):
        # POST con categoría no lista debe caer a la primera válida.
        self._post_gasto(categoria='NO_EXISTE')
        self.assertEqual(Gasto.objects.count(), 1)
        self.assertIn(Gasto.objects.get().categoria, [c[0] for c in Gasto.CATEGORIAS])


class FinanzasVistasTests(TestCase):
    """Vistas del estado de resultados y reportes financieros."""

    def setUp(self):
        self.admin = Usuarios.objects.create(
            nombre='Admin',
            documento='55555555',
            contra='secret123',
            telefono='3001112232',
            correo='finanzas@empresa.com',
            cargo='Admin',
            activo=True,
        )
        _loguear(self.client, self.admin)

        self.producto = Producto.objects.create(
            nombre='Filtro', precio=25000, stock=10, categoria='Filtros'
        )
        self.cliente = Cliente.objects.create(
            nombre='Cliente A', correo='clientea@empresa.com'
        )
        self.factura = Factura.objects.create(
            cliente=self.cliente,
            total=Decimal('50000'),
            metodo_pago='EFECTIVO',
            valor_pagado=Decimal('50000'),
        )
        Gasto.objects.create(
            concepto='Arriendo local',
            categoria='ARRIENDO',
            valor=Decimal('1500000'),
            fecha='2026-09-01',
            metodo_pago='EFECTIVO',
            proveedor='Proveedor SA',
            descripcion='Pago mensual',
            usuario='Admin',
        )

    def test_dashboard_financiero(self):
        response = self.client.get(reverse('finanzas:finanzas_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_ventas_por_categoria(self):
        response = self.client.get(reverse('finanzas:ventas_categoria'))
        self.assertEqual(response.status_code, 200)

    def test_historial_gastos(self):
        response = self.client.get(reverse('finanzas:gastos'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Arriendo local')

    def test_rentabilidad(self):
        response = self.client.get(reverse('finanzas:rentabilidad'))
        self.assertEqual(response.status_code, 200)

    def test_caja_conciliacion(self):
        response = self.client.get(reverse('finanzas:caja_conciliacion'))
        self.assertEqual(response.status_code, 200)

    def test_reportes_caja(self):
        response = self.client.get(reverse('finanzas:reportes'))
        self.assertEqual(response.status_code, 200)

    def test_ingresos(self):
        response = self.client.get(reverse('finanzas:ingresos'))
        self.assertEqual(response.status_code, 200)


class FinanzasAccesoTests(TestCase):
    """Un Empleado no puede registrar gastos ni ver reportes financieros."""

    def setUp(self):
        self.empleado = Usuarios.objects.create(
            nombre='Empleado',
            documento='66666666',
            contra='secret123',
            telefono='3001112231',
            correo='empleado@finanzas.com',
            cargo='Empleado',
            activo=True,
        )
        _loguear(self.client, self.empleado)

    def test_empleado_no_ve_dashboard_financiero(self):
        response = self.client.get(reverse('finanzas:finanzas_dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_empleado_no_registra_gastos(self):
        response = self.client.post(reverse('finanzas:nuevo_gasto'), {
            'concepto': 'Arriendo',
            'categoria': 'ARRIENDO',
            'fecha': '2026-09-01',
            'metodo_pago': 'EFECTIVO',
            'valor': '100000',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Gasto.objects.count(), 0)