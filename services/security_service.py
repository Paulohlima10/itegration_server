"""
Serviço de segurança da aplicação usando programação orientada a objetos
"""

import re
import time
from typing import Dict, Any, Optional, List
from collections import defaultdict, deque
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel, validator
from fastapi import HTTPException, Request
from services.logging_service import LoggingService

class RateLimiter:
    """Classe para implementar rate limiting"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Inicializa o rate limiter
        
        Args:
            max_requests: Número máximo de requisições por janela
            window_seconds: Tamanho da janela em segundos
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
    
    def is_allowed(self, client_ip: str) -> bool:
        """
        Verifica se o cliente pode fazer uma requisição
        
        Args:
            client_ip: IP do cliente
            
        Returns:
            True se permitido, False caso contrário
        """
        now = time.time()
        client_requests = self.requests[client_ip]
        
        # Remove requisições antigas da janela
        while client_requests and client_requests[0] <= now - self.window_seconds:
            client_requests.popleft()
        
        # Verifica se excedeu o limite
        if len(client_requests) >= self.max_requests:
            return False
        
        # Adiciona a requisição atual
        client_requests.append(now)
        return True

class DataValidator:
    """Classe para validação e sanitização de dados"""
    
    # Padrões de validação
    TABLE_NAME_PATTERN = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]*$')
    COLUMN_NAME_PATTERN = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]*$')
    COMPANY_ID_PATTERN = re.compile(r'^[a-zA-Z0-9\-_]+$')
    
    @staticmethod
    def sanitize_table_name(table_name: str) -> str:
        """
        Sanitiza nome de tabela
        
        Args:
            table_name: Nome da tabela
            
        Returns:
            Nome sanitizado
            
        Raises:
            ValueError: Se o nome for inválido
        """
        if not table_name or len(table_name) > 63:
            raise ValueError("Nome da tabela deve ter entre 1 e 63 caracteres")
        
        # Remove caracteres especiais e espaços
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', table_name.strip())
        
        # Garante que comece com letra
        if not sanitized[0].isalpha():
            sanitized = 'table_' + sanitized
        
        # Valida o padrão final
        if not DataValidator.TABLE_NAME_PATTERN.match(sanitized):
            raise ValueError(f"Nome de tabela inválido: {sanitized}")
        
        return sanitized.lower()
    
    @staticmethod
    def sanitize_column_name(column_name: str) -> str:
        """
        Sanitiza nome de coluna
        
        Args:
            column_name: Nome da coluna
            
        Returns:
            Nome sanitizado
            
        Raises:
            ValueError: Se o nome for inválido
        """
        if not column_name or len(column_name) > 63:
            raise ValueError("Nome da coluna deve ter entre 1 e 63 caracteres")
        
        # Remove caracteres especiais e espaços
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', column_name.strip())
        
        # Garante que comece com letra
        if not sanitized[0].isalpha():
            sanitized = 'col_' + sanitized
        
        # Valida o padrão final
        if not DataValidator.COLUMN_NAME_PATTERN.match(sanitized):
            raise ValueError(f"Nome de coluna inválido: {sanitized}")
        
        return sanitized.lower()
    
    @staticmethod
    def validate_company_id(company_id: str) -> str:
        """
        Valida ID da empresa
        
        Args:
            company_id: ID da empresa
            
        Returns:
            ID validado
            
        Raises:
            ValueError: Se o ID for inválido
        """
        if not company_id or len(company_id) > 50:
            raise ValueError("ID da empresa deve ter entre 1 e 50 caracteres")
        
        if not DataValidator.COMPANY_ID_PATTERN.match(company_id):
            raise ValueError("ID da empresa contém caracteres inválidos")
        
        return company_id.strip()
    
    @staticmethod
    def validate_json_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida e sanitiza dados JSON
        
        Args:
            data: Dados a serem validados
            
        Returns:
            Dados validados
            
        Raises:
            ValueError: Se os dados forem inválidos
        """
        if not isinstance(data, dict):
            raise ValueError("Dados devem ser um objeto JSON válido")
        
        if len(data) == 0:
            raise ValueError("Dados não podem estar vazios")
        
        if len(data) > 100:
            raise ValueError("Máximo de 100 campos por registro")
        
        validated_data = {}
        for key, value in data.items():
            # Sanitiza chave
            sanitized_key = DataValidator.sanitize_column_name(key)
            
            # Valida valor
            if value is None:
                validated_data[sanitized_key] = None
            elif isinstance(value, str) and len(value) > 10000:
                raise ValueError(f"Valor muito longo para campo {key}")
            else:
                validated_data[sanitized_key] = value
        
        return validated_data

