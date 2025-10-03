import asyncio
from services.supabase_service import SupabaseService
from services.logging_service import LoggingService
from config.settings import Settings

async def check_table():
    settings = Settings()
    logger = LoggingService(settings.LOG_LEVEL, settings.LOG_FILE)
    service = SupabaseService(settings, logger)
    
    empresa_id = '3e1a0646-0b39-4ea4-9f49-bf7c0cf34ac2'
    
    # Verificar se a tabela existe
    exists = await service.table_exists_postgres(empresa_id, 'usuarios')
    print(f'Tabela usuarios existe: {exists}')
    
    # Verificar estrutura da tabela
    query = '''
    SELECT 
        column_name,
        data_type,
        is_nullable,
        column_default,
        character_maximum_length
    FROM information_schema.columns 
    WHERE table_schema = 'public' AND table_name = 'usuarios'
    ORDER BY ordinal_position;
    '''
    
    result = await service.execute_query(empresa_id, query)
    if result:
        print('Estrutura da tabela usuarios:')
        for row in result:
            print(f'  {row}')
    else:
        print('Tabela não encontrada ou erro na consulta')
    
    # Verificar constraints
    constraints_query = '''
    SELECT 
        constraint_name,
        constraint_type
    FROM information_schema.table_constraints 
    WHERE table_schema = 'public' AND table_name = 'usuarios';
    '''
    
    constraints = await service.execute_query(empresa_id, constraints_query)
    if constraints:
        print('Constraints da tabela usuarios:')
        for row in constraints:
            print(f'  {row}')
    else:
        print('Nenhuma constraint encontrada')

if __name__ == "__main__":
    asyncio.run(check_table())