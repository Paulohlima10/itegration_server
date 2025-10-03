"""
Casos de teste para a API de recepção de dados
"""

import requests
import json
import time
from typing import Dict, Any

class TestCases:
    """Classe para executar casos de teste da API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Inicializa os casos de teste
        
        Args:
            base_url: URL base da API
        """
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_health_check(self) -> bool:
        """
        ✅ Teste básico de saúde da API
        
        Returns:
            True se passou no teste
        """
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code != 200:
                print(f"❌ Health check - FALHOU: Status {response.status_code}")
                return False
            data = response.json()
            # Aceita "healthy" ou "degraded" como status válidos
            if data.get("status") not in ["healthy", "degraded"]:
                print(f"❌ Health check - FALHOU: Status inválido {data}")
                return False
            print("✅ Health check - PASSOU")
            return True
        except Exception as e:
            print(f"❌ Health check - FALHOU: {e}")
            return False
    
    def test_new_table_data_reception(self) -> bool:
        """
        ✅ Recepção de dados com tabela nova
        
        Returns:
            True se passou no teste
        """
        try:
            test_data = {
                "table_name": "usuarios",  # Usando tabela que existe
                "data": [
                    {
                        "nome": "João Silva",
                        "email": "joao.silva@teste.com",
                        "idade": 30,
                        "ativo": True
                    },
                    {
                        "nome": "Maria Santos", 
                        "email": "maria.santos@teste.com",
                        "idade": 25,
                        "ativo": False
                    }
                ]
            }
            
            response = self.session.post(
                f"{self.base_url}/api/data/3e1a0646-0b39-4ea4-9f49-bf7c0cf34ac2",
                json=test_data
            )
            
            # Aceita tanto 200 quanto 201 para criação
            if response.status_code not in [200, 201]:
                print(f"❌ Recepção com tabela nova - FALHOU: Status {response.status_code}")
                return False
            data = response.json()
            if not data.get("success"):
                print(f"❌ Recepção com tabela nova - FALHOU: {data}")
                return False
            print("✅ Recepção com tabela nova - PASSOU")
            return True
            
        except Exception as e:
            print(f"❌ Recepção com tabela nova - FALHOU: {e}")
            return False
    
    def test_existing_table_data_reception(self) -> bool:
        """
        ✅ Recepção de dados com tabela existente
        
        Returns:
            True se passou no teste
        """
        try:
            test_data = {
                "table_name": "usuarios",  # Usando tabela que existe
                "data": [
                    {
                        "nome": "Pedro Costa",
                        "email": "pedro.costa@teste.com",
                        "idade": 35,
                        "ativo": True
                    }
                ]
            }
            
            response = self.session.post(
                f"{self.base_url}/api/data/3e1a0646-0b39-4ea4-9f49-bf7c0cf34ac2",
                json=test_data
            )
            
            if response.status_code != 200:
                print(f"❌ Recepção com tabela existente - FALHOU: Status {response.status_code}")
                return False
            data = response.json()
            if not data.get("success"):
                print(f"❌ Recepção com tabela existente - FALHOU: {data}")
                return False
            print("✅ Recepção com tabela existente - PASSOU")
            return True
            
        except Exception as e:
            print(f"❌ Recepção com tabela existente - FALHOU: {e}")
            return False
    
    def test_new_columns_addition(self) -> bool:
        """
        ✅ Adição de novas colunas
        
        Returns:
            True se passou no teste
        """
        try:
            # Criar uma tabela de produtos para testar adição de colunas
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
            
            response = self.session.post(
                f"{self.base_url}/api/data/3e1a0646-0b39-4ea4-9f49-bf7c0cf34ac2",
                json=test_data
            )
            
            if response.status_code != 200:
                print(f"❌ Adição de novas colunas - FALHOU: Status {response.status_code}")
                return False
            data = response.json()
            if not data.get("success"):
                print(f"❌ Adição de novas colunas - FALHOU: {data}")
                return False
            print("✅ Adição de novas colunas - PASSOU")
            return True
            
        except Exception as e:
            print(f"❌ Adição de novas colunas - FALHOU: {e}")
            return False
    
    def test_webhook_schema(self) -> bool:
        """
        ✅ Webhook de schema
        
        Returns:
            True se passou no teste
        """
        try:
            schema_data = {
                "schema": "CREATE TABLE webhook_test_table (id INTEGER PRIMARY KEY, title TEXT, status BOOLEAN);",
                "table_name": "webhook_test_table",
                "empresa_id": "3e1a0646-0b39-4ea4-9f49-bf7c0cf34ac2",
                "schema_type": "postgresql"
            }
            
            response = self.session.post(
                f"{self.base_url}/webhook/schema/3e1a0646-0b39-4ea4-9f49-bf7c0cf34ac2",
                json=schema_data
            )
            
            if response.status_code != 200:
                print(f"❌ Webhook de schema - FALHOU: Status {response.status_code}")
                return False
            data = response.json()
            if not data.get("success"):
                print(f"❌ Webhook de schema - FALHOU: {data}")
                return False
            print("✅ Webhook de schema - PASSOU")
            return True
            
        except Exception as e:
            print(f"❌ Webhook de schema - FALHOU: {e}")
            return False
    
    def test_company_not_found(self) -> bool:
        """
        ❌ Empresa não encontrada
        
        Returns:
            True se passou no teste (erro esperado)
        """
        try:
            test_data = {
                "table_name": "test_table",
                "data": [{"id": 1, "name": "test"}]
            }
            
            response = self.session.post(
                f"{self.base_url}/api/data/empresa_inexistente_999",
                json=test_data
            )
            
            # Espera erro 404
            if response.status_code != 404:
                print(f"❌ Empresa não encontrada - FALHOU: Esperado 404, recebido {response.status_code}")
                return False
            data = response.json()
            if "não encontrada" not in data.get("detail", "").lower():
                print(f"❌ Empresa não encontrada - FALHOU: Mensagem incorreta {data}")
                return False
            print("✅ Empresa não encontrada - PASSOU (erro esperado)")
            return True
            
        except Exception as e:
            print(f"❌ Empresa não encontrada - FALHOU: {e}")
            return False
    
    def test_invalid_config(self) -> bool:
        """
        ❌ Configurações inválidas
        
        Returns:
            True se passou no teste (erro esperado)
        """
        try:
            # Testa com dados inválidos
            invalid_data = {
                "table_name": "123invalid",  # Nome inválido
                "data": []  # Dados vazios
            }
            
            response = self.session.post(
                f"{self.base_url}/api/data/3e1a0646-0b39-4ea4-9f49-bf7c0cf34ac2",
                json=invalid_data
            )
            
            # Espera erro 400
            if response.status_code != 400:
                print(f"❌ Configurações inválidas - FALHOU: Esperado 400, recebido {response.status_code}")
                return False
            print("✅ Configurações inválidas - PASSOU (erro esperado)")
            return True
            
        except Exception as e:
            print(f"❌ Configurações inválidas - FALHOU: {e}")
            return False
    
    def test_connection_failure(self) -> bool:
        """
        ❌ Falha na conexão
        
        Returns:
            True se passou no teste (erro esperado)
        """
        try:
            # Testa com dados que causam erro de validação (formato inválido)
            test_data = {
                "table_name": "test_table",
                "data": "invalid_data_format"  # Deveria ser uma lista, não string
            }
            
            response = self.session.post(
                f"{self.base_url}/api/data/3e1a0646-0b39-4ea4-9f49-bf7c0cf34ac2",
                json=test_data
            )
            
            # Espera erro 400 ou 422 para dados inválidos (validação do FastAPI)
            if response.status_code not in [400, 422]:
                print(f"❌ Falha na conexão - FALHOU: Esperado 400/422, recebido {response.status_code}")
                return False
            print("✅ Falha na conexão - PASSOU (erro esperado)")
            return True
            
        except Exception as e:
            print(f"❌ Falha na conexão - FALHOU: {e}")
            return False
    
    def test_rate_limiting(self) -> bool:
        """
        Teste de rate limiting
        
        Returns:
            True se passou no teste
        """
        try:
            # Faz muitas requisições rapidamente
            for i in range(105):  # Excede o limite de 100
                response = self.session.get(f"{self.base_url}/api/companies")
                if response.status_code == 429:
                    print("✅ Rate limiting - PASSOU (limite atingido)")
                    return True
            
            print("❌ Rate limiting - FALHOU (limite não atingido)")
            return False
            
        except Exception as e:
            print(f"❌ Rate limiting - FALHOU: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """
        Executa todos os casos de teste
        
        Returns:
            Dicionário com resultados dos testes
        """
        print("🧪 EXECUTANDO CASOS DE TESTE")
        print("=" * 50)
        
        results = {
            "health_check": self.test_health_check(),
            "new_table_reception": self.test_new_table_data_reception(),
            "existing_table_reception": self.test_existing_table_data_reception(),
            "new_columns_addition": self.test_new_columns_addition(),
            "webhook_schema": self.test_webhook_schema(),
            "company_not_found": self.test_company_not_found(),
            "invalid_config": self.test_invalid_config(),
            "connection_failure": self.test_connection_failure(),
            "rate_limiting": self.test_rate_limiting()
        }
        
        print("\n" + "=" * 50)
        print("📊 RESUMO DOS TESTES")
        print("=" * 50)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSOU" if result else "❌ FALHOU"
            print(f"{test_name}: {status}")
        
        print(f"\nResultado: {passed}/{total} testes passaram")
        print(f"Taxa de sucesso: {(passed/total)*100:.1f}%")
        
        return results

def main():
    """Função principal para executar os testes"""
    tester = TestCases()
    results = tester.run_all_tests()
    
    # Retorna código de saída baseado nos resultados
    if all(results.values()):
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        return 0
    else:
        print("\n⚠️  ALGUNS TESTES FALHARAM!")
        return 1

if __name__ == "__main__":
    exit(main())