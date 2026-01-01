from django import template

register = template.Library()


def formatar_valor_moeda(value, incluir_simbolo=True):
    """
    Formata um valor numérico como moeda brasileira com separador de milhar.
    
    Args:
        value: Valor numérico a ser formatado
        incluir_simbolo: Se True, inclui o símbolo R$ no início
    
    Returns:
        String formatada (ex: "R$ 1.234,56" ou "1.234,56")
    """
    if value is None:
        return 'R$ 0,00' if incluir_simbolo else '0,00'
    
    try:
        # Converter para float se necessário
        valor = float(value)
        
        # Formatar com separador de milhar e 2 casas decimais
        # Usar vírgula para decimais e ponto para milhar
        valor_formatado = f'{valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        
        if incluir_simbolo:
            return f'R$ {valor_formatado}'
        else:
            return valor_formatado
    except (ValueError, TypeError):
        if incluir_simbolo:
            return f'R$ {value}'
        else:
            return str(value)


@register.filter(name='currency')
def currency(value):
    """
    Formata um valor numérico como moeda brasileira com separador de milhar.
    Exemplo: 1234.56 -> R$ 1.234,56
    """
    return formatar_valor_moeda(value, incluir_simbolo=True)


@register.filter(name='currency_value')
def currency_value(value):
    """
    Formata apenas o valor numérico com separador de milhar (sem o R$).
    Exemplo: 1234.56 -> 1.234,56
    """
    return formatar_valor_moeda(value, incluir_simbolo=False)


@register.simple_tag(takes_context=True)
def url_with_order(context, field):
    """
    Gera URL com parâmetro de ordenação, mantendo outros parâmetros da query string.
    Se o campo já estiver ordenado, inverte a ordem.
    """
    request = context['request']
    params = request.GET.copy()
    current_order = params.get('order_by', '-data')
    
    # Se já está ordenando por este campo, inverte a ordem
    if current_order == field:
        # Se está ascendente, muda para descendente
        new_order = f'-{field}'
    elif current_order == f'-{field}':
        # Se está descendente, muda para ascendente
        new_order = field
    else:
        # Novo campo, começa com descendente
        new_order = f'-{field}'
    
    params['order_by'] = new_order
    return params.urlencode()

