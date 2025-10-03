-- Função para executar SQL dinâmico (DDL/DML)
-- Execute este SQL no Dashboard do Supabase: https://supabase.com/dashboard/project/ffuyjdairjscwwjhtnmw/sql

CREATE OR REPLACE FUNCTION public.execute_sql(sql_query text)
RETURNS TABLE(status text, message text)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    is_ddl boolean := false;
BEGIN
    -- Executa SQL dinâmico
    EXECUTE sql_query;

    -- Detecta se é DDL básico
    is_ddl := lower(sql_query) LIKE 'create %'
           OR lower(sql_query) LIKE 'alter %'
           OR lower(sql_query) LIKE 'drop %'
           OR lower(sql_query) LIKE 'truncate %';

    IF is_ddl THEN
        -- Mitigação para notificações perdidas durante reload em andamento
        PERFORM pg_sleep(0.5);
        PERFORM pg_notify('pgrst', 'reload schema');
    END IF;

    -- Retorna uma linha tabular para compatibilidade com RPC do PostgREST
    RETURN QUERY SELECT 'success'::text, 'SQL executed successfully'::text;
    RETURN;
EXCEPTION WHEN OTHERS THEN
    RETURN QUERY SELECT 'error'::text, SQLERRM::text;
    RETURN;
END;
$$;

-- Grant permissões para execução
GRANT EXECUTE ON FUNCTION execute_sql(text) TO anon, authenticated;

-- Teste da função (opcional)
-- SELECT * FROM public.execute_sql('SELECT 1 as test_value');