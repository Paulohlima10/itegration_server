"""
Modelos de resposta da API
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from .base_models import BaseEntity

class APIResponse(BaseEntity):
    """Modelo base para respostas da API"""
    
    success: bool = Field(..., description="Se a operação foi bem-sucedida")
    message: str = Field(..., description="Mensagem de resposta")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp da resposta")

class DataInsertResponse(APIResponse):
    """Resposta para inserção de dados"""
    
    records_inserted: int = Field(default=0, description="Número de registros inseridos")
    table_name: str = Field(..., description="Nome da tabela")
    client_id: str = Field(..., description="ID do cliente")
    errors: Optional[List[str]] = Field(default=None, description="Lista de erros, se houver")

class SchemaCreateResponse(APIResponse):
    """Resposta para criação de schema"""
    
    table_name: str = Field(..., description="Nome da tabela criada")
    client_id: str = Field(..., description="ID do cliente")
    columns_created: int = Field(default=0, description="Número de colunas criadas")
    sql_executed: Optional[str] = Field(default=None, description="SQL executado")

class ErrorResponse(BaseEntity):
    """Resposta de erro"""
    
    success: bool = Field(default=False, description="Se a operação foi bem-sucedida")
    message: str = Field(..., description="Mensagem de erro")
    error_code: str = Field(..., description="Código do erro")
    details: Optional[Any] = Field(default=None, description="Detalhes do erro")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp da resposta")

class HealthCheckResponse(BaseEntity):
    """Resposta do health check"""
    
    status: str = Field(default="healthy", description="Status do serviço")
    version: str = Field(default="1.0.0", description="Versão da aplicação")
    uptime: Optional[str] = Field(default=None, description="Tempo de atividade")
    database_status: str = Field(default="connected", description="Status da conexão com banco")

class ClientStatusResponse(BaseEntity):
    """Resposta do status de um cliente"""
    
    client_id: str = Field(..., description="ID do cliente")
    client_name: str = Field(..., description="Nome do cliente")
    active: bool = Field(..., description="Se o cliente está ativo")
    supabase_status: str = Field(..., description="Status da conexão com Supabase do cliente")
    tables_count: int = Field(default=0, description="Número de tabelas no banco do cliente")
    last_activity: Optional[datetime] = Field(default=None, description="Última atividade")

class ValidationErrorResponse(BaseEntity):
    """Resposta para erros de validação"""
    
    success: bool = Field(default=False)
    message: str = Field(default="Erro de validação")
    validation_errors: List[Dict[str, Any]] = Field(..., description="Lista de erros de validação")
    timestamp: datetime = Field(default_factory=datetime.now)