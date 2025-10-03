"""
Endpoints principais da API para recepção de dados e schemas
"""

from typing import Dict, Any, List, Union, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import JSONResponse
import asyncio
import os
from datetime import datetime
from pydantic import ValidationError

from models.base_models import DataPayload, SchemaPayload, TableSchema, ColumnDefinition, ColumnType, MySQLIntegratorSchema, DatabaseSchema, TableDefinition, TableColumn, IntegratorDataPayload
from models.response_models import (
    DataInsertResponse, 
    SchemaCreateResponse, 
    ErrorResponse,
    APIResponse
)
from services.supabase_service import SupabaseService
from services.logging_service import LoggingService
from config.settings import Settings


# Router para endpoints de dados
data_router = APIRouter(prefix="/api", tags=["Data Reception"])

# Dependências globais
settings = Settings()
logger = LoggingService(settings.LOG_LEVEL, settings.LOG_FILE)
supabase_service = SupabaseService(settings, logger)


async def validate_empresa_id(empresa_id: str) -> bool:
    """Valida se empresa_id existe e tem configurações válidas"""
    try:
        config = await supabase_service.get_company_config(empresa_id)
        if not config:
            return False
        
        # Verifica se tem as configurações mínimas necessárias
        required_keys = ['DB_URL', 'DB_TOKEN']
        return all(key in config for key in required_keys)
        
    except Exception as e:
        logger.log_error(f"Erro ao validar empresa_id {empresa_id}: {str(e)}")
        return False


def infer_table_schema_from_data(table_name: str, data: List[Dict[str, Any]], empresa_id: str) -> TableSchema:
    """Infere schema da tabela baseado nos dados recebidos"""
    if not data:
        raise ValueError("Dados vazios fornecidos")
    
    # Analisa o primeiro registro para inferir tipos
    sample_record = data[0]
    columns = []
    
    for column_name, value in sample_record.items():
        # Infere tipo baseado no valor
        if isinstance(value, bool):
            column_type = ColumnType.BOOLEAN
        elif isinstance(value, int):
            column_type = ColumnType.INTEGER
        elif isinstance(value, float):
            column_type = ColumnType.DECIMAL
        elif isinstance(value, str):
            # Se parece com data/hora
            if len(value) >= 10 and ('-' in value or '/' in value):
                try:
                    datetime.fromisoformat(value.replace('Z', '+00:00'))
                    column_type = ColumnType.TIMESTAMP
                except:
                    column_type = ColumnType.VARCHAR
            else:
                column_type = ColumnType.VARCHAR
        else:
            column_type = ColumnType.TEXT  # Fallback para tipos complexos
        
        # Cria definição da coluna
        column_def = ColumnDefinition(
            name=column_name,
            type=column_type,  # Corrigido: usar 'type' em vez de 'column_type'
            nullable=True,  # Por padrão, permite NULL
            max_length=255 if column_type == ColumnType.VARCHAR else None
        )
        columns.append(column_def)
    
    # Assume que a primeira coluna é a chave primária se for 'id'
    primary_keys = ['id'] if 'id' in sample_record else []
    
    return TableSchema(
        name=table_name,
        columns=columns,
        client_id=empresa_id  # Adicionando o client_id obrigatório
    )


