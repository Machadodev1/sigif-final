from rest_framework import viewsets
from rest_framework.authentication import *
from rest_framework.permissions import *
from apps.auditoria.models import Auditoria
from apps.configuracion.models import EmpresaConfig
from apps.facturacion.models import Cliente, Factura
from apps.productos.models import Producto
from apps.usuarios.models import Usuarios

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


class UsuarioViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Usuarios.objects.all().order_by('-id')
    serializer_class = UsuarioSerializer
