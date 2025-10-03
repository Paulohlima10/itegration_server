"""
Endpoints auxiliares da API para monitoramento e consultas
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import asyncio
from datetime import datetime
import psutil
import os

from models.base_models import CompanyConfig
from models.response_models import (
    HealthCheckResponse,
    ClientStatusResponse,
    APIResponse,
    ErrorResponse
)
from models.error_models import ErrorHandler, CompanyNotFoundError, ConnectionFailedError, InternalServerError
from services.supabase_service import SupabaseService
from services.logging_service import LoggingService
from config.settings import Settings


# Router para endpoints auxiliares
auxiliary_router = APIRouter(tags=["Auxiliary"])

# Dependências globais
settings = Settings()
logger = LoggingService(settings.LOG_LEVEL, settings.LOG_FILE)
supabase_service = SupabaseService(settings, logger)


@auxiliary_router.get("/health", response_model=HealthCheckResponse)
async def health_check() -> JSONResponse:
    """
    Endpoint de verificação de saúde da API
    
    Retorna:
    - Status da API
    - Informações do sistema
    - Conectividade com Supabase principal
    - Métricas básicas
    """
    
    start_time = datetime.now()
    
    try:
        # Informações básicas do sistema
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        
        system_info = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": memory_info.percent,
            "memory_available_gb": round(memory_info.available / (1024**3), 2),
            "disk_percent": disk_info.percent,
            "disk_free_gb": round(disk_info.free / (1024**3), 2)
        }
        
        # Testa conectividade com Supabase principal
        supabase_status = "healthy"
        supabase_error = None
        
        try:
            # Tenta uma operação simples no Supabase principal
            companies = await supabase_service.get_all_companies()
            company_count = len(companies) if companies else 0
        except Exception as e:
            supabase_status = "unhealthy"
            supabase_error = str(e)
            company_count = 0
        
        # Verifica diretórios essenciais
        directories_status = {}
        essential_dirs = [
            settings.LOGS_DIR,
            settings.SCHEMAS_DIR
        ]
        
        for dir_path in essential_dirs:
            try:
                os.makedirs(dir_path, exist_ok=True)
                directories_status[os.path.basename(dir_path)] = "accessible"
            except Exception as e:
                directories_status[os.path.basename(dir_path)] = f"error: {str(e)}"
        
        # Calcula tempo de resposta
        response_time = (datetime.now() - start_time).total_seconds()
        
        # Determina status geral
        overall_status = "healthy"
        if supabase_status != "healthy":
            overall_status = "degraded"
        if system_info["memory_percent"] > 90 or system_info["disk_percent"] > 90:
            overall_status = "warning"
        
        # Log do health check
        logger.log_info(f"Health check executado - Status: {overall_status}")
        
        response = HealthCheckResponse(
            success=True,
            status=overall_status,
            timestamp=datetime.now(),
            version="1.0.0",
            uptime_seconds=response_time,
            system_info=system_info,
            services={
                "supabase_main": {
                    "status": supabase_status,
                    "error": supabase_error,
                    "companies_count": company_count
                },
                "directories": directories_status
            }
        )
        
        return JSONResponse(
            status_code=200,
            content=response.to_dict()
        )
        
    except Exception as e:
        logger.log_error(f"Erro no health check: {str(e)}")
        
        error_response = HealthCheckResponse(
            success=False,
            status="error",
            timestamp=datetime.now(),
            version="1.0.0",
            uptime_seconds=0,
            system_info={},
            services={"error": str(e)}
        )
        
        return JSONResponse(
            status_code=500,
            content=error_response.model_dump(mode='json')
        )


@auxiliary_router.get("/api/schemas")
async def list_schemas() -> JSONResponse:
    """
    Lista todos os schemas disponíveis no diretório de schemas
    
    Retorna:
    - Lista de arquivos de schema disponíveis
    - Informações sobre cada schema
    """
    try:
        schemas_dir = settings.SCHEMAS_DIR
        
        if not os.path.exists(schemas_dir):
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Diretório de schemas não encontrado",
                    "schemas": [],
                    "total_count": 0
                }
            )
        
        schema_files = []
        for filename in os.listdir(schemas_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(schemas_dir, filename)
                file_stats = os.stat(file_path)
                
                schema_files.append({
                    "filename": filename,
                    "size": file_stats.st_size,
                    "modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                    "path": file_path
                })
        
        logger.log_info(f"Listados {len(schema_files)} schemas")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Encontrados {len(schema_files)} schemas",
                "schemas": schema_files,
                "total_count": len(schema_files)
            }
        )
        
    except Exception as e:
        logger.log_error(f"Erro ao listar schemas: {str(e)}")
        
        error_response = ErrorResponse(
            success=False,
            message="Erro ao listar schemas",
            error_code="LIST_SCHEMAS_ERROR",
            details={"details": str(e)}
        )
        
        return JSONResponse(
            status_code=500,
            content=error_response.model_dump(mode='json')
        )


@auxiliary_router.get("/api/logs")
async def list_logs() -> JSONResponse:
    """
    Lista arquivos de log disponíveis
    
    Retorna:
    - Lista de arquivos de log
    - Informações sobre cada arquivo
    """
    try:
        logs_dir = settings.LOGS_DIR
        
        if not os.path.exists(logs_dir):
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Diretório de logs não encontrado",
                    "logs": [],
                    "total_count": 0
                }
            )
        
        log_files = []
        for filename in os.listdir(logs_dir):
            if filename.endswith('.log'):
                file_path = os.path.join(logs_dir, filename)
                file_stats = os.stat(file_path)
                
                log_files.append({
                    "filename": filename,
                    "size": file_stats.st_size,
                    "modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                    "path": file_path
                })
        
        # Ordena por data de modificação (mais recente primeiro)
        log_files.sort(key=lambda x: x['modified'], reverse=True)
        
        logger.log_info(f"Listados {len(log_files)} arquivos de log")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Encontrados {len(log_files)} arquivos de log",
                "logs": log_files,
                "total_count": len(log_files)
            }
        )
        
    except Exception as e:
        logger.log_error(f"Erro ao listar logs: {str(e)}")
        
        error_response = ErrorResponse(
            success=False,
            message="Erro ao listar logs",
            error_code="LIST_LOGS_ERROR",
            details={"details": str(e)}
        )
        
        return JSONResponse(
            status_code=500,
            content=error_response.model_dump(mode='json')
        )


@auxiliary_router.get("/api/logs/{log_filename}")
async def get_log_content(log_filename: str, lines: int = 100) -> JSONResponse:
    """
    Obtém conteúdo de um arquivo de log específico
    
    Args:
        log_filename: Nome do arquivo de log
        lines: Número de linhas a retornar (padrão: 100, últimas linhas)
    
    Retorna:
    - Conteúdo do arquivo de log
    - Informações do arquivo
    """
    try:
        logs_dir = settings.LOGS_DIR
        log_path = os.path.join(logs_dir, log_filename)
        
        if not os.path.exists(log_path):
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": f"Arquivo de log '{log_filename}' não encontrado",
                    "error_code": "LOG_FILE_NOT_FOUND"
                }
            )
        
        # Lê as últimas N linhas do arquivo
        with open(log_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            
        # Pega as últimas 'lines' linhas
        content_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        file_stats = os.stat(log_path)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Conteúdo do log '{log_filename}'",
                "log_info": {
                    "filename": log_filename,
                    "size": file_stats.st_size,
                    "modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                    "total_lines": len(all_lines),
                    "returned_lines": len(content_lines)
                },
                "content": content_lines
            }
        )
        
    except Exception as e:
        logger.log_error(f"Erro ao ler log '{log_filename}': {str(e)}")
        
        error_response = ErrorResponse(
            success=False,
            message=f"Erro ao ler arquivo de log '{log_filename}'",
            error_code="READ_LOG_ERROR",
            details={"details": str(e)}
        )
        
        return JSONResponse(
            status_code=500,
            content=error_response.model_dump(mode='json')
        )


@auxiliary_router.get("/api/companies")
async def list_companies() -> JSONResponse:
    """
    Lista todas as empresas cadastradas no sistema
    
    Retorna:
    - Lista de empresas com informações básicas
    - Status de configuração de cada empresa
    """
    
    try:
        logger.log_info("Listando empresas cadastradas")
        
        # Obtém todas as empresas
        companies = await supabase_service.get_all_companies()
        
        if not companies:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "Nenhuma empresa cadastrada",
                    "companies": [],
                    "total_count": 0
                }
            )
        
        # Processa informações de cada empresa
        companies_info = []
        
        for empresa_id in companies:
            try:
                # Obtém configurações da empresa
                config = await supabase_service.get_company_config(empresa_id)
                
                # Verifica se tem configurações mínimas
                has_db_config = config and 'DB_URL' in config and 'DB_TOKEN' in config
                
                # Tenta conectar para verificar status
                connection_status = "unknown"
                table_count = 0
                
                if has_db_config:
                    try:
                        client = await supabase_service.get_client_connection(empresa_id)
                        if client:
                            connection_status = "connected"
                            # Obtém informações das tabelas
                            tables_info = await supabase_service.get_table_info(empresa_id)
                            table_count = len(tables_info) if tables_info else 0
                        else:
                            connection_status = "connection_failed"
                    except:
                        connection_status = "connection_error"
                else:
                    connection_status = "not_configured"
                
                company_info = {
                    "empresa_id": empresa_id,
                    "has_configuration": has_db_config,
                    "connection_status": connection_status,
                    "table_count": table_count,
                    "config_keys": list(config.keys()) if config else []
                }
                
                companies_info.append(company_info)
                
            except Exception as e:
                logger.log_error(f"Erro ao processar empresa {empresa_id}: {str(e)}")
                
                companies_info.append({
                    "empresa_id": empresa_id,
                    "has_configuration": False,
                    "connection_status": "error",
                    "table_count": 0,
                    "error": str(e)
                })
        
        logger.log_info(f"Listagem concluída: {len(companies_info)} empresas")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Encontradas {len(companies_info)} empresas",
                "companies": companies_info,
                "total_count": len(companies_info)
            }
        )
        
    except Exception as e:
        logger.log_error(f"Erro ao listar empresas: {str(e)}")
        
        # Usar tratamento de erro específico
        error = ErrorHandler.handle_internal_error(e, "listagem de empresas")
        
        return JSONResponse(
            status_code=error.status_code,
            content=error.detail
        )


@auxiliary_router.get("/api/companies/{empresa_id}/config")
async def get_company_config(empresa_id: str) -> JSONResponse:
    """
    Obtém configurações de uma empresa específica
    
    Args:
        empresa_id: ID da empresa
        
    Retorna:
        Configurações da empresa (sem valores sensíveis)
    """
    
    try:
        logger.log_info(f"Obtendo configurações da empresa {empresa_id}")
        
        # Obtém configurações
        config = await supabase_service.get_company_config(empresa_id)
        
        if not config:
            # Usar tratamento de erro específico para empresa não encontrada
            raise ErrorHandler.handle_company_not_found(empresa_id, "Configurações não encontradas")
        
        # Remove valores sensíveis para exibição
        safe_config = {}
        for key, value in config.items():
            if any(sensitive in key.lower() for sensitive in ['token', 'key', 'password', 'secret']):
                safe_config[key] = "***HIDDEN***"
            else:
                safe_config[key] = value
        
        # Verifica se tem configurações mínimas
        required_keys = ['DB_URL', 'DB_TOKEN']
        has_required = all(key in config for key in required_keys)
        
        logger.log_info(f"Configurações obtidas para empresa {empresa_id}")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "empresa_id": empresa_id,
                "configuration": safe_config,
                "has_required_config": has_required,
                "required_keys": required_keys,
                "config_count": len(config)
            }
        )
        
    except (CompanyNotFoundError, ConnectionFailedError, InternalServerError):
        raise
    except Exception as e:
        logger.log_error(f"Erro ao obter configurações da empresa {empresa_id}: {str(e)}")
        
        # Usar tratamento de erro específico
        error = ErrorHandler.handle_internal_error(e, f"obtenção de configurações da empresa {empresa_id}")
        
        return JSONResponse(
            status_code=error.status_code,
            content=error.detail
        )


@auxiliary_router.get("/api/companies/{empresa_id}/tables")
async def get_company_tables(empresa_id: str) -> JSONResponse:
    """
    Lista tabelas de uma empresa específica
    
    Args:
        empresa_id: ID da empresa
        
    Retorna:
        Lista de tabelas com informações básicas
    """
    
    try:
        logger.log_info(f"Listando tabelas da empresa {empresa_id}")
        
        # Verifica se empresa existe
        config = await supabase_service.get_company_config(empresa_id)
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Empresa '{empresa_id}' não encontrada"
            )
        
        # Verifica conectividade
        client = await supabase_service.get_client_connection(empresa_id)
        if not client:
            raise HTTPException(
                status_code=503,
                detail=f"Não foi possível conectar ao banco da empresa '{empresa_id}'"
            )
        
        # Obtém informações das tabelas
        tables_info = await supabase_service.get_table_info(empresa_id)
        
        if not tables_info:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "empresa_id": empresa_id,
                    "message": "Nenhuma tabela encontrada",
                    "tables": [],
                    "total_count": 0
                }
            )
        
        # Processa informações das tabelas
        processed_tables = []
        
        for table_info in tables_info:
            try:
                # Informações básicas da tabela
                table_data = {
                    "table_name": table_info.get("table_name", "unknown"),
                    "schema": table_info.get("table_schema", "public"),
                    "columns": table_info.get("columns", []),
                    "column_count": len(table_info.get("columns", [])),
                    "has_primary_key": any(
                        col.get("is_primary_key", False) 
                        for col in table_info.get("columns", [])
                    )
                }
                
                processed_tables.append(table_data)
                
            except Exception as e:
                logger.log_error(f"Erro ao processar tabela: {str(e)}")
                continue
        
        logger.log_info(f"Listagem de tabelas concluída para empresa {empresa_id}: {len(processed_tables)} tabelas")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "empresa_id": empresa_id,
                "message": f"Encontradas {len(processed_tables)} tabelas",
                "tables": processed_tables,
                "total_count": len(processed_tables)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.log_error(f"Erro ao listar tabelas da empresa {empresa_id}: {str(e)}")
        
        error_response = ErrorResponse(
            success=False,
            error_code="LIST_TABLES_ERROR",
            message="Erro ao listar tabelas da empresa",
            details=str(e)
        )
        
        return JSONResponse(
            status_code=500,
            content=error_response.to_dict()
        )