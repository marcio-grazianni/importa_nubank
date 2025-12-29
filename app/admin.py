from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import TransacaoBancaria


@admin.register(TransacaoBancaria)
class TransacaoBancariaAdmin(admin.ModelAdmin):
    list_display = ['data', 'valor_formatado', 'descricao_resumida', 'criado_em']
    list_filter = ['data', 'criado_em']
    search_fields = ['descricao', 'identificador']
    date_hierarchy = 'data'
    ordering = ['-data', '-criado_em']
    readonly_fields = ['criado_em', 'atualizado_em']
    
    fieldsets = (
        ('Informações Principais', {
            'fields': ('data', 'valor', 'identificador', 'descricao')
        }),
        ('Metadados', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def valor_formatado(self, obj):
        if obj.is_entrada():
            return mark_safe(f'<span style="color: green;">R$ {obj.valor:.2f}</span>')
        else:
            return mark_safe(f'<span style="color: red;">R$ {obj.valor:.2f}</span>')
    valor_formatado.short_description = 'Valor'
    
    def descricao_resumida(self, obj):
        return obj.descricao[:50] + '...' if len(obj.descricao) > 50 else obj.descricao
    descricao_resumida.short_description = 'Descrição'