@data_router.post("/data/{empresa_id}", response_model=DataInsertResponse)
async def receive_data(
    empresa_id: str, 
    payload: DataPayload,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    """
    Endpoint principal para recepção de dados do integrador MySQL
    
    Fluxo:
    1. Validar empresa_id
    2. Obter configurações do cliente
    3. Conectar no Supabase do cliente
    4. Criar/atualizar tabela se necessário
    5. Inserir dados
    6. Retornar status
    """
    
    start_time = datetime.now()
    
    try:
        # Log da requisição recebida
        logger.log_request(
            method="POST",
            endpoint=f"/api/data/{empresa_id}",
            client_ip="localhost"  # Em produção, usar request.client.host
        )
        
        # 1. Validar empresa_id
        if not await validate_empresa_id(empresa_id):
            logger.log_error(f"Empresa ID inválido ou sem configurações: {empresa_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Empresa '{empresa_id}' não encontrada ou sem configurações válidas"
            )
        
        # 2. Validar payload
        if not payload.validate_payload():
            logger.log_error(f"Payload inválido recebido para empresa {empresa_id}")
            raise HTTPException(
                status_code=400,
                detail="Payload de dados inválido"
            )
        
        # Atualiza empresa_id no payload se não estiver definido
        if not payload.empresa_id:
            payload.empresa_id = empresa_id
        
        # 3. Conectar no Supabase do cliente
        client = await supabase_service.get_client_connection(empresa_id)
        if not client:
            logger.log_error(f"Falha ao conectar com Supabase da empresa {empresa_id}")
            raise HTTPException(
                status_code=503,
                detail="Erro de conexão com banco de dados do cliente"
            )

        # 4. Verificar se a tabela existe, senão criar
        table_exists = await supabase_service.table_exists(empresa_id, payload.table_name)
        if not table_exists:
            logger.log_info(f"Tabela '{payload.table_name}' não existe. Criando...")
            try:
                # Inferir schema da tabela a partir dos dados
                schema = supabase_service._infer_schema_from_data(empresa_id, payload.table_name, payload.data)
                
                # Criar a tabela
                create_sql = schema.get_create_table_sql()
                await supabase_service.execute_query(empresa_id, create_sql)
                logger.log_info(f"Tabela '{payload.table_name}' criada com sucesso.")

            except Exception as e:
                error_msg = f"Erro ao criar tabela '{payload.table_name}': {str(e)}"
                logger.log_error(error_msg)
                raise HTTPException(status_code=500, detail=error_msg)
        
        # 5. Inserir/Atualizar dados com o novo fluxo unificado
        success, message, records_inserted = await supabase_service.upsert_data(
            empresa_id=empresa_id,
            table_name=payload.table_name,
            data=payload.data
        )
        
        if not success:
            logger.log_error(f"Falha ao processar dados para a tabela {payload.table_name}: {message}")
            raise HTTPException(
                status_code=500,
                detail=message
            )
        
        # Calcula tempo de processamento
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Log de sucesso
        logger.log_info(
            f"Dados inseridos com sucesso: {records_inserted} registros na tabela "
            f"{payload.table_name} para empresa {empresa_id} em {processing_time:.2f}s"
        )
        
        # 5. Retornar resposta de sucesso
        response = DataInsertResponse(
            success=True,
            message=message,
            records_inserted=records_inserted,
            table_name=payload.table_name,
            client_id=empresa_id,
            processing_time_seconds=processing_time
        )
        
        return JSONResponse(
            status_code=200,
            content=response.to_dict()
        )
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Erro interno ao processar dados para empresa {empresa_id}: {str(e)}"
        logger.log_error(error_msg)
        
        # Retorna erro interno
        error_response = ErrorResponse(
            success=False,
            error_code="INTERNAL_ERROR",
            message="Erro interno do servidor",
            details=str(e) if settings.DEBUG else None
        )
        
        return JSONResponse(
            status_code=500,
            content=error_response.to_dict()
        )


@data_router.get("/data/{empresa_id}/{table_name}")
async def get_data(empresa_id: str, table_name: str):
    """
    Endpoint para ler dados de uma tabela de uma empresa.
    """
    logger.log_request(
        method="GET",
        endpoint=f"/api/data/{empresa_id}/{table_name}",
        client_ip="localhost"
    )

    if not await validate_empresa_id(empresa_id):
        logger.log_error(f"Empresa ID inválido ou sem configurações: {empresa_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Empresa '{empresa_id}' não encontrada ou sem configurações válidas"
        )

    try:
        query = f'SELECT * FROM "{table_name}"'
        data = await supabase_service.execute_query(empresa_id, query)

        if data is None:
            raise HTTPException(
                status_code=404,
                detail=f"Tabela '{table_name}' não encontrada para a empresa '{empresa_id}'"
            )

        response = JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": data
            }
        )
        response.charset = "utf-8"
        return response
    except Exception as e:
        error_msg = f"Erro ao ler dados da tabela {table_name} para empresa {empresa_id}: {str(e)}"
        logger.log_error(error_msg)

        raise HTTPException(
            status_code=500,
            detail="Erro interno do servidor"
        )


# Router para webhooks
webhook_router = APIRouter(prefix="/webhook", tags=["Webhooks"])

