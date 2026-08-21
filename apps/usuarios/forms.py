from django import forms

from .models import Usuarios


class UsuarioForm(forms.ModelForm):
    nombre = forms.CharField(label='Nombre del empleado')
    correo = forms.EmailField(label='Correo electrónico')

    class Meta:
        model = Usuarios
        fields = '__all__'
        labels = {
            'nombre': 'Nombre del empleado',
            'contra': 'Contraseña',
            'telefono': 'Teléfono',
            'correo': 'Correo electrónico',
            'activo': 'Activo',
            'fecha_inicio': 'Fecha de inicio',
            'cargo': 'Cargo',
        }
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'contra': forms.PasswordInput(render_value=True),
            'correo': forms.EmailInput(attrs={'placeholder': 'correo@empresa.com'}),
        }

    def clean_nombre(self):
        return self.cleaned_data['nombre'].strip()

    def clean_correo(self):
        return self.cleaned_data['correo'].strip().lower()