from rest_framework import viewsets

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
    queryset = Auditoria.objects.all().order_by('-id')
    serializer_class = AuditoriaSerializer


class EmpresaConfigViewSet(viewsets.ModelViewSet):
    queryset = EmpresaConfig.objects.all().order_by('-id')
    serializer_class = EmpresaConfigSerializer


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all().order_by('-id')
    serializer_class = ClienteSerializer


class FacturaViewSet(viewsets.ModelViewSet):
    queryset = Factura.objects.all().order_by('-id')
    serializer_class = FacturaSerializer


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all().order_by('-id')
    serializer_class = ProductoSerializer


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuarios.objects.all().order_by('-id')
    serializer_class = UsuarioSerializer