# Helper para normalizar payloads do MySQL Integrator (aceita tables como dict e tipos com tamanho)
def normalize_mysql_integrator_payload(payload_dict: Dict[str, Any]) -> MySQLIntegratorSchema:
    schema_dict = payload_dict.get("schema") or {}
    db_name = schema_dict.get("database_name") or "default_db"
    tables_raw = schema_dict.get("tables")

    tables_list: List[TableDefinition] = []

    def parse_type(raw_type: str):
        if not raw_type:
            return ("", None)
        rt = raw_type.strip()
        up = rt.upper()
        # VARCHAR(n)
        if up.startswith("VARCHAR"):
            l = up.find("(")
            r = up.find(")")
            max_len = None
            if l != -1 and r != -1 and r > l + 1:
                try:
                    max_len = int(up[l+1:r])
                except Exception:
                    max_len = None
            return ("varchar", max_len)
        # Tipos comuns
        if up == "INT" or up.startswith("INT"):
            return ("int", None)
        if up.startswith("DECIMAL"):
            return ("decimal", None)
        if up == "TEXT":
            return ("text", None)
        if up == "DATETIME":
            return ("datetime", None)
        return (rt.lower(), None)

    def normalize_column(col: Dict[str, Any]) -> TableColumn:
        col_type, max_len = parse_type(col.get("type") or "")
        return TableColumn(
            name=col.get("name") or "",
            type=col_type,
            nullable=bool(col.get("nullable", True)),
            is_primary_key=bool(col.get("primary_key", False)),
            max_length=max_len
        )

    if isinstance(tables_raw, dict):
        for tname, tinfo in tables_raw.items():
            cols_raw = (tinfo or {}).get("columns", [])
            columns = [normalize_column(c) for c in cols_raw]
            tables_list.append(TableDefinition(name=tname, columns=columns, record_count=(tinfo or {}).get("record_count")))
    elif isinstance(tables_raw, list):
        for t in tables_raw:
            tname = (t or {}).get("name")
            cols_raw = (t or {}).get("columns", [])
            columns = [normalize_column(c) for c in cols_raw]
            tables_list.append(TableDefinition(name=tname or "unknown_table", columns=columns, record_count=(t or {}).get("record_count")))

    schema_model = DatabaseSchema(database_name=db_name, tables=tables_list)

    ts = payload_dict.get("timestamp")
    if isinstance(ts, str):
        try:
            ts_parsed = datetime.fromisoformat(ts)
        except Exception:
            ts_parsed = datetime.now()
    elif isinstance(ts, datetime):
        ts_parsed = ts
    else:
        ts_parsed = datetime.now()

    return MySQLIntegratorSchema(
        schema=schema_model,
        timestamp=ts_parsed,
        source=payload_dict.get("source", "mysql_integrator"),
        empresa_id=payload_dict.get("empresa_id")
    )

