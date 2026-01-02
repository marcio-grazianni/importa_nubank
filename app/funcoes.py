"""
Funções genéricas reutilizáveis para o sistema de importação Nubank
"""
import calendar
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Tuple, Optional
from django.db.models import QuerySet
from .models import TransacaoBancaria


def get_datas_padrao_mes() -> Tuple[date, date]:
    """
    Retorna o primeiro e último dia do mês corrente.
    
    Returns:
        Tuple[date, date]: (primeiro_dia, ultimo_dia)
    """
    hoje = date.today()
    primeiro_dia = hoje.replace(day=1)
    ultimo_dia = hoje.replace(day=calendar.monthrange(hoje.year, hoje.month)[1])
    return primeiro_dia, ultimo_dia


def get_data_inicio_padrao() -> str:
    """
    Retorna a data de início padrão (primeiro dia do mês) como string no formato YYYY-MM-DD.
    
    Returns:
        str: Data no formato YYYY-MM-DD
    """
    primeiro_dia, _ = get_datas_padrao_mes()
    return primeiro_dia.strftime('%Y-%m-%d')


def get_data_fim_padrao() -> str:
    """
    Retorna a data de fim padrão (último dia do mês) como string no formato YYYY-MM-DD.
    
    Returns:
        str: Data no formato YYYY-MM-DD
    """
    _, ultimo_dia = get_datas_padrao_mes()
    return ultimo_dia.strftime('%Y-%m-%d')


def parse_data_filtro(data_str: Optional[str], padrao: Optional[str] = None) -> Optional[date]:
    """
    Faz o parse de uma string de data do filtro.
    
    Args:
        data_str: String da data no formato YYYY-MM-DD ou None
        padrao: String de data padrão se data_str for None
    
    Returns:
        date ou None se não conseguir fazer o parse
    """
    if not data_str:
        if padrao:
            data_str = padrao
        else:
            return None
    
    try:
        return datetime.strptime(data_str, '%Y-%m-%d').date()
    except ValueError:
        return None


def aplicar_filtros_transacoes(
    queryset: QuerySet,
    request_get: Dict,
    data_inicio_padrao: Optional[str] = None,
    data_fim_padrao: Optional[str] = None
) -> QuerySet:
    """
    Aplica filtros comuns às transações bancárias.
    
    Args:
        queryset: QuerySet inicial de TransacaoBancaria
        request_get: Dicionário com parâmetros GET da requisição
        data_inicio_padrao: Data de início padrão (se None, usa primeiro dia do mês)
        data_fim_padrao: Data de fim padrão (se None, usa último dia do mês)
    
    Returns:
        QuerySet filtrado
    """
    # Filtro por movimentação
    movimentacao = request_get.get('movimentacao', 'todos')
    if movimentacao == 'entradas':
        queryset = queryset.filter(valor__gt=0)
    elif movimentacao == 'saidas':
        queryset = queryset.filter(valor__lt=0)
    
    # Filtro por data inicial
    if not data_inicio_padrao:
        data_inicio_padrao = get_data_inicio_padrao()
    
    data_inicio = parse_data_filtro(
        request_get.get('data_inicio'),
        padrao=data_inicio_padrao
    )
    if data_inicio:
        queryset = queryset.filter(data__gte=data_inicio)
    
    # Filtro por data final
    if not data_fim_padrao:
        data_fim_padrao = get_data_fim_padrao()
    
    data_fim = parse_data_filtro(
        request_get.get('data_fim'),
        padrao=data_fim_padrao
    )
    if data_fim:
        queryset = queryset.filter(data__lte=data_fim)
    
    # Busca por descrição
    busca = request_get.get('busca')
    if busca:
        queryset = queryset.filter(descricao__icontains=busca)
    
    return queryset


def calcular_estatisticas(queryset: QuerySet) -> Dict[str, Decimal]:
    """
    Calcula estatísticas (entradas, saídas, saldo) de um queryset de transações.
    
    Args:
        queryset: QuerySet de TransacaoBancaria
    
    Returns:
        Dict com 'total_entradas', 'total_saidas' e 'saldo'
    """
    total_entradas = sum(t.valor for t in queryset if t.is_entrada())
    total_saidas = abs(sum(t.valor for t in queryset if t.is_saida()))
    saldo = sum(t.valor for t in queryset)
    
    return {
        'total_entradas': total_entradas,
        'total_saidas': total_saidas,
        'saldo': saldo
    }


