"""
Rotas para integrações e criação de modelos dinâmicos.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from models.base_models import TableSchema
from models.response_models import APIResponse
from services.supabase_service import SupabaseService
from services.logging_service import LoggingService
from config.settings import Settings

# Router
router = APIRouter(prefix="/v1/integrations", tags=["Integrations"])

# Dependências
settings = Settings()
logger = LoggingService(settings.LOG_LEVEL, settings.LOG_FILE)
supabase_service = SupabaseService(settings, logger)

@router.post("/dynamic-model", response_model=APIResponse)
async def create_dynamic_model(schema: TableSchema):
    """
    Cria uma tabela dinâmica baseada no schema fornecido.
    """
    try:
        create_sql = schema.get_create_table_sql()
        
        # O método correto é execute_query, que retorna uma lista de resultados ou None
        result = await supabase_service.execute_query(schema.client_id, create_sql)

        # A execução de DDL (CREATE TABLE) bem-sucedida retorna uma lista vazia ou None em alguns casos.
        # A falha geralmente levanta uma exceção, que será capturada pelo bloco `except`.

        return JSONResponse(
            status_code=201,
            content=APIResponse(success=True, message=f"Tabela '{schema.name}' criada com sucesso.").to_dict()
        )

    except HTTPException as http_exc:
        logger.log_error(f"Erro HTTP ao criar tabela: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        logger.log_error(f"Erro inesperado ao criar tabela: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor ao processar a criação da tabela.")