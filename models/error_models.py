"""
Modelos de erro específicos para diferentes cenários da API
"""
from typing import Optional, Dict, Any
from enum import Enum
from fastapi import HTTPException
from .base_models import BaseEntity


class ErrorCode(str, Enum):
    """Códigos de erro padronizados"""
    # Erros de empresa (404)
    COMPANY_NOT_FOUND = "COMPANY_NOT_FOUND"
    COMPANY_CONFIG_NOT_FOUND = "COMPANY_CONFIG_NOT_FOUND"
    
    # Erros de configuração (400)
    INVALID_CONFIG = "INVALID_CONFIG"
    INVALID_PARAMETERS = "INVALID_PARAMETERS"
    MISSING_REQUIRED_FIELDS = "MISSING_REQUIRED_FIELDS"
    INVALID_DATA_FORMAT = "INVALID_DATA_FORMAT"
    
    # Erros de conexão (503)
    DATABASE_CONNECTION_FAILED = "DATABASE_CONNECTION_FAILED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    CONNECTION_TIMEOUT = "CONNECTION_TIMEOUT"
    
    # Conflitos de tipos (422)
    TYPE_CONFLICT = "TYPE_CONFLICT"
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
    DATA_VALIDATION_ERROR = "DATA_VALIDATION_ERROR"
    INCOMPATIBLE_DATA_TYPES = "INCOMPATIBLE_DATA_TYPES"
    
    # Erros internos (500)
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    UNEXPECTED_ERROR = "UNEXPECTED_ERROR"
    
    # Erros de autorização (401/403)
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_TOKEN = "INVALID_TOKEN"
    
    # Erros de recursos (409)
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"


class APIError(BaseEntity):
    """Modelo base para erros da API"""
    error_code: ErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    request_id: Optional[str] = None


class CompanyNotFoundError(HTTPException):
    """Erro quando empresa não é encontrada (404)"""
    
    def __init__(self, empresa_id: str, details: Optional[Dict[str, Any]] = None):
        self.empresa_id = empresa_id
        self.details = details or {}
        
        super().__init__(
            status_code=404,
            detail={
                "error_code": ErrorCode.COMPANY_NOT_FOUND,
                "message": f"Empresa '{empresa_id}' não encontrada",
                "details": self.details
            }
        )


class InvalidConfigError(HTTPException):
    """Erro quando configurações são inválidas (400)"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.details = details or {}
        
        super().__init__(
            status_code=400,
            detail={
                "error_code": ErrorCode.INVALID_CONFIG,
                "message": message,
                "details": self.details
            }
        )


class ConnectionFailedError(HTTPException):
    """Erro quando falha na conexão (503)"""
    
    def __init__(self, service: str, details: Optional[Dict[str, Any]] = None):
        self.service = service
        self.details = details or {}
        
        super().__init__(
            status_code=503,
            detail={
                "error_code": ErrorCode.DATABASE_CONNECTION_FAILED,
                "message": f"Falha na conexão com {service}",
                "details": self.details
            }
        )


class TypeConflictError(HTTPException):
    """Erro quando há conflito de tipos (422)"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.details = details or {}
        
        super().__init__(
            status_code=422,
            detail={
                "error_code": ErrorCode.TYPE_CONFLICT,
                "message": message,
                "details": self.details
            }
        )


class DataValidationError(HTTPException):
    """Erro de validação de dados (422)"""
    
    def __init__(self, field: str, value: Any, expected_type: str, details: Optional[Dict[str, Any]] = None):
        self.field = field
        self.value = value
        self.expected_type = expected_type
        self.details = details or {}
        
        super().__init__(
            status_code=422,
            detail={
                "error_code": ErrorCode.DATA_VALIDATION_ERROR,
                "message": f"Erro de validação no campo '{field}': esperado {expected_type}, recebido {type(value).__name__}",
                "details": {
                    "field": field,
                    "received_value": str(value),
                    "expected_type": expected_type,
                    **self.details
                }
            }
        )


class ServiceUnavailableError(HTTPException):
    """Erro quando serviço está indisponível (503)"""
    
    def __init__(self, service: str, reason: str, details: Optional[Dict[str, Any]] = None):
        self.service = service
        self.reason = reason
        self.details = details or {}
        
        super().__init__(
            status_code=503,
            detail={
                "error_code": ErrorCode.SERVICE_UNAVAILABLE,
                "message": f"Serviço {service} indisponível: {reason}",
                "details": self.details
            }
        )


class InternalServerError(HTTPException):
    """Erro interno do servidor (500)"""
    
    def __init__(self, message: str = "Erro interno do servidor", details: Optional[Dict[str, Any]] = None):
        self.details = details or {}
        
        super().__init__(
            status_code=500,
            detail={
                "error_code": ErrorCode.INTERNAL_SERVER_ERROR,
                "message": message,
                "details": self.details
            }
        )


