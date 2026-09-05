from rest_framework import viewsets
from rest_framework.authentication import *
from rest_framework.permissions import *
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.views import APIView

from apps.auditoria.models import Auditoria
from apps.configuracion.models import EmpresaConfig
from apps.facturacion.models import Cliente, Factura
from apps.productos.models import Producto
from apps.usuarios.models import Usuarios
from rest_framework.decorators import action
from rest_framework.response import Response
from .authentication import *

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
    permission_classes = [IsAuthenticated]
    queryset = Auditoria.objects.all().order_by('-id')
    serializer_class = AuditoriaSerializer
    @action(detail=False, methods=['get'])
    def recientes(self, request):
        auditorias = Auditoria.objects.order_by('-fecha')[:5]
        serializer = self.get_serializer(auditorias, many=True)
        return Response(serializer.data)


class EmpresaConfigViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = EmpresaConfig.objects.all().order_by('-id')
    serializer_class = EmpresaConfigSerializer


class ClienteViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Cliente.objects.all().order_by('-id')
    serializer_class = ClienteSerializer


class FacturaViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Factura.objects.all().order_by('-id')
    serializer_class = FacturaSerializer


class ProductoViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    queryset = Producto.objects.all().order_by('-id')
    serializer_class = ProductoSerializer
    @action(detail=False, methods=['get'])
    def bajo_stock(self, request):
        productos = Producto.objects.filter(stock__lt=5)
        serializer = self.get_serializer(productos, many=True)
        return Response(serializer.data)


class UsuarioViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Usuarios.objects.all().order_by('-id')
    serializer_class = UsuarioSerializer

    def perform_create(self, serializer):
        actor = self._actor()
        if not actor or actor.cargo not in ('Admin', 'SuperAdmin'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('No tienes permiso para crear usuarios.')
        if serializer.validated_data.get('cargo') == 'SuperAdmin' and actor.cargo != 'SuperAdmin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Solo un SuperAdmin puede asignar ese rol.')
        serializer.save()

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

    def _actor(self):
        from apps.usuarios.models import Usuarios
        session_user = self.request.session.get('logueado') or {}
        return Usuarios.objects.filter(
            pk=session_user.get('id'), activo=True
        ).first()
    @action(detail=False, methods=['get'])
    def activos(self, request):
        usuarios = Usuarios.objects.filter(activo=True)
        serializer = self.get_serializer(usuarios, many=True)
        return Response(serializer.data)

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