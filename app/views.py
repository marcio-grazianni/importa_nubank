import csv
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.urls import reverse_lazy
from django.db import transaction
from django.db.models import Sum, Count
from django.http import JsonResponse
from .models import TransacaoBancaria


def detectar_tipo_transacao(descricao):
    """Detecta o tipo de transação baseado na descrição"""
    descricao_lower = descricao.lower()
    
    if 'transferência recebida pelo pix' in descricao_lower:
        return 'transferencia_pix_recebida'
    elif 'transferência enviada pelo pix' in descricao_lower:
        return 'transferencia_pix_enviada'
    elif 'compra no débito' in descricao_lower:
        return 'compra_debito'
    elif 'recarga de celular' in descricao_lower:
        return 'recarga_celular'
    elif 'pagamento de fatura' in descricao_lower:
        return 'pagamento_fatura'
    elif 'pagamento de boleto' in descricao_lower:
        return 'pagamento_boleto'
    elif 'débito em conta' in descricao_lower:
        return 'debito_conta'
    else:
        return 'outro'


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
                        
                        # Detectar tipo de transação
                        tipo_transacao = detectar_tipo_transacao(descricao)
                        
                        # Criar nova transação
                        TransacaoBancaria.objects.create(
                            identificador=identificador,
                            data=data,
                            valor=valor,
                            descricao=descricao,
                            tipo_transacao=tipo_transacao,
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
    paginate_by = 50
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtro por tipo
        tipo = self.request.GET.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo_transacao=tipo)
        
        # Filtro por data inicial
        data_inicio = self.request.GET.get('data_inicio')
        if data_inicio:
            try:
                data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                queryset = queryset.filter(data__gte=data_inicio)
            except ValueError:
                pass
        
        # Filtro por data final
        data_fim = self.request.GET.get('data_fim')
        if data_fim:
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
        context['tipos_transacao'] = TransacaoBancaria.TIPO_CHOICES
        
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
    template_name = 'app/transacao_form.html'
    fields = ['data', 'valor', 'identificador', 'descricao', 'tipo_transacao']
    success_url = reverse_lazy('app:transacao_list')
    
    def form_valid(self, form):
        # Detectar tipo de transação se não foi informado
        if not form.cleaned_data.get('tipo_transacao') or form.cleaned_data['tipo_transacao'] == 'outro':
            tipo = detectar_tipo_transacao(form.cleaned_data['descricao'])
            form.instance.tipo_transacao = tipo
        
        messages.success(self.request, 'Transação criada com sucesso!')
        return super().form_valid(form)


class TransacaoUpdateView(UpdateView):
    """View para editar transação existente"""
    model = TransacaoBancaria
    template_name = 'app/transacao_form.html'
    fields = ['data', 'valor', 'identificador', 'descricao', 'tipo_transacao']
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
        
        # Filtro por tipo
        tipo = self.request.GET.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo_transacao=tipo)
        
        # Filtro por data inicial
        data_inicio = self.request.GET.get('data_inicio')
        if data_inicio:
            try:
                data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                queryset = queryset.filter(data__gte=data_inicio)
            except ValueError:
                pass
        
        # Filtro por data final
        data_fim = self.request.GET.get('data_fim')
        if data_fim:
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
        context['tipos_transacao'] = TransacaoBancaria.TIPO_CHOICES
        
        queryset = self.get_queryset()
        
        # Agrupar por descrição e somar valores
        agrupado = queryset.values('descricao').annotate(
            total_valor=Sum('valor'),
            quantidade=Count('id')
        ).order_by('-total_valor')
        
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
