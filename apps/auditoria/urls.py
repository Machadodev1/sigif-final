from django.urls import path
from . import views

urlpatterns = [
    path("", views.auditoria, name="auditoria"),

    path(
        "exportar/excel/",
        views.exportar_excel,
        name="exportar_excel"
    ),

    path(
        "exportar/pdf/",
        views.exportar_pdf,
        name="exportar_pdf"
    ),
]