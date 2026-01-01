import csv
from datetime import date
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.urls import reverse_lazy
from django.db import transaction
from django.db.models import Sum, Count
from .models import TransacaoBancaria
from .forms import TransacaoForm, FiltroForm
from .funcoes import (
    aplicar_filtros_transacoes,
    calcular_estatisticas,
    get_initial_data_filtro,
    processar_linha_csv,
)


def importa_csv(request):
    """View para importação de arquivo CSV"""
    if request.method == 'POST':
        if 'csv_file' not in request.FILES:
            messages.error(request, 'Por favor, selecione um arquivo CSV.')
            return redirect('app:transacao_importa_csv')
        
        csv_file = request.FILES['csv_file']
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'O arquivo deve ser um CSV.')
            return redirect('app:transacao_importa_csv')
        
        try:
            # Decodificar o arquivo
            decoded_file = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(decoded_file.splitlines())
            
            transacoes_criadas = 0
            transacoes_ignoradas = 0
            erros = []
            
            with transaction.atomic():
                for row_num, row in enumerate(csv_reader, start=2):
                    transacao, erro = processar_linha_csv(row, row_num)
                    
                    if erro:
                        erros.append(erro)
                    elif transacao is None:
                        # None indica que a transação já existe (deve ser ignorada)
                        transacoes_ignoradas += 1
                    else:
                        transacoes_criadas += 1
            
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
            return redirect('app:transacao_importa_csv')
    
    return render(request, 'app/importa_csv.html')


class TransacaoListView(ListView):
    """View para listar todas as transações"""
    model = TransacaoBancaria
    template_name = 'app/transacao_list.html'
    context_object_name = 'transacoes'
    paginate_by = 100
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = aplicar_filtros_transacoes(queryset, self.request.GET)
        
        # Ordenação
        order_by = self.request.GET.get('order_by', '-data')
        if order_by:
            queryset = queryset.order_by(order_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_by'] = self.request.GET.get('order_by', '-data')
        
        # Criar form de filtro com valores da query string ou padrões
        initial_data = get_initial_data_filtro(self.request.GET)
        context['filtro_form'] = FiltroForm(initial=initial_data)
        context['movimentacao_atual'] = initial_data['movimentacao']
        
        # Estatísticas
        queryset = self.get_queryset()
        stats = calcular_estatisticas(queryset)
        context.update(stats)
        
        return context


class TransacaoCreateView(CreateView):
    """View para criar nova transação"""
    model = TransacaoBancaria
    form_class = TransacaoForm
    template_name = 'app/transacao_form.html'
    success_url = reverse_lazy('app:transacao_list')
    
    def get_initial(self):
        """Define valores iniciais para o formulário"""
        return {
            'data': date.today(),
        }
    
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
        queryset = aplicar_filtros_transacoes(queryset, self.request.GET)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order_by'] = self.request.GET.get('order_by', '-total_valor')
        
        # Criar form de filtro com valores da query string ou padrões
        initial_data = get_initial_data_filtro(self.request.GET)
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
        context['total_grupos'] = agrupado.count()
        
        # Estatísticas gerais
        stats = calcular_estatisticas(queryset)
        context.update(stats)
        
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
