#!/usr/bin/env python3
"""
Teste para o novo formato MySQL Integrator Schema
"""

import requests
import json
from datetime import datetime

def test_mysql_integrator_schema():
    """Testa o envio de schema no formato do MySQL Integrator"""
    
    # URL do endpoint
    url = "http://localhost:8000/webhook/schema/3e1a0646-0b39-4ea4-9f49-bf7c0cf34ac2"
    
    # Dados no formato que seu sistema envia
    payload = {
        "schema": {
            "database_name": "automatiza",
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
        "timestamp": datetime.now().isoformat(),
        "source": "mysql_integrator_webhook",
        "empresa_id": "3e1a0646-0b39-4ea4-9f49-bf7c0cf34ac2"
    }
    
    # Headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        print("🧪 Testando novo formato MySQL Integrator Schema...")
        print(f"📡 Endpoint: {url}")
        print(f"📦 Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        # Fazer a requisição
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"\n📊 Status Code: {response.status_code}")
        print(f"📋 Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            print("\n✅ Sucesso! Schema recebido e processado com o novo formato.")
            return True
        else:
            print(f"\n❌ Erro: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Erro: Não foi possível conectar ao servidor. Certifique-se de que ele está rodando.")
        return False
    except Exception as e:
        print(f"\n❌ Erro inesperado: {str(e)}")
        return False

def test_formato_tradicional():
    """Testa o formato tradicional para garantir retrocompatibilidade"""
    
    # URL do endpoint
    url = "http://localhost:8000/webhook/schema/3e1a0646-0b39-4ea4-9f49-bf7c0cf34ac2"
    
    # Dados no formato tradicional
    payload = {
        "schema": "CREATE TABLE teste_tradicional (id INTEGER PRIMARY KEY, nome VARCHAR(100) NOT NULL);",
        "table_name": "teste_tradicional",
        "schema_type": "mysql"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        print("\n🧪 Testando formato tradicional (retrocompatibilidade)...")
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            print("\n✅ Sucesso! Formato tradicional ainda funciona.")
            return True
        else:
            print(f"\n❌ Erro: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando testes do endpoint /webhook/schema/")
    print("=" * 60)
    
    # Testar novo formato
    sucesso_novo = test_mysql_integrator_schema()
    
    print("\n" + "=" * 60)
    
    # Testar formato tradicional
    sucesso_tradicional = test_formato_tradicional()
    
    print("\n" + "=" * 60)
    print("📊 Resumo dos Testes:")
    print(f"   Novo formato MySQL Integrator: {'✅' if sucesso_novo else '❌'}")
    print(f"   Formato tradicional: {'✅' if sucesso_tradicional else '❌'}")
    
    if sucesso_novo and sucesso_tradicional:
        print("\n🎉 Todos os testes passaram! O endpoint está funcionando com ambos os formatos.")
    else:
        print("\n⚠️  Alguns testes falharam. Verifique os logs acima.")