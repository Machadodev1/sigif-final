from django import forms
from .models import Producto, CATEGORIAS

CATEGORIA_CHOICES = [
    ('', 'Seleccione una categoría...'),
] + CATEGORIAS


class ProductoForm(forms.ModelForm):
    categoria = forms.ChoiceField(
        choices=CATEGORIA_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='Categoría',
        error_messages={'required': 'La categoría es obligatoria.'}
    )

    class Meta:
        model = Producto
        fields = ['nombre', 'categoria', 'precio', 'stock', 'descripcion']
        labels = {
            'nombre': 'Nombre del producto',
            'categoria': 'Categoría',
            'precio': 'Precio unitario ($)',
            'stock': 'Stock disponible (unidades)',
            'descripcion': 'Descripción del producto',
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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if 'stock' in self.fields:
                self.fields['stock'].required = False
            if self.instance.categoria:
                valores_existentes = [c[0] for c in self.fields['categoria'].choices]
                if self.instance.categoria not in valores_existentes:
                    self.fields['categoria'].choices = [
                        ('', 'Seleccione una categoría...'),
                        (self.instance.categoria, f"{self.instance.categoria} (Actual)"),
                    ] + list(CATEGORIAS)

    def clean_stock(self):
        if self.instance and self.instance.pk:
            return self.instance.stock
        stock = self.cleaned_data.get('stock')
        if stock is None:
            raise forms.ValidationError('El stock es obligatorio.')
        return stock

