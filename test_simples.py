import requests
import json

# Teste simples de upsert
test_data = {
    "table_name": "usuarios",
    "data": [
        {
            "nome": "João Silva Teste",
            "email": "joao@teste.com",
            "idade": 30
        }
    ]
}

try:
    response = requests.post(
        "http://localhost:8000/api/data/3e1a0646-0b39-4ea4-9f49-bf7c0cf34ac2",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Resposta: {response.text}")
    
except Exception as e:
    print(f"Erro: {e}")