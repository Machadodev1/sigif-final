from rest_framework import viewsets
from rest_framework.authentication import *
from rest_framework.permissions import *
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.throttling import ScopedRateThrottle

from apps.auditoria.models import Auditoria
from apps.configuracion.models import EmpresaConfig
from apps.facturacion.models import Cliente, Factura
from apps.productos.models import Producto
from apps.usuarios.models import Usuarios
from rest_framework.decorators import action
from rest_framework.response import Response
from .authentication import *
from .permissions import RolApiPermission, ProductoLecturaPublica

from .serializador import (
    AuditoriaSerializer,
    ClienteSerializer,
    EmpresaConfigSerializer,
    FacturaSerializer,
    ProductoSerializer,
    UsuarioSerializer,
)


class AuditoriaViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [RolApiPermission]
    queryset = Auditoria.objects.all().order_by('-id')
    serializer_class = AuditoriaSerializer

    def get_modulo(self):
        return "AUDITORIA"

    def _get_usuario(self):
        return self.request.session.get("logueado", {}).get("nombre", "Usuario API")

    def perform_create(self, serializer):
        serializer.save()
        Auditoria.objects.create(
            usuario=self._get_usuario(),
            accion=f"CREÓ REGISTRO DE AUDITORÍA: {serializer.instance}",
            modulo=self.get_modulo()
        )

    def perform_update(self, serializer):
        serializer.save()
        Auditoria.objects.create(
            usuario=self._get_usuario(),
            accion=f"ACTUALIZÓ REGISTRO DE AUDITORÍA: {serializer.instance}",
            modulo=self.get_modulo()
        )

    def perform_destroy(self, instance):
        Auditoria.objects.create(
            usuario=self._get_usuario(),
            accion=f"ELIMINÓ REGISTRO DE AUDITORÍA: {instance}",
            modulo=self.get_modulo()
        )
        instance.delete()

    @action(detail=False, methods=['get'])
    def recientes(self, request):
        auditorias = Auditoria.objects.order_by('-fecha')[:5]
        serializer = self.get_serializer(auditorias, many=True)
        return Response(serializer.data)


class EmpresaConfigViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [RolApiPermission]
    queryset = EmpresaConfig.objects.all().order_by('-id')
    serializer_class = EmpresaConfigSerializer

    def get_modulo(self):
        return "CONFIGURACION"

    def _get_usuario(self):
        return self.request.session.get("logueado", {}).get("nombre", "Usuario API")

    def perform_create(self, serializer):
        serializer.save()
        Auditoria.objects.create(
            usuario=self._get_usuario(),
            accion=f"CREÓ CONFIGURACIÓN DE EMPRESA: {serializer.instance.nombre_comercial}",
            modulo=self.get_modulo()
        )

    def perform_update(self, serializer):
        serializer.save()
        Auditoria.objects.create(
            usuario=self._get_usuario(),
            accion=f"ACTUALIZÓ CONFIGURACIÓN DE EMPRESA: {serializer.instance.nombre_comercial}",
            modulo=self.get_modulo()
        )

    def perform_destroy(self, instance):
        nombre = instance.nombre_comercial
        Auditoria.objects.create(
            usuario=self._get_usuario(),
            accion=f"ELIMINÓ CONFIGURACIÓN DE EMPRESA: {nombre}",
            modulo=self.get_modulo()
        )
        instance.delete()


class ClienteViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [RolApiPermission]
    queryset = Cliente.objects.all().order_by('-id')
    serializer_class = ClienteSerializer

    def get_modulo(self):
        return "FACTURACION"

    def _get_usuario(self):
        return self.request.session.get("logueado", {}).get("nombre", "Usuario API")

    def perform_create(self, serializer):
        serializer.save()
        Auditoria.objects.create(
            usuario=self._get_usuario(),
            accion=f"CREÓ CLIENTE: {serializer.instance.nombre}",
            modulo=self.get_modulo()
        )

    def perform_update(self, serializer):
        serializer.save()
        Auditoria.objects.create(
            usuario=self._get_usuario(),
            accion=f"ACTUALIZÓ CLIENTE: {serializer.instance.nombre}",
            modulo=self.get_modulo()
        )

    def perform_destroy(self, instance):
        nombre = instance.nombre
        Auditoria.objects.create(
            usuario=self._get_usuario(),
            accion=f"ELIMINÓ CLIENTE: {nombre}",
            modulo=self.get_modulo()
        )
        instance.delete()


class FacturaViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [RolApiPermission]
    queryset = Factura.objects.all().order_by('-id')
    serializer_class = FacturaSerializer

    def get_modulo(self):
        return "FACTURACION"

    def _get_usuario(self):
        return self.request.session.get("logueado", {}).get("nombre", "Usuario API")

    def perform_create(self, serializer):
        serializer.save()
        Auditoria.objects.create(
            usuario=self._get_usuario(),
            accion=f"CREÓ FACTURA #{serializer.instance.id} - CLIENTE: {serializer.instance.cliente.nombre} - TOTAL: {serializer.instance.total}",
            modulo=self.get_modulo()
        )

    def perform_update(self, serializer):
        serializer.save()
        Auditoria.objects.create(
            usuario=self._get_usuario(),
            accion=f"ACTUALIZÓ FACTURA #{serializer.instance.id} - CLIENTE: {serializer.instance.cliente.nombre}",
            modulo=self.get_modulo()
        )

    def perform_destroy(self, instance):
        cliente_nombre = instance.cliente.nombre
        factura_id = instance.id
        Auditoria.objects.create(
            usuario=self._get_usuario(),
            accion=f"ELIMINÓ FACTURA #{factura_id} - CLIENTE: {cliente_nombre}",
            modulo=self.get_modulo()
        )
        instance.delete()


class ProductoViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [ProductoLecturaPublica]
    queryset = Producto.objects.all().order_by('-id')
    serializer_class = ProductoSerializer

    def get_modulo(self):
        return "PRODUCTOS"

    def _get_usuario(self):
        return self.request.session.get("logueado", {}).get("nombre", "Usuario API")

    def perform_create(self, serializer):
        serializer.save()
        Auditoria.objects.create(
            usuario=self._get_usuario(),
            accion=f"CREÓ PRODUCTO: {serializer.instance.nombre}",
            modulo=self.get_modulo()
        )

    def perform_update(self, serializer):
        serializer.save()
        Auditoria.objects.create(
            usuario=self._get_usuario(),
            accion=f"ACTUALIZÓ PRODUCTO: {serializer.instance.nombre}",
            modulo=self.get_modulo()
        )

    def perform_destroy(self, instance):
        nombre = instance.nombre
        Auditoria.objects.create(
            usuario=self._get_usuario(),
            accion=f"ELIMINÓ PRODUCTO: {nombre}",
            modulo=self.get_modulo()
        )
        instance.delete()

    @action(detail=False, methods=['get'])
    def bajo_stock(self, request):
        productos = Producto.objects.filter(stock__lt=5)
        serializer = self.get_serializer(productos, many=True)
        return Response(serializer.data)


class UsuarioViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [RolApiPermission]
    queryset = Usuarios.objects.all().order_by('-id')
    serializer_class = UsuarioSerializer

    def get_modulo(self):
        return "USUARIOS"

    def _get_usuario(self):
        return self.request.session.get("logueado", {}).get("nombre", "Usuario API")

    def _actor(self):
        from apps.usuarios.models import Usuarios
        session_user = self.request.session.get('logueado') or {}
        return Usuarios.objects.filter(
            pk=session_user.get('id'), activo=True
        ).first()

    def perform_create(self, serializer):
        actor = self._actor()
        if not actor or actor.cargo not in ('Admin', 'SuperAdmin'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('No tienes permiso para crear usuarios.')
        if serializer.validated_data.get('cargo') == 'SuperAdmin' and actor.cargo != 'SuperAdmin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Solo un SuperAdmin puede asignar ese rol.')
        serializer.save()
        Auditoria.objects.create(
            usuario=self._get_usuario(),
            accion=f"CREÓ USUARIO: {serializer.instance.nombre}",
            modulo=self.get_modulo()
        )

    def perform_update(self, serializer):
        actor = self._actor()
        target = self.get_object()
        if not actor or actor.cargo not in ('Admin', 'SuperAdmin'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('No tienes permiso para modificar usuarios.')
        if target.es_superadmin_principal and target.id != actor.id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('El SuperAdmin principal está protegido.')
        if actor.cargo == 'Admin' and (
            target.cargo == 'SuperAdmin'
            or (target.cargo == 'Admin' and target.id != actor.id)
        ):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('No tienes permiso para modificar ese usuario.')
        serializer.save(cargo=target.cargo, activo=target.activo)
        Auditoria.objects.create(
            usuario=self._get_usuario(),
            accion=f"ACTUALIZÓ USUARIO: {serializer.instance.nombre}",
            modulo=self.get_modulo()
        )

    def perform_destroy(self, instance):
        nombre = instance.nombre
        Auditoria.objects.create(
            usuario=self._get_usuario(),
            accion=f"ELIMINÓ USUARIO: {nombre}",
            modulo=self.get_modulo()
        )
        instance.delete()

    @action(detail=False, methods=['get'])
    def activos(self, request):
        usuarios = Usuarios.objects.filter(activo=True)
        serializer = self.get_serializer(usuarios, many=True)
        return Response(serializer.data)

class LoginTokenView(ObtainAuthToken):
    """Obtiene un token de API con límite de intentos (anti brute-force)."""
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]


    def post(self, request):
        # Elimina el token asociado al usuario de la petición
        request.user.auth_token.delete()
        return Response(
            {"message": "Sesión cerrada correctamente. Token destruido."}, 
            status=status.HTTP_200_OK
        )