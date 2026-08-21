from django import forms

from .models import Usuarios


class UsuarioForm(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre del empleado',
        error_messages={'required': 'El nombre del empleado es obligatorio para continuar.'},
    )
    contra = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(render_value=True),
        error_messages={'required': 'La contraseña es obligatoria para continuar.'},
    )
    correo = forms.EmailField(
        label='Correo electrónico',
        error_messages={
            'required': 'El correo electrónico es obligatorio para continuar.',
            'invalid': 'Ingresa un correo electrónico válido.',
        },
    )

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
        error_messages = {
            'nombre': {'required': 'El nombre del empleado es obligatorio para continuar.'},
            'contra': {'required': 'La contraseña es obligatoria para continuar.'},
            'telefono': {'required': 'El teléfono es obligatorio para continuar.'},
            'correo': {
                'required': 'El correo electrónico es obligatorio para continuar.',
                'unique': 'Este correo ya está registrado en el sistema.',
            },
            'cargo': {'required': 'El cargo es obligatorio para continuar.'},
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