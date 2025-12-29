"""
Filtro de logging para suprimir logs 404 de requisições comuns do Chrome DevTools
"""
import logging


class IgnoreChromeDevToolsFilter(logging.Filter):
    """
    Filtro para suprimir logs 404 de requisições do Chrome DevTools
    que não afetam o funcionamento do sistema
    """
    
    def filter(self, record):
        # Lista de paths que devem ter logs 404 suprimidos
        ignored_paths = [
            '/.well-known/',
            '/favicon.ico',
        ]
        
        # Verificar a mensagem do log (formato: "GET /path HTTP/1.1" 404)
        message = getattr(record, 'getMessage', lambda: str(record.msg))()
        
        # Se contém 404 e algum dos paths ignorados, não logar
        if '404' in message:
            if any(ignored_path in message for ignored_path in ignored_paths):
                return False
        
        # Para outros logs, permitir normalmente
        return True

