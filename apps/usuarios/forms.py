from django import forms
from .models import Usuarios


class UsuarioForm(forms.ModelForm):
    nombre = forms.CharField(
        label='Nombre del empleado',
        error_messages={'required': 'El nombre del empleado es obligatorio para continuar.'},
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej. Juan Pérez, María Gómez...',
            'class': 'form-control',
        }),
    )
    documento = forms.CharField(
        label='Documento de identidad',
        error_messages={'required': 'El documento de identidad es obligatorio para continuar.'},
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej. 1234567890',
            'class': 'form-control',
        }),
    )
    contra = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(render_value=True, attrs={
            'placeholder': '••••••••',
            'class': 'form-control',
        }),
        error_messages={'required': 'La contraseña es obligatoria para continuar.'},
    )
    correo = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={
            'placeholder': 'correo@empresa.com',
            'class': 'form-control',
        }),
        error_messages={
            'required': 'El correo electrónico es obligatorio para continuar.',
            'invalid': 'Ingresa un correo electrónico válido.',
        },
    )
    telefono = forms.CharField(
        label='Teléfono de contacto',
        required=True,
        error_messages={'required': 'El teléfono es obligatorio para continuar.'},
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej. 3001234567',
            'class': 'form-control',
        }),
    )

    class Meta:
        model = Usuarios
        fields = ['nombre', 'documento', 'correo', 'contra', 'telefono', 'cargo', 'fecha_inicio', 'activo']
        labels = {
            'nombre': 'Nombre del empleado',
            'documento': 'Documento de identidad',
            'contra': 'Contraseña',
            'telefono': 'Teléfono de contacto',
            'correo': 'Correo electrónico',
            'activo': 'Usuario activo en el sistema',
            'fecha_inicio': 'Fecha de inicio / Contratación',
            'cargo': 'Rol / Cargo en el sistema',
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
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'cargo': forms.Select(attrs={'class': 'form-select'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_nombre(self):
        return self.cleaned_data['nombre'].strip()

    def clean_correo(self):
        return self.cleaned_data['correo'].strip().lower()