class ErrorHandler:
    """Classe para tratamento centralizado de erros"""
    
    @staticmethod
    def handle_company_not_found(empresa_id: str, additional_info: Optional[str] = None) -> CompanyNotFoundError:
        """Trata erro de empresa não encontrada"""
        details = {}
        if additional_info:
            details["additional_info"] = additional_info
            
        return CompanyNotFoundError(empresa_id, details)
    
    @staticmethod
    def handle_invalid_config(config_field: str, reason: str) -> InvalidConfigError:
        """Trata erro de configuração inválida"""
        message = f"Configuração inválida no campo '{config_field}': {reason}"
        details = {
            "field": config_field,
            "reason": reason
        }
        
        return InvalidConfigError(message, details)
    
    @staticmethod
    def handle_connection_failed(service: str, error_message: str, connection_url: Optional[str] = None) -> ConnectionFailedError:
        """Trata erro de falha na conexão"""
        details = {
            "error_message": error_message
        }
        if connection_url:
            # Mascarar informações sensíveis da URL
            masked_url = ErrorHandler._mask_sensitive_info(connection_url)
            details["connection_url"] = masked_url
            
        return ConnectionFailedError(service, details)
    
    @staticmethod
    def handle_type_conflict(expected_type: str, received_type: str, field: str, table: Optional[str] = None) -> TypeConflictError:
        """Trata erro de conflito de tipos"""
        message = f"Conflito de tipos no campo '{field}': esperado {expected_type}, recebido {received_type}"
        details = {
            "field": field,
            "expected_type": expected_type,
            "received_type": received_type
        }
        if table:
            details["table"] = table
            
        return TypeConflictError(message, details)
    
    @staticmethod
    def handle_data_validation(field: str, value: Any, expected_type: str, validation_rule: Optional[str] = None) -> DataValidationError:
        """Trata erro de validação de dados"""
        details = {}
        if validation_rule:
            details["validation_rule"] = validation_rule
            
        return DataValidationError(field, value, expected_type, details)
    
    @staticmethod
    def handle_service_unavailable(service: str, reason: str, retry_after: Optional[int] = None) -> ServiceUnavailableError:
        """Trata erro de serviço indisponível"""
        details = {}
        if retry_after:
            details["retry_after_seconds"] = retry_after
            
        return ServiceUnavailableError(service, reason, details)
    
    @staticmethod
    def handle_internal_error(original_error: Exception, context: Optional[str] = None) -> InternalServerError:
        """Trata erro interno do servidor"""
        details = {
            "error_type": type(original_error).__name__,
            "error_message": str(original_error)
        }
        if context:
            details["context"] = context
            
        message = "Erro interno do servidor"
        if context:
            message += f" ({context})"
            
        return InternalServerError(message, details)
    
    @staticmethod
    def _mask_sensitive_info(url: str) -> str:
        """Mascara informações sensíveis de URLs"""
        import re
        
        # Mascarar senhas em URLs
        masked_url = re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', url)
        
        # Mascarar tokens/keys
        masked_url = re.sub(r'[?&](token|key|password|secret)=([^&]+)', r'\1=***', masked_url)
        
        return masked_url


# Mapeamento de códigos de erro para status HTTP
ERROR_STATUS_MAPPING = {
    ErrorCode.COMPANY_NOT_FOUND: 404,
    ErrorCode.COMPANY_CONFIG_NOT_FOUND: 404,
    
    ErrorCode.INVALID_CONFIG: 400,
    ErrorCode.INVALID_PARAMETERS: 400,
    ErrorCode.MISSING_REQUIRED_FIELDS: 400,
    ErrorCode.INVALID_DATA_FORMAT: 400,
    
    ErrorCode.DATABASE_CONNECTION_FAILED: 503,
    ErrorCode.SERVICE_UNAVAILABLE: 503,
    ErrorCode.EXTERNAL_SERVICE_ERROR: 503,
    ErrorCode.CONNECTION_TIMEOUT: 503,
    
    ErrorCode.TYPE_CONFLICT: 422,
    ErrorCode.SCHEMA_MISMATCH: 422,
    ErrorCode.DATA_VALIDATION_ERROR: 422,
    ErrorCode.INCOMPATIBLE_DATA_TYPES: 422,
    
    ErrorCode.INTERNAL_SERVER_ERROR: 500,
    ErrorCode.UNEXPECTED_ERROR: 500,
    
    ErrorCode.UNAUTHORIZED: 401,
    ErrorCode.FORBIDDEN: 403,
    ErrorCode.INVALID_TOKEN: 401,
    
    ErrorCode.RESOURCE_CONFLICT: 409,
    ErrorCode.DUPLICATE_RESOURCE: 409
}


def get_http_status_for_error(error_code: ErrorCode) -> int:
    """Retorna o status HTTP apropriado para um código de erro"""
    return ERROR_STATUS_MAPPING.get(error_code, 500)