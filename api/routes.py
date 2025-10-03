"""
Rotas da API FastAPI
"""

from fastapi import APIRouter

# Router principal que será incluído no main.py
router = APIRouter()

@router.get("/status")
async def api_status():
    """Endpoint para verificar status da API"""
    return {
        "api_status": "online",
        "version": "1.0.0",
        "endpoints": [
            "/api/v1/status",
            "/api/v1/receive-data",
            "/api/v1/receive-schema"
        ]
    }