# Novo handler compartilhado para aceitar empresa_id pela rota OU pelo corpo
async def _process_schema_request(
    empresa_id_path: Optional[str],
    payload_raw: Any,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    """
    Processa o schema recebido, aceitando empresa_id via rota ou via corpo.
    """
    start_time = datetime.now()

    # Constrói o payload tipado a partir do corpo recebido
    if isinstance(payload_raw, dict):
        if isinstance(payload_raw.get("schema"), str):
            payload = SchemaPayload.from_dict(payload_raw)
        else:
            payload = normalize_mysql_integrator_payload(payload_raw)
    else:
        payload = payload_raw

    # Determina o empresa_id final (rota tem prioridade; se não houver, usa do corpo)
    empresa_id_final = empresa_id_path or getattr(payload, "empresa_id", None)

    try:
        # Log da requisição
        endpoint_log = f"/webhook/schema" + (f"/{empresa_id_final}" if empresa_id_path else "")
        logger.log_request(
            method="POST",
            endpoint=endpoint_log,
            client_ip="localhost"  # Em produção, usar request.client.host
        )

        # Validar existência de empresa_id em algum lugar
        if not empresa_id_final:
            logger.log_error("empresa_id ausente na rota e no corpo do payload")
            raise HTTPException(
                status_code=400,
                detail="empresa_id é obrigatório (na rota ou no corpo)"
            )

        # 1. Validar empresa_id
        if not await validate_empresa_id(empresa_id_final):
            logger.log_error(f"Empresa ID inválido para schema: {empresa_id_final}")
            raise HTTPException(
                status_code=404,
                detail=f"Empresa '{empresa_id_final}' não encontrada"
            )

        # 2. Detectar tipo de payload e processar
        schema_dir = settings.get_schema_directory()
        filepath = None
        table_name = None

        if isinstance(payload, SchemaPayload):
            # Formato tradicional: schema SQL string
            logger.log_info(f"Recebido schema SQL tradicional para empresa {empresa_id_final}")

            # Validar schema SQL
            if not payload.validate_schema():
                logger.log_error(f"Schema SQL inválido recebido para empresa {empresa_id_final}")
                raise HTTPException(
                    status_code=400,
                    detail="Schema SQL inválido"
                )

            # Garantir empresa_id no payload
            payload.empresa_id = empresa_id_final

            # Salvar schema em arquivo (em subpasta da empresa)
            empresa_schema_dir = os.path.join(schema_dir, empresa_id_final)
            filepath = payload.save_to_file(empresa_schema_dir)
            table_name = payload.extract_table_name()

        elif isinstance(payload, MySQLIntegratorSchema):
            # Novo formato: JSON com estrutura de banco de dados
            logger.log_info(f"Recebido schema JSON do MySQL Integrator para empresa {empresa_id_final}")

            # Validar schema JSON
            if not payload.schema or not payload.schema.tables:
                logger.log_error(f"Schema JSON inválido recebido para empresa {empresa_id_final}")
                raise HTTPException(
                    status_code=400,
                    detail="Schema JSON inválido"
                )

            # Garantir empresa_id no payload
            payload.empresa_id = empresa_id_final

            # Converter JSON para SQL e salvar
            try:
                sql_content = payload.convert_to_sql()

                # Pegar o nome da primeira tabela como referência
                tables = payload.schema.tables
                table_name = tables[0].name if tables else "unknown_table"

                # Salvar o schema convertido
                filepath = payload.save_to_file(schema_dir, table_name)

                logger.log_info(f"Schema JSON convertido para SQL: {len(sql_content)} caracteres")

            except Exception as e:
                logger.log_error(f"Erro ao converter schema JSON para SQL: {str(e)}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Erro ao converter schema JSON: {str(e)}"
                )

        if not filepath:
            raise HTTPException(
                status_code=500,
                detail="Erro ao processar schema"
            )

        logger.log_info(f"Schema salvo em arquivo: {filepath}")

        # Calcula tempo de processamento
        processing_time = (datetime.now() - start_time).total_seconds()

        # Log de sucesso
        logger.log_info(
            f"Schema recebido e salvo para empresa {empresa_id_final}, "
            f"tabela: {table_name}, arquivo: {os.path.basename(filepath)}"
        )

        # 4. Retornar confirmação
        response = SchemaCreateResponse(
            success=True,
            message="Schema recebido e salvo com sucesso",
            table_name=table_name,
            client_id=empresa_id_final,
            file_path=filepath,
            processing_time_seconds=processing_time
        )

        return JSONResponse(
            status_code=200,
            content=response.to_dict()
        )

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Erro interno ao processar schema para empresa {empresa_id_final}: {str(e)}"
        logger.log_error(error_msg)

        error_response = ErrorResponse(
            success=False,
            error_code="INTERNAL_ERROR",
            message="Erro interno do servidor",
            details=str(e) if settings.DEBUG else None
        )

        return JSONResponse(
            status_code=500,
            content=error_response.to_dict()
        )

# Endpoint antigo com empresa_id na rota (continua aceitando)
@webhook_router.post("/schema/{empresa_id}", response_model=SchemaCreateResponse)
async def receive_schema(
    empresa_id: str,
    request: Request,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    payload = await request.json()
    return await _process_schema_request(empresa_id_path=empresa_id, payload_raw=payload, background_tasks=background_tasks)

# Novo endpoint sem empresa_id na rota (lê do corpo JSON)
@webhook_router.post("/schema", response_model=SchemaCreateResponse)
async def receive_schema_body(
    request: Request,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    payload = await request.json()
    return await _process_schema_request(empresa_id_path=None, payload_raw=payload, background_tasks=background_tasks)

# Compatibilidade com barra final
@webhook_router.post("/schema/", response_model=SchemaCreateResponse)
async def receive_schema_body_slash(
    request: Request,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    payload = await request.json()
    return await _process_schema_request(empresa_id_path=None, payload_raw=payload, background_tasks=background_tasks)

# Suporte explícito a preflight CORS para evitar 405 em clientes
@webhook_router.options("/schema")
async def preflight_schema() -> JSONResponse:
    return JSONResponse(status_code=200, content={"success": True})

@webhook_router.options("/schema/")
async def preflight_schema_slash() -> JSONResponse:
    return JSONResponse(status_code=200, content={"success": True})

@webhook_router.options("/schema/{empresa_id}")
async def preflight_schema_with_id(empresa_id: str) -> JSONResponse:
    return JSONResponse(status_code=200, content={"success": True, "empresa_id": empresa_id})

@webhook_router.post("/data", response_model=APIResponse)
async def receive_integrator_data_body(
    request: Request,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    payload_raw = await request.json()
    return await _process_integrator_data_request(empresa_id_path=None, payload_raw=payload_raw, background_tasks=background_tasks)

@webhook_router.post("/data/", response_model=APIResponse)
async def receive_integrator_data_body_slash(
    request: Request,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    payload_raw = await request.json()
    return await _process_integrator_data_request(empresa_id_path=None, payload_raw=payload_raw, background_tasks=background_tasks)

@webhook_router.options("/data")
async def preflight_data() -> JSONResponse:
    return JSONResponse(status_code=200, content={"success": True})

@webhook_router.options("/data/")
async def preflight_data_slash() -> JSONResponse:
    return JSONResponse(status_code=200, content={"success": True})

async def _process_integrator_data_request(empresa_id_path: Optional[str], payload_raw: Dict[str, Any], background_tasks: BackgroundTasks) -> JSONResponse:
    start_time = datetime.now()
    try:
        empresa_id = payload_raw.get("empresa_id") or empresa_id_path
        if not empresa_id:
            logger.log_error("empresa_id ausente no payload de dados integrador")
            raise HTTPException(status_code=400, detail="empresa_id é obrigatório")
        
        logger.log_request(method="POST", endpoint=f"/webhook/data", client_ip="localhost")
        
        if not await validate_empresa_id(empresa_id):
            logger.log_error(f"Empresa ID inválido ou sem configurações: {empresa_id}")
            raise HTTPException(status_code=404, detail=f"Empresa '{empresa_id}' não encontrada ou sem configurações válidas")
        
        # Normaliza payload: aceita formato multi-tabelas {"data": {...}} ou single-tabela {"table": "...", "records": [...]}
        try:
            integrator_payload = IntegratorDataPayload(**payload_raw)
        except Exception as e:
            # Tenta converter formato single-tabela para multi-tabelas
            if isinstance(payload_raw, dict) and "table" in payload_raw and "records" in payload_raw:
                table_name_in = str(payload_raw.get("table"))
                records_in = payload_raw.get("records") or []
                normalized_raw = {
                    "timestamp": payload_raw.get("timestamp", datetime.now().isoformat()),
                    "data": {table_name_in: records_in},
                    "source": payload_raw.get("source", "mysql_integrator"),
                    "empresa_id": empresa_id,
                }
                try:
                    integrator_payload = IntegratorDataPayload(**normalized_raw)
                except Exception as e2:
                    logger.log_error(f"Falha ao normalizar payload single-tabela: {e2}")
                    raise HTTPException(status_code=400, detail="Payload de dados inválido após normalização")
            else:
                logger.log_error(f"Formato de payload inválido: chaves esperadas 'data' ou 'table'/'records'")
                raise HTTPException(status_code=400, detail="Formato de payload inválido: esperado 'data' por tabelas ou 'table'+'records'")
        if not integrator_payload.validate_payload():
            raise HTTPException(status_code=400, detail="Payload multi-tabelas inválido")
        
        client = await supabase_service.get_client_connection(empresa_id)
        if not client:
            logger.log_error(f"Falha ao conectar com Supabase da empresa {empresa_id}")
            raise HTTPException(status_code=503, detail="Erro de conexão com banco de dados do cliente")
        
        total_inserted = 0
        table_results: List[Dict[str, Any]] = []
        
        for table_name, records in integrator_payload.data.items():
            if not records:
                continue
            table_exists = await supabase_service.table_exists(empresa_id, table_name)
            if not table_exists:
                logger.log_info(f"Tabela '{table_name}' não existe. Criando...")
                schema = supabase_service._infer_schema_from_data(empresa_id, table_name, records)
                create_sql = schema.get_create_table_sql()
                await supabase_service.execute_query(empresa_id, create_sql)
                logger.log_info(f"Tabela '{table_name}' criada com sucesso.")
            success, message, records_inserted = await supabase_service.upsert_data(
                empresa_id=empresa_id,
                table_name=table_name,
                data=records
            )
            if not success:
                logger.log_error(f"Falha ao processar dados para a tabela {table_name}: {message}")
                raise HTTPException(status_code=500, detail=message)
            total_inserted += records_inserted or 0
            table_results.append({
                "table_name": table_name,
                "records_inserted": records_inserted,
                "message": message
            })
        processing_time = (datetime.now() - start_time).total_seconds()
        content = {
            "success": True,
            "message": f"Dados processados com sucesso para {len(table_results)} tabelas",
            "timestamp": datetime.now().isoformat(),
            "client_id": empresa_id,
            "total_records_inserted": total_inserted,
            "processing_time_seconds": processing_time,
            "tables": table_results
        }
        return JSONResponse(status_code=200, content=content)
    except HTTPException:
        raise
    except Exception as e:
        error_response = ErrorResponse(success=False, message="Erro interno do servidor", error_code="INTERNAL_ERROR", details=str(e) if settings.DEBUG else None)
        return JSONResponse(status_code=500, content=error_response.to_dict())