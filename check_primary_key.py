import asyncio
from services.supabase_service import SupabaseService
from services.logging_service import LoggingService
from config.settings import Settings

async def check_primary_key():
    settings = Settings()
    logger = LoggingService(settings.LOG_LEVEL, settings.LOG_FILE)
    service = SupabaseService(settings, logger)
    
    empresa_id = '3e1a0646-0b39-4ea4-9f49-bf7c0cf34ac2'
    
    # Verificar qual coluna é a PRIMARY KEY
    query = '''
    SELECT 
        kcu.column_name,
        tc.constraint_name,
        tc.constraint_type
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu 
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
    WHERE tc.table_schema = 'public' 
        AND tc.table_name = 'usuarios'
        AND tc.constraint_type = 'PRIMARY KEY';
    '''
    
    result = await service.execute_query(empresa_id, query)
    if result:
        print('Coluna(s) PRIMARY KEY da tabela usuarios:')
        for row in result:
            print(f'  {row}')
    else:
        print('Nenhuma PRIMARY KEY encontrada')
    
    # Verificar se a coluna id é nullable
    nullable_query = '''
    SELECT 
        column_name,
        is_nullable,
        column_default
    FROM information_schema.columns 
    WHERE table_schema = 'public' 
        AND table_name = 'usuarios'
        AND column_name = 'id';
    '''
    
    nullable_result = await service.execute_query(empresa_id, nullable_query)
    if nullable_result:
        print('Propriedades da coluna id:')
        for row in nullable_result:
            print(f'  {row}')

if __name__ == "__main__":
    asyncio.run(check_primary_key())