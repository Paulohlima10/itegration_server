import asyncio
from services.supabase_service import SupabaseService
from services.logging_service import LoggingService
from config.settings import Settings

async def test():
    settings = Settings()
    logger = LoggingService(settings.LOG_LEVEL, settings.LOG_FILE)
    service = SupabaseService(settings, logger)
    
    config = await service.get_company_config('3e1a0646-0b39-4ea4-9f49-bf7c0cf34ac2')
    print(f'Config: {config}')
    
    if config:
        print(f'DB_URL in config: {"DB_URL" in config}')
        print(f'DB_TOKEN in config: {"DB_TOKEN" in config}')
        print(f'Keys: {list(config.keys())}')
    else:
        print('Config is None')

if __name__ == "__main__":
    asyncio.run(test())