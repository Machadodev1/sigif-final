from django import forms
from .models import Usuarios


class UsuarioForm(forms.ModelForm):

    nombre = forms.CharField(
        label='Nombre del empleado',
        error_messages={
            'required': 'El nombre del empleado es obligatorio para continuar.'
        },
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej. Juan Pérez, María Gómez...',
            'class': 'form-control',
        }),
    )

    documento = forms.CharField(
        label='Documento de identidad',
        error_messages={
            'required': 'El documento de identidad es obligatorio para continuar.'
        },
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej. 1234567890',
            'class': 'form-control',
            'inputmode': 'numeric',
        }),
    )

    contra = forms.CharField(
        label='Contraseña',
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Mínimo 8 caracteres',
            'class': 'form-control',
        }),
        error_messages={
            'required': 'La contraseña es obligatoria para continuar.',
            'min_length': 'La contraseña debe tener como mínimo 8 caracteres.',
        },
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
        error_messages={
            'required': 'El teléfono es obligatorio para continuar.'
        },
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej. 3001234567',
            'class': 'form-control',
            'inputmode': 'numeric',
        }),
    )

    class Meta:
        model = Usuarios
        # SEGURIDAD: el indicador del SuperAdmin principal nunca se acepta
        # desde HTML ni desde request.POST.
        fields = [
            'nombre', 'documento', 'contra', 'telefono', 'correo',
            'activo', 'fecha_inicio', 'cargo',
        ]

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

        widgets = {
            'fecha_inicio': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                }
            ),
            'cargo': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),
            'activo': forms.CheckboxInput(
                attrs={
                    'class': 'form-check-input'
                }
            ),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()

        # Solo letras y espacios, incluyendo acentos y ñ
        if not all(caracter.isalpha() or caracter.isspace() for caracter in nombre):
            raise forms.ValidationError(
                'El nombre solo puede contener letras y espacios.'
            )

        if not any(caracter.isalpha() for caracter in nombre):
            raise forms.ValidationError(
                'El nombre debe contener al menos una letra.'
            )

        return ' '.join(nombre.split())

    def clean_documento(self):
        documento = self.cleaned_data['documento'].strip()

        if not documento.isdigit():
            raise forms.ValidationError(
                'El documento solo puede contener números.'
            )

        existe = Usuarios.objects.filter(documento=documento).exclude(
            pk=self.instance.pk
        ).exists()

        if existe:
            raise forms.ValidationError(
                'Este documento ya está registrado en el sistema.'
            )

        return documento

    def clean_telefono(self):
        telefono = self.cleaned_data['telefono'].strip()

        if not telefono.isdigit():
            raise forms.ValidationError(
                'El teléfono solo puede contener números.'
            )

        existe = Usuarios.objects.filter(telefono=telefono).exclude(
            pk=self.instance.pk
        ).exists()

        if existe:
            raise forms.ValidationError(
                'Este número de teléfono ya está registrado en el sistema.'
            )

        return telefono

    def clean_correo(self):
        correo = self.cleaned_data['correo'].strip().lower()

        existe = Usuarios.objects.filter(correo=correo).exclude(
            pk=self.instance.pk
        ).exists()

        if existe:
            raise forms.ValidationError(
                'Este correo electrónico ya está registrado en el sistema.'
            )

        return correo