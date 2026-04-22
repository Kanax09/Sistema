from django import forms
from .models import Clientes

from django import forms

class RestoreDBForm(forms.Form):
    backup_file = forms.FileField(label="Selecciona el archivo .sqlite3")


class ClienteRegistrationForm(forms.ModelForm):
    class Meta:
        model = Clientes
        # Incluimos todos los campos definidos en tu modelo Clientes
        fields = ['CI', 'NAME', 'SURNAME', 'DIRECTION', 'BIRTHDATE', 'USERNAME', 'PASSWORD']
        widgets = {
            # PasswordInput oculta los caracteres al escribir
            'PASSWORD': forms.PasswordInput(attrs={'class': 'form-control'}),
            # DateInput con tipo date para mostrar un calendario en el navegador
            'BIRTHDATE': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }