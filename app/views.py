import csv
import calendar
from datetime import datetime, date
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.urls import reverse_lazy
from django.db import transaction
from django.db.models import Sum, Count
from .models import TransacaoBancaria
from .forms import TransacaoForm, FiltroForm


def upload_csv(request):
    """View para upload e importação de arquivo CSV"""
    if request.method == 'POST':
        if 'csv_file' not in request.FILES:
            messages.error(request, 'Por favor, selecione um arquivo CSV.')
            return redirect('app:transacao_upload')
        
        csv_file = request.FILES['csv_file']
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'O arquivo deve ser um CSV.')
            return redirect('app:transacao_upload')
        
        try:
            # Decodificar o arquivo
            decoded_file = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(decoded_file.splitlines())
            
            transacoes_criadas = 0
            transacoes_ignoradas = 0
            erros = []
            
            with transaction.atomic():
                for row_num, row in enumerate(csv_reader, start=2):
                    try:
                        # Parse da data (formato DD/MM/YYYY)
                        data_str = row.get('Data', '').strip()
                        if not data_str:
                            erros.append(f'Linha {row_num}: Data vazia')
                            continue
                        
                        try:
                            data = datetime.strptime(data_str, '%d/%m/%Y').date()
                        except ValueError:
                            erros.append(f'Linha {row_num}: Data inválida: {data_str}')
                            continue
                        
                        # Parse do valor
                        valor_str = row.get('Valor', '').strip()
                        if not valor_str:
                            erros.append(f'Linha {row_num}: Valor vazio')
                            continue
                        
                        try:
                            valor = float(valor_str.replace(',', '.'))
                        except ValueError:
                            erros.append(f'Linha {row_num}: Valor inválido: {valor_str}')
                            continue
                        
                        # Identificador
                        identificador = row.get('Identificador', '').strip()
                        if not identificador:
                            erros.append(f'Linha {row_num}: Identificador vazio')
                            continue
                        
                        # Descrição
                        descricao = row.get('Descrição', '').strip()
                        if not descricao:
                            erros.append(f'Linha {row_num}: Descrição vazia')
                            continue
                        
                        # Verificar se o identificador já existe (evitar duplicatas)
                        if TransacaoBancaria.objects.filter(identificador=identificador).exists():
                            transacoes_ignoradas += 1
                            continue
                        
                        # Criar nova transação
                        TransacaoBancaria.objects.create(
                            identificador=identificador,
                            data=data,
                            valor=valor,
                            descricao=descricao,
                        )
                        
                        transacoes_criadas += 1
                    
                    except Exception as e:
                        erros.append(f'Linha {row_num}: Erro ao processar - {str(e)}')
                        continue
            
            # Mensagens de resultado
            if transacoes_criadas > 0:
                messages.success(
                    request,
                    f'{transacoes_criadas} transação(ões) criada(s) com sucesso!'
                )
            
            if transacoes_ignoradas > 0:
                messages.info(
                    request,
                    f'{transacoes_ignoradas} transação(ões) ignorada(s) (já existiam no banco de dados).'
                )
            
            if erros:
                messages.warning(
                    request,
                    f'{len(erros)} erro(s) encontrado(s) durante a importação.'
                )
                # Mostrar primeiros 5 erros
                for erro in erros[:5]:
                    messages.warning(request, erro)
                if len(erros) > 5:
                    messages.warning(request, f'... e mais {len(erros) - 5} erro(s)')
            
            return redirect('app:transacao_list')
        
        except Exception as e:
            messages.error(request, f'Erro ao processar arquivo CSV: {str(e)}')
            return redirect('app:transacao_upload')
    
    return render(request, 'app/upload_csv.html')


