"""
Script para configurar dados de teste para a empresa test_company_001
Este script simula a configuração de empresa sem depender do Supabase principal
"""

import json
import os
from pathlib import Path

def setup_test_company_config():
    """Configura dados de teste para a empresa test_company_001"""
    
    # Criar diretório de configurações de teste se não existir
    test_config_dir = Path("test_configs")
    test_config_dir.mkdir(exist_ok=True)
    
    # Configuração de teste para test_company_001
    test_company_config = {
        "test_company_001": {
            "DB_URL": "https://test-company.supabase.co",
            "DB_TOKEN": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test-token",
            "COMPANY_NAME": "Empresa de Teste 001",
            "ACTIVE": "true"
        }
    }
    
    # Salvar configuração em arquivo JSON
    config_file = test_config_dir / "company_configs.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(test_company_config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Configuração de teste salva em: {config_file}")
    print(f"📋 Empresa configurada: test_company_001")
    print(f"🔗 DB_URL: {test_company_config['test_company_001']['DB_URL']}")
    print(f"🔑 DB_TOKEN: {test_company_config['test_company_001']['DB_TOKEN'][:20]}...")
    
    return config_file

def create_mock_supabase_service():
    """Cria um serviço mock para testes"""
    
    mock_service_content = '''"""
Serviço mock do Supabase para testes
"""

import json
from pathlib import Path
from typing import Dict, Optional

class MockSupabaseService:
    """Serviço mock para testes sem conexão real com Supabase"""
    
    def __init__(self):
        self.config_file = Path("test_configs/company_configs.json")
        self._load_configs()
    
    def _load_configs(self):
        """Carrega configurações do arquivo JSON"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.configs = json.load(f)
        else:
            self.configs = {}
    
    async def get_company_config(self, empresa_id: str) -> Optional[Dict[str, str]]:
        """Obtém configuração de uma empresa"""
        return self.configs.get(empresa_id)
    
    def validate_empresa_id(self, empresa_id: str) -> bool:
        """Valida se a empresa existe e tem configurações mínimas"""
        config = self.configs.get(empresa_id)
        if not config:
            return False
        
        # Verificar se tem configurações mínimas
        required_keys = ['DB_URL', 'DB_TOKEN']
        return all(key in config for key in required_keys)

# Instância global para uso nos testes
mock_supabase = MockSupabaseService()
'''
    
    mock_file = Path("test_configs/mock_supabase_service.py")
    with open(mock_file, 'w', encoding='utf-8') as f:
        f.write(mock_service_content)
    
    print(f"✅ Serviço mock criado em: {mock_file}")
    return mock_file

if __name__ == "__main__":
    print("🚀 Configurando dados de teste...")
    
    # Configurar dados de teste
    config_file = setup_test_company_config()
    
    # Criar serviço mock
    mock_file = create_mock_supabase_service()
    
    print("\n✅ Configuração de teste concluída!")
    print("📝 Próximos passos:")
    print("   1. Execute os testes da API")
    print("   2. Os testes agora devem encontrar a empresa test_company_001")
    print("   3. Verifique os resultados em test_results.txt")