class SecurityService:
    """Serviço principal de segurança"""
    
    def __init__(self, logging_service: LoggingService):
        """
        Inicializa o serviço de segurança
        
        Args:
            logging_service: Serviço de logging
        """
        self.logging_service = logging_service
        self.rate_limiter = RateLimiter(max_requests=100, window_seconds=60)
        self.validator = DataValidator()
        self.logger = logging.getLogger(__name__)
    
    def check_rate_limit(self, request: Request) -> None:
        """
        Verifica rate limiting para uma requisição
        
        Args:
            request: Requisição FastAPI
            
        Raises:
            HTTPException: Se exceder o rate limit
        """
        client_ip = self._get_client_ip(request)
        
        if not self.rate_limiter.is_allowed(client_ip):
            self.logging_service.log_security_event(
                "RATE_LIMIT_EXCEEDED", 
                client_ip,
                f"Excedeu {self.rate_limiter.max_requests} requisições em {self.rate_limiter.window_seconds}s"
            )
            raise HTTPException(
                status_code=429,
                detail="Rate limit excedido. Tente novamente mais tarde."
            )
    
    def validate_and_sanitize_data(self, data: Dict[str, Any], 
                                 table_name: str = None) -> Dict[str, Any]:
        """
        Valida e sanitiza dados de entrada
        
        Args:
            data: Dados a serem validados
            table_name: Nome da tabela (opcional)
            
        Returns:
            Dados validados e sanitizados
            
        Raises:
            HTTPException: Se os dados forem inválidos
        """
        try:
            # Valida dados JSON
            validated_data = self.validator.validate_json_data(data)
            
            # Sanitiza nome da tabela se fornecido
            if table_name:
                sanitized_table = self.validator.sanitize_table_name(table_name)
                return validated_data, sanitized_table
            
            return validated_data
            
        except ValueError as e:
            self.logging_service.log_security_event(
                "INVALID_INPUT",
                "unknown",
                str(e)
            )
            raise HTTPException(
                status_code=400,
                detail=f"Dados inválidos: {str(e)}"
            )
    
    def validate_company_permissions(self, company_id: str, 
                                   client_ip: str = None) -> str:
        """
        Valida permissões da empresa
        
        Args:
            company_id: ID da empresa
            client_ip: IP do cliente
            
        Returns:
            ID da empresa validado
            
        Raises:
            HTTPException: Se as permissões forem inválidas
        """
        try:
            validated_id = self.validator.validate_company_id(company_id)
            
            # Log de auditoria
            self.logging_service.log_audit(
                "COMPANY_ACCESS",
                resource=validated_id,
                details=f"IP: {client_ip}" if client_ip else None
            )
            
            return validated_id
            
        except ValueError as e:
            self.logging_service.log_security_event(
                "INVALID_COMPANY_ID",
                client_ip or "unknown",
                str(e)
            )
            raise HTTPException(
                status_code=400,
                detail=f"ID da empresa inválido: {str(e)}"
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Obtém o IP do cliente da requisição
        
        Args:
            request: Requisição FastAPI
            
        Returns:
            IP do cliente
        """
        # Verifica headers de proxy
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # IP direto
        return request.client.host if request.client else "unknown"