-- Script para criar tabela company_conf no Supabase Principal
-- Esta tabela armazena as configurações de cada empresa/cliente

CREATE TABLE IF NOT EXISTS company_conf (
    empresa_id TEXT NOT NULL,
    chave TEXT NOT NULL,
    valor TEXT NOT NULL,
    descricao TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Chave primária composta
    PRIMARY KEY (empresa_id, chave)
);

-- Índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_company_conf_empresa_id ON company_conf(empresa_id);
CREATE INDEX IF NOT EXISTS idx_company_conf_chave ON company_conf(chave);

-- Comentários para documentação
COMMENT ON TABLE company_conf IS 'Configurações por empresa/cliente';
COMMENT ON COLUMN company_conf.empresa_id IS 'Identificador único da empresa';
COMMENT ON COLUMN company_conf.chave IS 'Nome da configuração (ex: DB_URL, DB_TOKEN)';
COMMENT ON COLUMN company_conf.valor IS 'Valor da configuração';
COMMENT ON COLUMN company_conf.descricao IS 'Descrição opcional da configuração';

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_company_conf_updated_at 
    BEFORE UPDATE ON company_conf 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Inserir dados de exemplo (opcional - remover em produção)
INSERT INTO company_conf (empresa_id, chave, valor, descricao) VALUES
('empresa_exemplo', 'DB_URL', 'https://exemplo.supabase.co', 'URL do Supabase da empresa exemplo'),
('empresa_exemplo', 'DB_TOKEN', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...', 'Token de acesso do Supabase da empresa exemplo')
ON CONFLICT (empresa_id, chave) DO NOTHING;

-- Verificar se a tabela foi criada corretamente
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'company_conf'
ORDER BY ordinal_position;