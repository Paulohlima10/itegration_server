import asyncio
import requests
import json

async def test_upsert_fix():
    """Testar se o upsert agora funciona corretamente"""
    
    # Dados para teste
    test_data = {
        "table_name": "usuarios",
        "data": [
            {
                "id": 1,
                "nome": "João Silva Teste",
                "email": "joao@teste.com",
                "idade": 30
            }
        ]
    }
    
    try:
        # Fazer requisição POST para o endpoint /api/data
        response = requests.post(
            "http://localhost:8000/api/data/3e1a0646-0b39-4ea4-9f49-bf7c0cf34ac2",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        print(f"Resposta: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Sucesso: {result.get('message', 'Sem mensagem')}")
            print(f"Registros afetados: {result.get('records_affected', 0)}")
        else:
            print(f"Erro na requisição: {response.text}")
            
    except Exception as e:
        print(f"Erro ao fazer requisição: {e}")

if __name__ == "__main__":
    asyncio.run(test_upsert_fix())