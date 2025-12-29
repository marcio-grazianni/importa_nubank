from django.db import models


class TransacaoBancaria(models.Model):
    """Model para armazenar transações bancárias do extrato Nubank"""
    
    data = models.DateField('Data', db_index=True)
    valor = models.DecimalField(
        'Valor',
        max_digits=10,
        decimal_places=2
    )
    identificador = models.CharField('Identificador', max_length=36, unique=True, db_index=True)
    descricao = models.TextField('Descrição')
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Transação Bancária'
        verbose_name_plural = 'Transações Bancárias'
        ordering = ['-data', '-criado_em']
        indexes = [
            models.Index(fields=['identificador']),
        ]
    
    def __str__(self):
        return f"{self.data.strftime('%d/%m/%Y')} - {self.valor} - {self.descricao[:50]}"
    
    def is_entrada(self):
        """Retorna True se o valor é positivo (entrada)"""
        return self.valor > 0
    
    def is_saida(self):
        """Retorna True se o valor é negativo (saída)"""
        return self.valor < 0

