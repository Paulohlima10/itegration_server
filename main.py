"""
Aplicação FastAPI para recepção de dados MySQL e replicação para Supabase
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime
import os

from config.settings import Settings
from services.logging_service import LoggingService
from services.security_service import SecurityService
from api.data_routes import data_router, webhook_router
from api.auxiliary_routes import auxiliary_router
from api.v1.integrations import router as integrations_router


# Configurações globais
settings = Settings()
logger = LoggingService(settings.LOG_LEVEL, settings.LOG_FILE)
security_service = SecurityService(logger)

# Inicialização da aplicação FastAPI
app = FastAPI(
    title="MySQL to Supabase Data Replicator",
    description="API para recepção de dados MySQL e replicação automática para bancos Supabase de clientes",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware para logar o corpo da requisição
@app.middleware("http")
async def log_request_body_middleware(request: Request, call_next):
    if "application/json" in request.headers.get("content-type", ""):
        body = await request.body()
        logger.log_info(f"Request Body: {body.decode('utf-8')}")
        # Recria o stream da requisição para que possa ser lido novamente pelo endpoint
        async def receive():
            return {"type": "http.request", "body": body}
        request = Request(request.scope, receive)
    
    response = await call_next(request)
    return response

# Middleware de rate limiting
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Middleware para aplicar rate limiting"""
    try:
        # Aplica rate limiting apenas em endpoints de dados
        if request.url.path.startswith("/api/") and request.url.path != "/api/health":
            security_service.check_rate_limit(request)
        
        response = await call_next(request)
        return response
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"error": e.detail}
        )

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusão dos routers
app.include_router(data_router)
app.include_router(webhook_router)
app.include_router(auxiliary_router)
app.include_router(integrations_router)


@app.on_event("startup")
async def startup_event():
    """Evento executado na inicialização da aplicação"""
    logger.log_info("=== INICIANDO APLICAÇÃO ===")
    logger.log_info(f"Ambiente: {'Desenvolvimento' if settings.DEBUG else 'Produção'}")
    logger.log_info(f"Host: {settings.HOST}:{settings.PORT}")
    
    # Cria diretórios necessários
    try:
        os.makedirs(settings.LOGS_DIR, exist_ok=True)
        os.makedirs(settings.SCHEMAS_DIR, exist_ok=True)
        logger.log_info("Diretórios criados com sucesso")
    except Exception as e:
        logger.log_error(e, "Erro ao criar diretórios")
    
    # Log dos endpoints registrados
    logger.log_info("Endpoints registrados:")
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(route.methods)
            logger.log_info(f"  {methods} {route.path}")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento executado no encerramento da aplicação"""
    logger.log_info("=== ENCERRANDO APLICAÇÃO ===")


@app.get("/")
async def root():
    """Endpoint raiz da API"""
    return {
        "message": "MySQL to Supabase Data Replicator API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "docs": "/docs",
        "endpoints": {
            "data_reception": "/api/data/{empresa_id}",
            "schema_webhook": "/webhook/schema/{empresa_id}",
            "health_check": "/health",
            "companies": "/api/companies",
            "company_config": "/api/companies/{empresa_id}/config",
            "company_tables": "/api/companies/{empresa_id}/tables"
        }
    }


# Tratamento global de exceções
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handler global para exceções não tratadas"""
    logger.log_error(f"Exceção não tratada: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Erro interno do servidor",
            "message": str(exc) if settings.DEBUG else "Erro interno",
            "timestamp": datetime.now().isoformat()
        }
    )


if __name__ == "__main__":
    # Execução da aplicação
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )