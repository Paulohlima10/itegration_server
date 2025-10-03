"""
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
