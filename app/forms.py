from django import forms
from bootstrap_datepicker_plus.widgets import DatePickerInput
from .models import TransacaoBancaria


def get_datepicker_widget(attrs=None):
    """
    Retorna um widget DatePickerInput configurado com opções padrão.
    
    Args:
        attrs: Dicionário de atributos HTML adicionais (opcional)
    
    Returns:
        DatePickerInput configurado
    """
    default_attrs = {'class': 'form-control'}
    if attrs:
        default_attrs.update(attrs)
    
    return DatePickerInput(
        attrs=default_attrs,
        options={
            "format": "DD/MM/YYYY",
            "locale": "pt-br",
            "viewMode": "days",
            "calendarWeeks": False,
            "showClose": True,
            "showClear": True,
            "showTodayButton": True,
            "sideBySide": False,
        }
    )


class TransacaoForm(forms.ModelForm):
    """Formulário para criar e editar transações"""
    
    class Meta:
        model = TransacaoBancaria
        fields = ['data', 'valor', 'identificador', 'descricao']
        widgets = {
            'data': get_datepicker_widget(),
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
        widget=get_datepicker_widget()
    )
    data_fim = forms.DateField(
        label='Data Fim',
        required=False,
        widget=get_datepicker_widget()
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

