"""
Serviço de logging da aplicação usando programação orientada a objetos
"""

import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional

class LoggingService:
    """Classe para gerenciar o sistema de logs da aplicação"""
    
    def __init__(self, log_level: str = "INFO", log_file: str = "logs/receptor.log"):
        """
        Inicializa o serviço de logging
        
        Args:
            log_level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Caminho para o arquivo de log
        """
        self.log_level = getattr(logging, log_level.upper())
        self.log_file = log_file
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Configura o sistema de logging avançado com FileHandler e StreamHandler"""
        # Cria o diretório de logs se não existir
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        # Configuração básica do logging conforme especificado
        logging.basicConfig(
            level=self.log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        # Configuração adicional para rotação de arquivos
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        # Formatter personalizado
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Logger para auditoria
        self._setup_audit_logger()
    
    def _setup_audit_logger(self) -> None:
        """Configura logger específico para auditoria"""
        audit_logger = logging.getLogger('audit')
        audit_handler = logging.FileHandler('logs/audit.log', encoding='utf-8')
        audit_formatter = logging.Formatter(
            '%(asctime)s - AUDIT - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        audit_handler.setFormatter(audit_formatter)
        audit_logger.addHandler(audit_handler)
        audit_logger.setLevel(logging.INFO)
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Retorna um logger com o nome especificado
        
        Args:
            name: Nome do logger (geralmente __name__ do módulo)
            
        Returns:
            Logger configurado
        """
        return logging.getLogger(name)
    
    def log_request(self, method: str, endpoint: str, client_ip: str, 
                   status_code: Optional[int] = None) -> None:
        """
        Registra informações de requisição HTTP
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            endpoint: Endpoint acessado
            client_ip: IP do cliente
            status_code: Código de status da resposta
        """
        logger = self.get_logger("http_requests")
        message = f"{method} {endpoint} - IP: {client_ip}"
        if status_code:
            message += f" - Status: {status_code}"
        logger.info(message)
    
    def log_database_operation(self, operation: str, table: str, 
                             client_id: str, success: bool = True) -> None:
        """
        Registra operações de banco de dados
        
        Args:
            operation: Tipo de operação (INSERT, UPDATE, CREATE_TABLE, etc.)
            table: Nome da tabela
            client_id: ID do cliente
            success: Se a operação foi bem-sucedida
        """
        logger = self.get_logger("database")
        status = "SUCCESS" if success else "FAILED"
        message = f"{operation} on {table} for client {client_id} - {status}"
        
        if success:
            logger.info(message)
        else:
            logger.error(message)
    
    def log_info(self, message: str) -> None:
        """
        Registra uma mensagem de informação
        
        Args:
            message: Mensagem a ser registrada
        """
        logger = logging.getLogger(__name__)
        logger.info(message)
    
    def log_warning(self, message: str) -> None:
        """
        Registra uma mensagem de aviso
        
        Args:
            message: Mensagem a ser registrada
        """
        logger = logging.getLogger(__name__)
        logger.warning(message)

    def log_error(self, error: Exception, context: str = "") -> None:
        """
        Registra erros com contexto adicional
        
        Args:
            error: Exceção capturada
            context: Contexto adicional sobre o erro
        """
        logger = logging.getLogger(__name__)
        message = f"Error in {context}: {str(error)}" if context else str(error)
        logger.error(message, exc_info=True)
    
    def log_audit(self, action: str, user_id: str = None, resource: str = None, 
                  details: str = None) -> None:
        """
        Registra eventos de auditoria para segurança
        
        Args:
            action: Ação realizada
            user_id: ID do usuário (se aplicável)
            resource: Recurso acessado
            details: Detalhes adicionais
        """
        audit_logger = logging.getLogger('audit')
        message_parts = [f"ACTION: {action}"]
        
        if user_id:
            message_parts.append(f"USER: {user_id}")
        if resource:
            message_parts.append(f"RESOURCE: {resource}")
        if details:
            message_parts.append(f"DETAILS: {details}")
            
        audit_logger.info(" | ".join(message_parts))
    
    def log_security_event(self, event_type: str, client_ip: str, 
                          details: str = None) -> None:
        """
        Registra eventos de segurança
        
        Args:
            event_type: Tipo do evento (RATE_LIMIT, INVALID_INPUT, etc.)
            client_ip: IP do cliente
            details: Detalhes adicionais
        """
        security_logger = logging.getLogger('security')
        message = f"SECURITY_EVENT: {event_type} from IP: {client_ip}"
        if details:
            message += f" - {details}"
        security_logger.warning(message)