class TransacaoListView(ListView):
    """View para listar todas as transações"""
    model = TransacaoBancaria
    template_name = 'app/transacao_list.html'
    context_object_name = 'transacoes'
    paginate_by = 100
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtro por movimentação (padrão: 'todos')
        movimentacao = self.request.GET.get('movimentacao', 'todos')
        if movimentacao == 'entradas':
            queryset = queryset.filter(valor__gt=0)
        elif movimentacao == 'saidas':
            queryset = queryset.filter(valor__lt=0)
        # Se for 'todos', não aplica filtro
        
        # Filtro por data inicial (usa padrão se não fornecido)
        data_inicio = self.request.GET.get('data_inicio')
        if not data_inicio:
            # Se não foi fornecido, usar primeiro dia do mês corrente
            hoje = date.today()
            data_inicio = hoje.replace(day=1).strftime('%Y-%m-%d')
        
        try:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            queryset = queryset.filter(data__gte=data_inicio)
        except ValueError:
            pass
        
        # Filtro por data final (usa padrão se não fornecido)
        data_fim = self.request.GET.get('data_fim')
        if not data_fim:
            # Se não foi fornecido, usar último dia do mês corrente
            hoje = date.today()
            ultimo_dia = calendar.monthrange(hoje.year, hoje.month)[1]
            data_fim = hoje.replace(day=ultimo_dia).strftime('%Y-%m-%d')
        
        try:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
            queryset = queryset.filter(data__lte=data_fim)
        except ValueError:
            pass
        
        # Busca por descrição
        busca = self.request.GET.get('busca')
        if busca:
            queryset = queryset.filter(descricao__icontains=busca)
        
        # Ordenação
        order_by = self.request.GET.get('order_by', '-data')
        if order_by:
            queryset = queryset.order_by(order_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_by'] = self.request.GET.get('order_by', '-data')
        
        # Datas padrão (primeiro e último dia do mês corrente)
        hoje = date.today()
        primeiro_dia_mes = hoje.replace(day=1)
        ultimo_dia_mes = hoje.replace(day=calendar.monthrange(hoje.year, hoje.month)[1])
        
        # Criar form de filtro com valores da query string ou padrões
        initial_data = {
            'data_inicio': self.request.GET.get('data_inicio', primeiro_dia_mes.strftime('%Y-%m-%d')),
            'data_fim': self.request.GET.get('data_fim', ultimo_dia_mes.strftime('%Y-%m-%d')),
            'movimentacao': self.request.GET.get('movimentacao', 'todos'),
            'busca': self.request.GET.get('busca', ''),
        }
        context['filtro_form'] = FiltroForm(initial=initial_data)
        context['movimentacao_atual'] = initial_data['movimentacao']
        
        # Estatísticas
        queryset = self.get_queryset()
        context['total_entradas'] = sum(
            t.valor for t in queryset if t.is_entrada()
        )
        context['total_saidas'] = abs(sum(
            t.valor for t in queryset if t.is_saida()
        ))
        context['saldo'] = sum(t.valor for t in queryset)
        
        return context


class TransacaoCreateView(CreateView):
    """View para criar nova transação"""
    model = TransacaoBancaria
    form_class = TransacaoForm
    template_name = 'app/transacao_form.html'
    success_url = reverse_lazy('app:transacao_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Transação criada com sucesso!')
        return super().form_valid(form)


class TransacaoUpdateView(UpdateView):
    """View para editar transação existente"""
    model = TransacaoBancaria
    form_class = TransacaoForm
    template_name = 'app/transacao_form.html'
    success_url = reverse_lazy('app:transacao_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Transação atualizada com sucesso!')
        return super().form_valid(form)


class TransacaoDeleteView(DeleteView):
    """View para excluir transação"""
    model = TransacaoBancaria
    template_name = 'app/transacao_confirm_delete.html'
    success_url = reverse_lazy('app:transacao_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Transação excluída com sucesso!')
        return super().delete(request, *args, **kwargs)


class TransacaoDetailView(DetailView):
    """View para visualizar detalhes de uma transação"""
    model = TransacaoBancaria
    template_name = 'app/transacao_detail.html'
    context_object_name = 'transacao'


class TransacaoSinteticoView(TemplateView):
    """View para exibir relatório sintético agrupado por descrição"""
    template_name = 'app/transacao_sintetico.html'
    
    def get_queryset(self):
        """Aplica os mesmos filtros da lista de transações"""
        queryset = TransacaoBancaria.objects.all()
        
        # Filtro por movimentação (padrão: 'todos')
        movimentacao = self.request.GET.get('movimentacao', 'todos')
        if movimentacao == 'entradas':
            queryset = queryset.filter(valor__gt=0)
        elif movimentacao == 'saidas':
            queryset = queryset.filter(valor__lt=0)
        # Se for 'todos', não aplica filtro
        
        # Filtro por data inicial (usa padrão se não fornecido)
        data_inicio = self.request.GET.get('data_inicio')
        if not data_inicio:
            # Se não foi fornecido, usar primeiro dia do mês corrente
            hoje = date.today()
            data_inicio = hoje.replace(day=1).strftime('%Y-%m-%d')
        
        try:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            queryset = queryset.filter(data__gte=data_inicio)
        except ValueError:
            pass
        
        # Filtro por data final (usa padrão se não fornecido)
        data_fim = self.request.GET.get('data_fim')
        if not data_fim:
            # Se não foi fornecido, usar último dia do mês corrente
            hoje = date.today()
            ultimo_dia = calendar.monthrange(hoje.year, hoje.month)[1]
            data_fim = hoje.replace(day=ultimo_dia).strftime('%Y-%m-%d')
        
        try:
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
            queryset = queryset.filter(data__lte=data_fim)
        except ValueError:
            pass
        
        # Busca por descrição
        busca = self.request.GET.get('busca')
        if busca:
            queryset = queryset.filter(descricao__icontains=busca)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_by'] = self.request.GET.get('order_by', '-total_valor')
        
        # Datas padrão (primeiro e último dia do mês corrente)
        hoje = date.today()
        primeiro_dia_mes = hoje.replace(day=1)
        ultimo_dia_mes = hoje.replace(day=calendar.monthrange(hoje.year, hoje.month)[1])
        
        # Criar form de filtro com valores da query string ou padrões
        initial_data = {
            'data_inicio': self.request.GET.get('data_inicio', primeiro_dia_mes.strftime('%Y-%m-%d')),
            'data_fim': self.request.GET.get('data_fim', ultimo_dia_mes.strftime('%Y-%m-%d')),
            'movimentacao': self.request.GET.get('movimentacao', 'todos'),
            'busca': self.request.GET.get('busca', ''),
        }
        context['filtro_form'] = FiltroForm(initial=initial_data)
        context['movimentacao_atual'] = initial_data['movimentacao']
        
        queryset = self.get_queryset()
        
        # Agrupar por descrição e somar valores
        agrupado = queryset.values('descricao').annotate(
            total_valor=Sum('valor'),
            quantidade=Count('id')
        )
        
        # Aplicar ordenação
        agrupado = agrupado.order_by(context['order_by'])
        
        context['agrupado'] = agrupado
        
        # Estatísticas gerais
        context['total_entradas'] = sum(
            t.valor for t in queryset if t.is_entrada()
        )
        context['total_saidas'] = abs(sum(
            t.valor for t in queryset if t.is_saida()
        ))
        context['saldo'] = sum(t.valor for t in queryset)
        context['total_grupos'] = agrupado.count()
        
        return context


def clear_database(request):
    """View para limpar todos os dados do banco de dados"""
    if request.method == 'POST':
        # Verificar confirmação
        if request.POST.get('confirm') == 'yes':
            try:
                with transaction.atomic():
                    total_transacoes = TransacaoBancaria.objects.count()
                    
                    if total_transacoes == 0:
                        messages.info(request, 'O banco de dados já está vazio.')
                        return redirect('app:transacao_list')
                    
                    # Excluir todos os registros
                    TransacaoBancaria.objects.all().delete()
                    
                    messages.success(
                        request,
                        f'{total_transacoes} transação(ões) foram excluídas com sucesso! O banco de dados foi limpo.'
                    )
                    return redirect('app:transacao_list')
                    
            except Exception as e:
                messages.error(request, f'Erro ao limpar o banco de dados: {str(e)}')
                return redirect('app:clear_database')
        else:
            messages.warning(request, 'A limpeza do banco de dados foi cancelada.')
            return redirect('app:transacao_list')
    
    # GET - mostrar página de confirmação
    total_transacoes = TransacaoBancaria.objects.count()
    context = {
        'total_transacoes': total_transacoes,
    }
    return render(request, 'app/clear_database.html', context)
