from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('usuarios/', views.usuarios, name='usuarios'),
    path('crear_usuarios/', views.crear_usuarios, name='crear_usuarios'),
    path('editar_usuarios/<int:id>/', views.editar_usuarios, name='editar_usuarios'),
    # path('eliminar_usuario/<int:id>/', views.eliminar_usuario, name='eliminar_usuario'),
    path("cambiar_estado_usuario/<int:id>/", views.cambiar_estado_usuario, name="cambiar_estado_usuario"),
]
