#!/usr/bin/env python3
"""
Script de debug para testar o schema MySQL Integrator
"""

import json
import requests
import sys

# Dados de teste simplificados
test_schema = {
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
                        "is_primary_key": True
                    },
                    {
                        "name": "nome",
                        "type": "varchar",
                        "nullable": False,
                        "is_primary_key": False,
                        "max_length": 255
                    }
                ]
            }
        ]
    },
    "timestamp": "2025-10-02T17:21:58.470615",
    "source": "mysql_integrator_webhook",
    "empresa_id": "3e1a0646-0b39-4ea4-9f49-bf7c0cf34ac2"
}

def test_simple_schema():
    """Testa schema simplificado"""
    print("🧪 Testando schema simplificado...")
    
    url = "http://localhost:8000/webhook/schema/3e1a0646-0b39-4ea4-9f49-bf7c0cf34ac2"
    
    try:
        response = requests.post(url, json=test_schema)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 422:
            print(f"❌ Erro de validação:")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
            return False
        elif response.status_code == 200:
            print(f"✅ Sucesso!")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
            return True
        else:
            print(f"⚠️  Status inesperado: {response.status_code}")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False

def test_schema_validation():
    """Testa validação do schema localmente"""
    print("\n🔍 Testando validação local...")
    
    try:
        from models.base_models import MySQLIntegratorSchema
        
        # Testa criar o modelo
        schema_obj = MySQLIntegratorSchema(**test_schema)
        print("✅ Modelo criado com sucesso!")
        
        # Testa conversão para SQL
        sql = schema_obj.convert_to_sql()
        print(f"✅ SQL gerado: {len(sql)} caracteres")
        print("SQL:")
        print(sql)
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na validação local: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Debug MySQL Integrator Schema")
    print("=" * 50)
    
    # Testa validação local primeiro
    local_ok = test_schema_validation()
    
    # Testa requisição
    print("\n" + "=" * 50)
    api_ok = test_simple_schema()
    
    print(f"\n📊 Resultados:")
    print(f"   Validação local: {'✅' if local_ok else '❌'}")
    print(f"   API request: {'✅' if api_ok else '❌'}")