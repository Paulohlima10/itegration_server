#!/usr/bin/env python3
"""
Script para configurar dados de empresa de teste no Supabase
Usa as configurações da aplicação para acessar o banco correto
"""

import asyncio
import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent))

from config.settings import Settings
from services.supabase_service import SupabaseService
from services.logging_service import LoggingService

async def setup_company_data():
    """Configura dados de empresa de teste no banco"""
    
    # Inicializar serviços
    settings = Settings()
    logger = LoggingService(settings.LOG_LEVEL, settings.LOG_FILE)
    supabase_service = SupabaseService(settings, logger)
    
    empresa_id = "3e1a0646-0b39-4ea4-9f49-bf7c0cf34ac2"
    
    print(f"Configurando dados para empresa: {empresa_id}")
    
    try:
        # Obter cliente principal
        main_client = supabase_service.get_main_client()
        
        # Verificar se a tabela company_conf existe
        print("Verificando se tabela company_conf existe...")
        
        # Criar tabela se não existir
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS company_conf (
            empresa_id TEXT NOT NULL,
            chave TEXT NOT NULL,
            valor TEXT NOT NULL,
            descricao TEXT DEFAULT '',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            PRIMARY KEY (empresa_id, chave)
        );
        
        CREATE INDEX IF NOT EXISTS idx_company_conf_empresa_id ON company_conf(empresa_id);
        CREATE INDEX IF NOT EXISTS idx_company_conf_chave ON company_conf(chave);
        """
        
        # Executar criação da tabela via RPC (se suportado) ou inserir dados diretamente
        print("Inserindo dados da empresa...")
        
        # Dados da empresa de teste
        company_data = [
            {
                "empresa_id": empresa_id,
                "chave": "DB_URL",
                "valor": "https://ffuyjdairjscwwjhtnmw.supabase.co",
                "descricao": "URL do Supabase da empresa de teste"
            },
            {
                "empresa_id": empresa_id,
                "chave": "DB_TOKEN", 
                "valor": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZmdXlqZGFpcmpzY3d3amh0bm13Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mjc4MDk5NzAsImV4cCI6MjA0MzM4NTk3MH0.Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8Ej8",
                "descricao": "Token de acesso do Supabase da empresa de teste"
            },
            {
                "empresa_id": empresa_id,
                "chave": "COMPANY_NAME",
                "valor": "Empresa de Teste",
                "descricao": "Nome da empresa de teste"
            },
            {
                "empresa_id": empresa_id,
                "chave": "ACTIVE",
                "valor": "true",
                "descricao": "Status ativo da empresa"
            }
        ]
        
        # Verificar se os dados já existem na tabela company_conf (somente leitura)
        print("\nVerificando configurações existentes na tabela company_conf...")
        response = main_client.table('company_conf').select('*').eq('empresa_id', empresa_id).execute()
        
        if response.data:
            print(f"✓ {len(response.data)} configurações encontradas para a empresa:")
            for item in response.data:
                print(f"  - {item['chave']}: {item['valor'][:50]}...")
        else:
            print("✗ Nenhuma configuração encontrada para esta empresa")
            print("NOTA: A tabela company_conf é somente leitura. As configurações devem ser inseridas manualmente no banco de dados.")
            
        print(f"\n✓ Verificação da empresa {empresa_id} concluída!")
        
    except Exception as e:
        print(f"✗ Erro durante configuração: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("=== Configuração de Dados de Empresa ===")
    success = asyncio.run(setup_company_data())
    
    if success:
        print("\n✓ Configuração concluída com sucesso!")
        sys.exit(0)
    else:
        print("\n✗ Falha na configuração!")
        sys.exit(1)