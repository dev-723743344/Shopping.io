from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'brand', 'purchase_price', 'selling_price', 'quantity', 'unit']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent',
                'placeholder': 'Mahsulot nomi'
            }),
            'brand': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent',
                'placeholder': 'Brend'
            }),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent',
                'placeholder': 'Kelgandagi narx',
                'step': '0.01'
            }),
            'selling_price': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent',
                'placeholder': 'Sotuvdagi narx',
                'step': '0.01'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent',
                'placeholder': 'Miqdor',
                'step': '0.01'
            }),
            'unit': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent'
            })
        }
        labels = {
            'name': 'Mahsulot nomi',
            'brand': 'Brend',
            'purchase_price': 'Kelgandagi narx',
            'selling_price': 'Sotuvdagi narx',
            'quantity': 'Miqdor',
            'unit': 'Oʻlchov birligi'
        }

class ExcelImportForm(forms.Form):
    excel_file = forms.FileField(
        label='Excel fayl',
        help_text='Quyidagi ustunlar boʻlgan Excel fayl: Nomi, Brend, Kelgandagi narx, Sotuvdagi narx, Miqdor, Oʻlchov birligi',
        widget=forms.FileInput(attrs={
            'class': 'w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-accent file:text-accent-foreground hover:file:opacity-90',
            'accept': '.xlsx, .xls'
        })
    )
