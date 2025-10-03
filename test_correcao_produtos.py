import requests
import json

# Testar a correção com dados de produtos estruturados corretamente
test_data = {
    "table_name": "produtos_teste",
    "data": [
        {
            "id": 1,
            "nome": "Produto com Nova Coluna",
            "preco": 199.99,
            "ativo": True,
            "criado_em": "2024-01-04T16:00:00",
            "categoria": "Eletrônicos",  # Nova coluna
            "peso": 1.5,  # Nova coluna
            "tags": ["novo", "popular"]  # Nova coluna JSON
        }
    ]
}

try:
    # Testar na porta 8000 (onde o servidor já está rodando)
    response = requests.post(
        "http://localhost:8000/api/data/3e1a0646-0b39-4ea4-9f49-bf7c0cf34ac2",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Resposta: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Sucesso: {result.get('message', 'Sem mensagem')}")
        print(f"Registros afetados: {result.get('records_inserted', 0)}")
    else:
        print(f"❌ Erro na requisição: {response.text}")
        
except Exception as e:
    print(f"❌ Erro ao fazer requisição: {e}")