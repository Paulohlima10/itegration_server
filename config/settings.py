"""
Configurações da aplicação usando Pydantic Settings
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os

class Settings(BaseSettings):
    """Classe de configurações da aplicação usando POO"""
    
    # Configurações do servidor
    HOST: str = Field(default="0.0.0.0", description="Host do servidor")
    PORT: int = Field(default=8000, description="Porta do servidor")
    DEBUG: bool = Field(default=False, description="Modo debug")
    
    # Configurações do Supabase Principal (para configurações das empresas)
    SUPABASE_MAIN_URL: str = Field(..., description="URL do Supabase principal")
    SUPABASE_MAIN_KEY: str = Field(..., description="Chave do Supabase principal")
    SUPABASE_SERVICE_KEY: str = Field(..., description="Chave de serviço do Supabase")
    
    # Configurações de segurança
    SECRET_KEY: str = Field(..., description="Chave secreta para JWT")
    API_KEY: Optional[str] = Field(default=None, description="Chave da API para autenticação")
    DATABASE_SECRET: Optional[str] = Field(default=None, description="Senha do Postgres (service role) para conexões diretas")
    DATABASE_URL: Optional[str] = Field(default=None, description="URL de conexão direta com o banco de dados PostgreSQL")
    
    # Configurações de logs
    LOG_LEVEL: str = Field(default="INFO", description="Nível de log")
    LOG_FILE: str = Field(default="logs/app.log", description="Arquivo de log")
    
    # Configurações de diretórios
    SCHEMAS_DIR: str = Field(default="schemas", description="Diretório para schemas")
    LOGS_DIR: str = Field(default="logs", description="Diretório para logs")
    
    # Configurações de timeout
    REQUEST_TIMEOUT: int = Field(default=30, description="Timeout para requisições")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        """Inicializa as configurações e cria diretórios necessários"""
        super().__init__(**kwargs)
        self._create_directories()
    
    def _create_directories(self) -> None:
        """Cria os diretórios necessários se não existirem"""
        directories = [self.SCHEMAS_DIR, self.LOGS_DIR]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    @property
    def database_url(self) -> str:
        """Retorna a URL do banco principal"""
        return self.SUPABASE_MAIN_URL
    
    @property
    def is_development(self) -> bool:
        """Verifica se está em modo de desenvolvimento"""
        return self.DEBUG
    
    def get_client_supabase_config(self, client_url: str, client_key: str) -> dict:
        """Retorna configuração para Supabase do cliente"""
        return {
            "url": client_url,
            "key": client_key,
            "timeout": self.REQUEST_TIMEOUT
        }
    
    def get_schema_directory(self) -> str:
        """Retorna o diretório de schemas"""
        return self.SCHEMAS_DIR