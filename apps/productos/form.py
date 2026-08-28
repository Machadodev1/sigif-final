from django import forms
from .models import Producto


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'categoria', 'precio', 'stock', 'descripcion', 'activo']
        labels = {
            'nombre': 'Nombre del producto',
            'categoria': 'Categoría',
            'precio': 'Precio unitario ($)',
            'stock': 'Stock disponible (unidades)',
            'descripcion': 'Descripción del producto',
            'activo': 'Producto activo para ventas',
        }
        error_messages = {
            'nombre': {'required': 'El nombre del producto es obligatorio.'},
            'categoria': {'required': 'La categoría es obligatoria.'},
            'precio': {'required': 'El precio es obligatorio.'},
            'stock': {'required': 'El stock es obligatorio.'},
        }
        widgets = {
            'nombre': forms.TextInput(attrs={
                'placeholder': 'Ej. Martillo de acero, Aceite 10W-40...',
                'class': 'form-control',
            }),
            'categoria': forms.TextInput(attrs={
                'placeholder': 'Ej. Herramientas, Repuestos, General...',
                'class': 'form-control',
            }),
            'precio': forms.NumberInput(attrs={
                'placeholder': 'Ej. 25000',
                'min': '1',
                'step': '1',
                'class': 'form-control',
            }),
            'stock': forms.NumberInput(attrs={
                'placeholder': 'Ej. 50',
                'min': '0',
                'step': '1',
                'class': 'form-control',
            }),
            'descripcion': forms.Textarea(attrs={
                'placeholder': 'Escribe una descripción breve o especificaciones del producto...',
                'rows': 3,
                'class': 'form-control',
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
