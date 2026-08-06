from rest_framework import viewsets
from rest_framework.authentication import *
from rest_framework.permissions import *
from apps.auditoria.models import Auditoria
from apps.configuracion.models import EmpresaConfig
from apps.facturacion.models import Cliente, Factura
from apps.productos.models import Producto
from apps.usuarios.models import Usuarios
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializador import (
    AuditoriaSerializer,
    ClienteSerializer,
    EmpresaConfigSerializer,
    FacturaSerializer,
    ProductoSerializer,
    UsuarioSerializer,
)


class AuditoriaViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Auditoria.objects.all().order_by('-id')
    serializer_class = AuditoriaSerializer
    @action(detail=False, methods=['get'])
    def recientes(self, request):
        auditorias = Auditoria.objects.order_by('-fecha')[:10]
        serializer = self.get_serializer(auditorias, many=True)
        return Response(serializer.data)


class EmpresaConfigViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = EmpresaConfig.objects.all().order_by('-id')
    serializer_class = EmpresaConfigSerializer


class ClienteViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Cliente.objects.all().order_by('-id')
    serializer_class = ClienteSerializer


class FacturaViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Factura.objects.all().order_by('-id')
    serializer_class = FacturaSerializer


class ProductoViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]
    queryset = Producto.objects.all().order_by('-id')
    serializer_class = ProductoSerializer
    @action(detail=False, methods=['get'])
    def bajo_stock(self, request):
        productos = Producto.objects.filter(stock__lt=5)
        serializer = self.get_serializer(productos, many=True)
        return Response(serializer.data)


class UsuarioViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Usuarios.objects.all().order_by('-id')
    serializer_class = UsuarioSerializer
    @action(detail=False, methods=['get'])
    def activos(self, request):
        usuarios = Usuarios.objects.filter(is_active=True)
        serializer = self.get_serializer(usuarios, many=True)
        return Response(serializer.data)