def get_initial_data_filtro(request_get: Dict) -> Dict:
    """
    Retorna dados iniciais para o formulário de filtro baseado nos parâmetros GET.
    
    Args:
        request_get: Dicionário com parâmetros GET da requisição
    
    Returns:
        Dict com dados iniciais para FiltroForm
    """
    primeiro_dia, ultimo_dia = get_datas_padrao_mes()
    
    return {
        'data_inicio': request_get.get('data_inicio', primeiro_dia.strftime('%Y-%m-%d')),
        'data_fim': request_get.get('data_fim', ultimo_dia.strftime('%Y-%m-%d')),
        'movimentacao': request_get.get('movimentacao', 'todos'),
        'busca': request_get.get('busca', ''),
    }


def parse_valor_csv(valor_str: str) -> Optional[float]:
    """
    Faz o parse de um valor do CSV, convertendo vírgula para ponto.
    
    Args:
        valor_str: String do valor (pode ter vírgula como separador decimal)
    
    Returns:
        float ou None se não conseguir fazer o parse
    """
    if not valor_str or not valor_str.strip():
        return None
    
    try:
        return float(valor_str.strip().replace(',', '.'))
    except ValueError:
        return None


def parse_data_csv(data_str: str) -> Optional[date]:
    """
    Faz o parse de uma data do CSV no formato DD/MM/YYYY.
    
    Args:
        data_str: String da data no formato DD/MM/YYYY
    
    Returns:
        date ou None se não conseguir fazer o parse
    """
    if not data_str or not data_str.strip():
        return None
    
    try:
        return datetime.strptime(data_str.strip(), '%d/%m/%Y').date()
    except ValueError:
        return None


def validar_linha_csv(row: Dict, row_num: int) -> Tuple[bool, Optional[str]]:
    """
    Valida uma linha do CSV.
    
    Args:
        row: Dicionário com os dados da linha
        row_num: Número da linha (para mensagens de erro)
    
    Returns:
        Tuple[bool, Optional[str]]: (é_válida, mensagem_erro)
    """
    # Validar data
    data_str = row.get('Data', '').strip()
    if not data_str:
        return False, f'Linha {row_num}: Data vazia'
    
    data = parse_data_csv(data_str)
    if not data:
        return False, f'Linha {row_num}: Data inválida: {data_str}'
    
    # Validar valor
    valor_str = row.get('Valor', '').strip()
    if not valor_str:
        return False, f'Linha {row_num}: Valor vazio'
    
    valor = parse_valor_csv(valor_str)
    if valor is None:
        return False, f'Linha {row_num}: Valor inválido: {valor_str}'
    
    # Validar identificador
    identificador = row.get('Identificador', '').strip()
    if not identificador:
        return False, f'Linha {row_num}: Identificador vazio'
    
    # Validar descrição
    descricao = row.get('Descrição', '').strip()
    if not descricao:
        return False, f'Linha {row_num}: Descrição vazia'
    
    return True, None


def processar_linha_csv(row: Dict, row_num: int) -> Tuple[Optional[TransacaoBancaria], Optional[str]]:
    """
    Processa uma linha válida do CSV e retorna uma transação ou erro.
    
    Args:
        row: Dicionário com os dados da linha
        row_num: Número da linha (para mensagens de erro)
    
    Returns:
        Tuple[Optional[TransacaoBancaria], Optional[str]]: 
        - (transacao, None) se criada com sucesso
        - (None, None) se já existe (deve ser ignorada)
        - (None, mensagem_erro) se houver erro
    """
    # Validar linha
    valida, erro = validar_linha_csv(row, row_num)
    if not valida:
        return None, erro
    
    # Verificar se já existe
    identificador = row.get('Identificador', '').strip()
    if TransacaoBancaria.objects.filter(identificador=identificador).exists():
        return None, None  # None indica que deve ser ignorada (já existe)
    
    # Criar transação (já validado, então podemos usar diretamente)
    try:
        transacao = TransacaoBancaria.objects.create(
            identificador=identificador,
            data=parse_data_csv(row.get('Data', '').strip()),
            valor=parse_valor_csv(row.get('Valor', '').strip()),
            descricao=row.get('Descrição', '').strip(),
        )
        return transacao, None
    except Exception as e:
        return None, f'Linha {row_num}: Erro ao processar - {str(e)}'

