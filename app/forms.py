from django import forms
from bootstrap_datepicker_plus.widgets import DatePickerInput
from .models import TransacaoBancaria


class TransacaoForm(forms.ModelForm):
    """Formulário para criar e editar transações"""
    
    class Meta:
        model = TransacaoBancaria
        fields = ['data', 'valor', 'identificador', 'descricao']
        widgets = {
            'data': DatePickerInput(
                attrs={'class': 'form-control'},
                options={
                    "format": "DD/MM/YYYY",
                    "locale": "pt-br",
                    "showClose": True,
                    "showClear": True,
                    "showTodayButton": True,
                }
            ),
            'valor': forms.NumberInput(attrs={'class': 'form-control'}),
            'identificador': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'data': 'Data',
            'valor': 'Valor',
            'identificador': 'Identificador (UUID)',
            'descricao': 'Descrição',
        }


class FiltroForm(forms.Form):
    """Formulário para filtros de transações"""
    data_inicio = forms.DateField(
        label='Data Início',
        required=False,
        widget=DatePickerInput(
            attrs={'class': 'form-control'},
            options={
                "format": "DD/MM/YYYY",
                "locale": "pt-br",
                "showClose": True,
                "showClear": True,
                "showTodayButton": True,
            }
        )
    )
    data_fim = forms.DateField(
        label='Data Fim',
        required=False,
        widget=DatePickerInput(
            attrs={'class': 'form-control'},
            options={
                "format": "DD/MM/YYYY",
                "locale": "pt-br",
                "showClose": True,
                "showClear": True,
                "showTodayButton": True,
            }
        )
    )
    movimentacao = forms.ChoiceField(
        label='Movimentação',
        choices=[
            ('todos', 'Todos'),
            ('entradas', 'Entradas'),
            ('saidas', 'Saídas'),
        ],
        required=False,
        initial='todos',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    busca = forms.CharField(
        label='Buscar',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Buscar na descrição...'})
    )

