"""
Serviço de configuração para gerenciar configurações de empresas
"""
from typing import Dict, Optional, Any
import json
import asyncio
from datetime import datetime, timedelta
from fastapi import HTTPException
from models.base_models import BaseEntity
from services.supabase_service import SupabaseService
from services.logging_service import LoggingService


class CompanyConfig(BaseEntity):
    """Modelo para configuração de empresa"""
    empresa_id: str
    database_url: str
    database_token: str
    schema_name: Optional[str] = "public"
    max_connections: Optional[int] = 10
    timeout: Optional[int] = 30
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: Optional[bool] = True


class ConfigService:
    """Serviço para gerenciar configurações de empresas"""
    
    def __init__(self):
        self.supabase_service = SupabaseService()
        self.logger = LoggingService()
        self._config_cache: Dict[str, Dict] = {}
        self._cache_expiry: Dict[str, datetime] = {}
        self._cache_duration = timedelta(minutes=15)  # Cache por 15 minutos
    
    async def get_company_config(self, empresa_id: str) -> CompanyConfig:
        """
        Obtém a configuração de uma empresa
        
        Args:
            empresa_id: ID da empresa
            
        Returns:
            CompanyConfig: Configuração da empresa
            
        Raises:
            HTTPException: Se a empresa não for encontrada ou configuração inválida
        """
        try:
            # Verificar cache primeiro
            cached_config = self._get_from_cache(empresa_id)
            if cached_config:
                self.logger.info(f"Configuração da empresa {empresa_id} obtida do cache")
                return CompanyConfig(**cached_config)
            
            # Buscar no banco de dados
            config_data = await self.supabase_service.get_company_config(empresa_id)
            
            if not config_data:
                self.logger.error(f"Empresa {empresa_id} não encontrada")
                raise HTTPException(
                    status_code=404,
                    detail=f"Empresa {empresa_id} não encontrada"
                )
            
            # Validar configuração
            await self._validate_config_data(config_data)
            
            # Criar objeto de configuração
            company_config = CompanyConfig(**config_data)
            
            # Armazenar no cache
            await self.cache_config(empresa_id, config_data)
            
            self.logger.info(f"Configuração da empresa {empresa_id} obtida com sucesso")
            return company_config
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Erro ao obter configuração da empresa {empresa_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro interno ao obter configuração da empresa"
            )
    
    async def validate_company(self, empresa_id: str) -> bool:
        """
        Valida se uma empresa existe e está ativa
        
        Args:
            empresa_id: ID da empresa
            
        Returns:
            bool: True se a empresa é válida
            
        Raises:
            HTTPException: Se a empresa não for válida
        """
        try:
            config = await self.get_company_config(empresa_id)
            
            if not config.is_active:
                self.logger.warning(f"Empresa {empresa_id} está inativa")
                raise HTTPException(
                    status_code=403,
                    detail=f"Empresa {empresa_id} está inativa"
                )
            
            # Testar conexão com o banco da empresa
            try:
                test_connection = await self.supabase_service.test_company_connection(
                    config.database_url,
                    config.database_token
                )
                
                if not test_connection:
                    self.logger.error(f"Falha na conexão com banco da empresa {empresa_id}")
                    raise HTTPException(
                        status_code=503,
                        detail=f"Serviço indisponível para empresa {empresa_id}"
                    )
                    
            except Exception as conn_error:
                self.logger.error(f"Erro de conexão para empresa {empresa_id}: {str(conn_error)}")
                raise HTTPException(
                    status_code=503,
                    detail=f"Falha na conexão com o banco da empresa"
                )
            
            self.logger.info(f"Empresa {empresa_id} validada com sucesso")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Erro ao validar empresa {empresa_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Erro interno na validação da empresa"
            )
    
    async def cache_config(self, empresa_id: str, config: Dict[str, Any]) -> None:
        """
        Armazena configuração no cache
        
        Args:
            empresa_id: ID da empresa
            config: Dados de configuração
        """
        try:
            self._config_cache[empresa_id] = config.copy()
            self._cache_expiry[empresa_id] = datetime.now() + self._cache_duration
            
            self.logger.debug(f"Configuração da empresa {empresa_id} armazenada no cache")
            
        except Exception as e:
            self.logger.error(f"Erro ao armazenar configuração no cache: {str(e)}")
    
    def _get_from_cache(self, empresa_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém configuração do cache se ainda válida
        
        Args:
            empresa_id: ID da empresa
            
        Returns:
            Dict ou None se não encontrado ou expirado
        """
        try:
            if empresa_id not in self._config_cache:
                return None
            
            # Verificar se o cache expirou
            if datetime.now() > self._cache_expiry.get(empresa_id, datetime.min):
                # Cache expirado, remover
                self._config_cache.pop(empresa_id, None)
                self._cache_expiry.pop(empresa_id, None)
                return None
            
            return self._config_cache[empresa_id]
            
        except Exception as e:
            self.logger.error(f"Erro ao acessar cache: {str(e)}")
            return None
    
    async def _validate_config_data(self, config_data: Dict[str, Any]) -> None:
        """
        Valida os dados de configuração
        
        Args:
            config_data: Dados de configuração
            
        Raises:
            HTTPException: Se a configuração for inválida
        """
        required_fields = ['empresa_id', 'database_url', 'database_token']
        
        for field in required_fields:
            if field not in config_data or not config_data[field]:
                self.logger.error(f"Campo obrigatório ausente: {field}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Configuração inválida: campo '{field}' é obrigatório"
                )
        
        # Validar URL do banco
        if not config_data['database_url'].startswith(('postgresql://', 'postgres://')):
            self.logger.error("URL do banco inválida")
            raise HTTPException(
                status_code=400,
                detail="Configuração inválida: URL do banco deve ser PostgreSQL"
            )
    
    async def clear_cache(self, empresa_id: Optional[str] = None) -> None:
        """
        Limpa o cache de configurações
        
        Args:
            empresa_id: ID específico da empresa ou None para limpar tudo
        """
        try:
            if empresa_id:
                self._config_cache.pop(empresa_id, None)
                self._cache_expiry.pop(empresa_id, None)
                self.logger.info(f"Cache da empresa {empresa_id} limpo")
            else:
                self._config_cache.clear()
                self._cache_expiry.clear()
                self.logger.info("Cache de configurações limpo completamente")
                
        except Exception as e:
            self.logger.error(f"Erro ao limpar cache: {str(e)}")
    
    async def update_company_config(self, empresa_id: str, config_updates: Dict[str, Any]) -> CompanyConfig:
        """
        Atualiza configuração de uma empresa
        
        Args:
            empresa_id: ID da empresa
            config_updates: Dados para atualizar
            
        Returns:
            CompanyConfig: Configuração atualizada
        """
        try:
            # Validar dados de entrada
            await self._validate_config_data({**config_updates, 'empresa_id': empresa_id})
            
            # Atualizar no banco
            updated_config = await self.supabase_service.update_company_config(
                empresa_id, 
                config_updates
            )
            
            if not updated_config:
                raise HTTPException(
                    status_code=404,
                    detail=f"Empresa {empresa_id} não encontrada para atualização"
                )
            
            # Limpar cache para forçar reload
            await self.clear_cache(empresa_id)
            
            self.logger.info(f"Configuração da empresa {empresa_id} atualizada com sucesso")
            return CompanyConfig(**updated_config)
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Erro ao atualizar configuração da empresa {empresa_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Erro interno ao atualizar configuração"
            )