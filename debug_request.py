#!/usr/bin/env python3
"""
Debug da requisição real para verificar o JSON enviado
"""

import json
import requests

# Dados do teste
mysql_integrator_payload = {
    "schema": {
        "database_name": "teste_db",
        "tables": [
            {
                "name": "cadastro_produtos",
                "columns": [
                    {
                        "name": "id",
                        "type": "int",
                        "nullable": False,
                        "is_primary_key": True,
                        "max_length": None
                    },
                    {
                        "name": "nome", 
                        "type": "varchar",
                        "nullable": False,
                        "is_primary_key": False,
                        "max_length": 255
                    },
                    {
                        "name": "preco",
                        "type": "decimal",
                        "nullable": True,
                        "is_primary_key": False,
                        "max_length": None
                    },
                    {
                        "name": "data_criacao",
                        "type": "datetime", 
                        "nullable": True,
                        "is_primary_key": False,
                        "max_length": None
                    }
                ],
                "record_count": 0
            }
        ]
    },
    "timestamp": "2025-10-02T17:21:58.470615",
    "source": "mysql_integrator_webhook"
}

print("🔍 Debug da Requisição")
print("=" * 50)

# Ver o JSON que será enviado
json_str = json.dumps(mysql_integrator_payload, indent=2)
print("📤 JSON que será enviado:")
print(json_str)

# Verificar se o JSON é válido
try:
    parsed = json.loads(json_str)
    print(f"\n✅ JSON é válido")
    print(f"   - Tipo do schema: {type(parsed['schema'])}")
    print(f"   - Número de tabelas: {len(parsed['schema']['tables'])}")
    print(f"   - Primeira tabela: {parsed['schema']['tables'][0]['name']}")
    print(f"   - Número de colunas: {len(parsed['schema']['tables'][0]['columns'])}")
except Exception as e:
    print(f"\n❌ JSON inválido: {e}")

# Testar contra o endpoint local
print(f"\n🧪 Testando contra endpoint local...")
try:
    from models.base_models import MySQLIntegratorSchema
    schema_obj = MySQLIntegratorSchema(**mysql_integrator_payload)
    print("✅ Modelo validado localmente com sucesso")
except Exception as e:
    print(f"❌ Erro na validação local: {e}")