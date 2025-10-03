"""
Serviço para operações com Supabase
Implementa conexões com o banco principal e bancos dos clientes
"""

from typing import Dict, List, Any, Optional, Tuple
import asyncio
import asyncpg
from datetime import datetime
from urllib.parse import quote, urlparse, urlunparse
from supabase import create_client, Client
from config.settings import Settings
from models.base_models import CompanyConfig, TableSchema, ColumnDefinition
from services.logging_service import LoggingService


class ConnectionPool:
    """Gerenciador de pool de conexões para bancos de clientes"""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.pools: Dict[str, asyncpg.Pool] = {}
        self.connection_counts: Dict[str, int] = {}
    
    async def get_pool(self, empresa_id: str, db_url: str) -> Optional[asyncpg.Pool]:
        """Obtém pool de conexões para uma empresa"""
        if empresa_id not in self.pools:
            try:
                pool = await asyncpg.create_pool(
                    db_url,
                    min_size=1,
                    max_size=self.max_connections,
                    command_timeout=30,
                    statement_cache_size=0
                )
                self.pools[empresa_id] = pool
                self.connection_counts[empresa_id] = 0
                return pool
            except Exception:
                return None
        
        return self.pools[empresa_id]
    
    async def close_pool(self, empresa_id: str):
        """Fecha pool de conexões de uma empresa"""
        if empresa_id in self.pools:
            await self.pools[empresa_id].close()
            del self.pools[empresa_id]
            self.connection_counts.pop(empresa_id, None)
    
    async def close_all_pools(self):
        """Fecha todos os pools de conexões"""
        for empresa_id in list(self.pools.keys()):
            await self.close_pool(empresa_id)


class SupabaseService:
    """Serviço para gerenciar conexões e operações com Supabase"""
    
    def __init__(self, settings: Settings, logger: LoggingService):
        self.settings = settings
        self.logger = logger
        # Removido cache global de clientes para evitar problemas de concorrência
        # self._main_client: Optional[Client] = None
        # self._client_connections: Dict[str, Client] = {}
        self._connection_pool = ConnectionPool()
        self._client_db_configs: Dict[str, Dict[str, str]] = {}
        
    def get_main_client(self) -> Client:
        """Cria um cliente isolado do Supabase principal (sem cache para evitar problemas de concorrência)"""
        try:
            client = create_client(
                self.settings.SUPABASE_MAIN_URL,
                self.settings.SUPABASE_MAIN_KEY
            )
            self.logger.log_info("Cliente Supabase principal criado (isolado)")
            return client
        except Exception as e:
            self.logger.log_error(f"Erro ao criar cliente Supabase principal: {str(e)}")
            raise
    
    async def connect_to_client_db(self, db_url: str, db_token: str) -> Optional[Client]:
        """
        Conecta a um banco de dados específico do cliente
        """
        try:
            client = create_client(db_url, db_token)
            try:
                client.auth.get_session()
                self.logger.log_info(f"Conexão estabelecida com banco cliente: {db_url}")
                return client
            except:
                self.logger.log_info(f"Conexão estabelecida com banco cliente (sem auth): {db_url}")
                return client
                
        except Exception as e:
            self.logger.log_error(f"Erro ao conectar com banco cliente {db_url}: {str(e)}")
            return None
    
    async def get_client_connection(self, empresa_id: str) -> Optional[Client]:
        """
        Cria uma conexão cliente Supabase isolada para uma empresa específica (sem cache)
        """
        try:
            config = await self.get_company_config(empresa_id)
            if not config:
                self.logger.log_error(f"Configuração não encontrada para empresa: {empresa_id}")
                return None
            
            db_url = config.get('DB_URL')
            db_token = config.get('DB_TOKEN')
            
            if not db_url or not db_token:
                self.logger.log_error(f"Configurações de banco incompletas para empresa: {empresa_id}")
                return None
            
            client = await self.connect_to_client_db(db_url, db_token)
            
            if client:
                self.logger.log_info(f"Cliente Supabase isolado criado para empresa: {empresa_id}")
            else:
                self.logger.log_error(f"Falha ao criar cliente Supabase para empresa: {empresa_id}")
            
            return client
            
        except Exception as e:
            self.logger.log_error(f"Erro ao criar conexão cliente para empresa {empresa_id}: {str(e)}")
            return None

    async def table_exists(self, empresa_id: str, table_name: str) -> bool:
        """Verifica se uma tabela existe no banco de dados do cliente."""
        query = f"""
        SELECT EXISTS (
            SELECT FROM 
                pg_tables
            WHERE 
                schemaname = 'public' AND 
                tablename  = '{table_name}'
        );
        """
        try:
            result = await self.execute_query(empresa_id, query)
            return result[0]['exists'] if result else False
        except Exception as e:
            self.logger.log_error(f"Erro ao verificar a existência da tabela '{table_name}': {str(e)}")
            return False

    async def invalidate_client_connection(self, empresa_id: str):
        """Método mantido para compatibilidade mas sem efeito (clientes não são mais cacheados)"""
        self.logger.log_info(f"Método invalidate_client_connection chamado para empresa {empresa_id} (sem efeito - clientes não cacheados)")

    async def get_connection_pool(self, empresa_id: str) -> Optional[asyncpg.Pool]:
        """
        Obtém pool de conexões para uma empresa específica.
        Prioriza a DATABASE_URL do .env se disponível.
        """
        postgres_url = None
        try:
            # Prioridade 1: Usar DATABASE_URL do .env se estiver definida
            if self.settings.DATABASE_URL:
                self.logger.log_info(f"Tentando obter pool de conexões com DATABASE_URL do .env para empresa: {empresa_id}")
                
                raw_url = self.settings.DATABASE_URL
                try:
                    parsed_url = urlparse(raw_url)
                    if parsed_url.password:
                        encoded_password = quote(parsed_url.password)
                        netloc = f"{parsed_url.username}:{encoded_password}@{parsed_url.hostname}"
                        if parsed_url.port:
                            netloc += f":{parsed_url.port}"
                        postgres_url = urlunparse(parsed_url._replace(netloc=netloc))
                    else:
                        postgres_url = raw_url
                except Exception as e:
                    self.logger.log_error(f"Erro ao analisar a DATABASE_URL: {e}")
                    postgres_url = raw_url # Fallback para a URL original em caso de erro

            # Prioridade 2: Construir a URL a partir da configuração da empresa
            else:
                self.logger.log_info(f"DATABASE_URL não definida. Construindo URL a partir da config da empresa: {empresa_id}")
                if empresa_id not in self._client_db_configs:
                    config = await self.get_company_config(empresa_id)
                    if not config:
                        self.logger.log_error(f"Configuração não encontrada para empresa: {empresa_id}")
                        return None
                    self._client_db_configs[empresa_id] = config
                
                config = self._client_db_configs[empresa_id]
                db_url = config.get('DB_URL') # e.g., https://project.supabase.co
                
                if not db_url:
                    self.logger.log_error(f"URL do banco (DB_URL) não configurada para empresa: {empresa_id}")
                    return None
                
                # A senha pode ser o DB_TOKEN específico da empresa ou o DATABASE_SECRET global
                password = config.get('DB_TOKEN') or self.settings.DATABASE_SECRET
                
                if not password:
                    self.logger.log_error(f"Nenhuma senha de banco de dados (DB_TOKEN ou DATABASE_SECRET) encontrada para a empresa: {empresa_id}")
                    return None

                postgres_url = self._convert_supabase_to_postgres_url(db_url, password)

            if not postgres_url:
                self.logger.log_error(f"Não foi possível determinar a URL do PostgreSQL para a empresa: {empresa_id}")
                return None

            # Tenta obter/criar o pool de conexão
            pool = await self._connection_pool.get_pool(empresa_id, postgres_url)
            
            if pool:
                self.logger.log_info(f"Pool de conexões obtido com sucesso para empresa: {empresa_id}")
                return pool
            else:
                self.logger.log_error(
                    f"Falha ao obter pool de conexões para empresa: {empresa_id} com a URL: {postgres_url}. Verifique se as credenciais (DB_TOKEN/DATABASE_SECRET/DATABASE_URL) estão corretas e são a senha do Postgres, não uma API key."
                )
                return None
            
        except Exception as e:
            self.logger.log_error(f"Erro excepcional ao obter pool de conexões para empresa {empresa_id}: {str(e)}")
            return None

    async def execute_query(self, empresa_id: str, query: str, params: Optional[List[Any]] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Executa uma query no banco de dados de uma empresa
        """
        pool = None
        connection = None
        
        try:
            pool = await self.get_connection_pool(empresa_id)
            if not pool:
                return None
            
            connection = await pool.acquire()
            
            ddl = query.strip().lower().startswith(("create ", "alter ", "drop "))

            if ddl:
                await connection.execute(query)
                result = []
                self.logger.log_info(f"DDL executado: {query}. Notificando PostgREST para recarregar o schema.")
                try:
                    # Notifica o PostgREST para recarregar o cache do schema
                    await connection.execute("NOTIFY pgrst, 'reload schema'")
                    self.logger.log_info("Notificação de recarregamento de schema enviada para pgrst.")
                except Exception as notify_err:
                    self.logger.log_error(f"Falha ao notificar o recarregamento do schema do PostgREST: {str(notify_err)}")
            else:
                if params:
                    # Usar fetch sem preparar statements explicitamente (statement_cache_size=0 já aplicado no pool)
                    result = await connection.fetch(query, *params)
                else:
                    result = await connection.fetch(query)
            
            results = [dict(row) for row in result]
            
            self.logger.log_database_operation(
                operation="EXECUTE_QUERY",
                table="custom_query",
                client_id=empresa_id,
                success=True
            )
            
            return results
            
        except Exception as e:
            self.logger.log_error(f"Erro ao executar query para empresa {empresa_id}: {str(e)}")
            raise e
            
        finally:
            if connection and pool:
                await pool.release(connection)
    
    def _convert_supabase_to_postgres_url(self, supabase_url: str, token: str) -> str:
        """
        Converte URL do Supabase para URL PostgreSQL
        """
        try:
            if 'supabase.co' in supabase_url:
                project_id = supabase_url.replace('https://', '').replace('.supabase.co', '')
                encoded_token = quote(token or '', safe='')
                postgres_url = f"postgresql://postgres:{encoded_token}@db.{project_id}.supabase.co:5432/postgres"
                return postgres_url
            
            return supabase_url
            
        except Exception as e:
            self.logger.log_error(f"Erro ao converter URL: {str(e)}")
            return supabase_url

    async def get_all_companies(self) -> List[str]:
        """Busca todas as empresas únicas cadastradas no banco principal"""
        try:
            main_client = self.get_main_client()
            response = main_client.table('company_conf').select('empresa_id').execute()
            
            if not response.data:
                return []
            
            # Extrair empresa_id únicos
            companies = list(set(item['empresa_id'] for item in response.data if item.get('empresa_id')))
            
            self.logger.log_database_operation(
                operation="SELECT",
                table="company_conf",
                client_id="all_companies"
            )
            
            return companies
            
        except Exception as e:
            self.logger.log_error(f"Erro ao buscar todas as empresas: {str(e)}")
            return []

    async def get_table_info(self, empresa_id: str) -> List[Dict[str, Any]]:
        """Obtém informações das tabelas de uma empresa"""
        try:
            query = """
            SELECT 
                table_name,
                pg_size_pretty(pg_total_relation_size(quote_ident(table_name)::regclass)) as size
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            ORDER BY table_name;
            """
            
            result = await self.execute_query(empresa_id, query)
            return result if result else []
            
        except Exception as e:
            self.logger.log_error(f"Erro ao obter informações das tabelas da empresa {empresa_id}: {str(e)}")
            return []

    async def get_company_config(self, empresa_id: str) -> Optional[Dict[str, str]]:
        """Busca configurações de uma empresa no banco principal"""
        try:
            main_client = self.get_main_client()
            response = main_client.table('company_conf').select('chave, valor').eq('empresa_id', empresa_id).execute()
            
            if not response.data:
                return None
            
            config = {item['chave']: item['valor'] for item in response.data}
            
            self.logger.log_database_operation(
                operation="SELECT",
                table="company_conf",
                client_id=empresa_id
            )
            
            return config
            
        except Exception as e:
            self.logger.log_error(f"Erro ao buscar configurações da empresa {empresa_id}: {str(e)}")
            return None
    
    async def save_company_config(self, config: CompanyConfig) -> bool:
        """Salva configuração de empresa no banco principal"""
        try:
            if not config.validate_config():
                self.logger.log_error("Configuração inválida fornecida")
                return False
            
            main_client = self.get_main_client()
            
            existing = main_client.table('company_conf').select('*').eq('empresa_id', config.empresa_id).eq('chave', config.chave).execute()
            
            config_data = {
                'empresa_id': config.empresa_id,
                'chave': config.chave,
                'valor': config.valor,
                'descricao': config.descricao
            }
            
            if existing.data:
                response = main_client.table('company_conf').update(config_data).eq('empresa_id', config.empresa_id).eq('chave', config.chave).execute()
                operation = "UPDATE"
            else:
                response = main_client.table('company_conf').insert(config_data).execute()
                operation = "INSERT"
            
            if response.data:
                self.logger.log_database_operation(
                    operation=operation,
                    table="company_conf",
                    client_id=config.empresa_id,
                    success=True
                )
                return True
            
            return False
            
        except Exception as e:
            self.logger.log_error(f"Erro ao salvar configuração: {str(e)}")
            return False

    async def table_exists_postgres(self, empresa_id: str, table_name: str) -> bool:
        """Verifica se uma tabela existe tentando uma consulta direta."""
        query = f'SELECT 1 FROM public."{table_name}" LIMIT 1;'
        try:
            # Usamos execute_query, mas ignoramos o resultado. 
            # O sucesso ou falha da execução é o que importa.
            await self.execute_query(empresa_id, query)
            # Se a query for bem-sucedida, a tabela existe.
            return True
        except Exception as e:
            # Se a exceção for de tabela indefinida, significa que a tabela não existe.
            # asyncpg.exceptions.UndefinedTableError é o esperado, mas pode vir encapsulado.
            if "UndefinedTableError" in str(e) or "does not exist" in str(e):
                self.logger.log_info(f"A tabela '{table_name}' não existe (verificado por consulta direta).")
                return False
            # Se for outra exceção, logamos como erro, mas consideramos que a tabela não existe para evitar falhas.
            self.logger.log_error(f"Erro inesperado ao verificar existência da tabela '{table_name}': {e}")
            return False

    async def upsert_data(self, empresa_id: str, table_name: str, data: List[Dict[str, Any]]) -> Tuple[bool, str, int]:
        """
        Centraliza a lógica de verificação, criação/alteração de tabela e inserção de dados.
        """
        if not data:
            self.logger.log_warning("Nenhum dado fornecido para inserção.")
            return True, "Nenhum dado fornecido.", 0

        try:
            client = await self.get_client_connection(empresa_id)
            if not client:
                message = f"Não foi possível obter conexão para a empresa {empresa_id}."
                self.logger.log_error(message)
                return False, message, 0

            table_exists = await self.table_exists_postgres(empresa_id, table_name)
            inferred_schema = self._infer_schema_from_data(empresa_id, table_name, data)

            if not table_exists:
                self.logger.log_info(f"Tabela '{table_name}' não existe. Criando...")
                create_sql = inferred_schema.get_create_table_sql()
                
                await self.execute_query(empresa_id, create_sql)
                
                # Forçar o recarregamento do schema do PostgREST e invalidar a conexão
                self.logger.log_info("Forçando o recarregamento do schema do PostgREST e invalidando a conexão...")
                await self.execute_query(empresa_id, "NOTIFY pgrst, 'reload schema'")
                await self.invalidate_client_connection(empresa_id)
                
                # Pausa curta para dar tempo ao PostgREST para recarregar
                await asyncio.sleep(1)

                client = await self.get_client_connection(empresa_id) # Re-obter o cliente
                if not client:
                    message = f"Não foi possível re-obter conexão para a empresa {empresa_id} após criação de tabela."
                    self.logger.log_error(message)
                    return False, message, 0

                if not await self.table_exists_postgres(empresa_id, table_name):
                     message = f"Falha ao criar a tabela '{table_name}' mesmo após notificação e reconexão."
                     self.logger.log_error(message)
                     return False, message, 0
                self.logger.log_info(f"Tabela '{table_name}' criada com sucesso.")
            else:
                self.logger.log_info(f"Tabela '{table_name}' já existe. Verificando e adicionando colunas ausentes...")
                await self._compare_and_alter_table(empresa_id, table_name, inferred_schema)

            self.logger.log_info(f"Inserindo/atualizando dados na tabela '{table_name}'.")
            
            # Detectar a coluna PRIMARY KEY real da tabela, não do schema inferido
            pk_column = await self._get_primary_key_column(empresa_id, table_name)
            
            if pk_column:
                response = client.table(table_name).upsert(data, on_conflict=pk_column).execute()
            else:
                response = client.table(table_name).insert(data).execute()

            if response.data:
                records_inserted = len(response.data)
                message = f"{records_inserted} registros inseridos/atualizados com sucesso em '{table_name}'."
                self.logger.log_info(message)
                return True, message, records_inserted
            else:
                error_message = response.error.message if response.error else 'desconhecido'
                message = f"Falha ao inserir dados em '{table_name}'. Erro: {error_message}"
                self.logger.log_error(message)
                return False, message, 0

        except Exception as e:
            try:
                error_str = str(e)
            except UnicodeDecodeError:
                error_str = repr(e)

            message = f"Erro inesperado durante o processo de upsert para a tabela '{table_name}': {error_str}"
            self.logger.log_error(message)
            return False, message, 0

    def _infer_schema_from_data(self, empresa_id: str, table_name: str, data: List[Dict[str, Any]]) -> TableSchema:
        """
        Infere o esquema da tabela a partir de uma lista de dicionários.
        """
        columns_definition = {}
        if not data:
            return TableSchema(name=table_name, columns=[], client_id=empresa_id)

        sample = data[0]
        # Tenta encontrar uma coluna 'id' para ser a chave primária
        has_id_column = 'id' in sample
        for key, value in sample.items():
            # Mapeamento de tipos de dados Python para PostgreSQL
            if isinstance(value, bool):
                pg_type = "boolean"
            elif isinstance(value, int):
                pg_type = "bigint"
            elif isinstance(value, float):
                pg_type = "real"
            elif isinstance(value, datetime):
                pg_type = "timestamp"
            else: # Default to TEXT for strings or other types
                pg_type = "text"
            
            # Define a chave primária
            if has_id_column:
                is_primary_key = (key.lower() == 'id')
            else:
                # Fallback para a primeira coluna se não houver 'id'
                is_primary_key = (len(columns_definition) == 0)
            
            columns_definition[key] = ColumnDefinition(name=key, type=pg_type, primary_key=is_primary_key)

        # Garante que a coluna 'id' seja a primeira, se existir
        if has_id_column and 'id' in columns_definition:
            id_column = columns_definition.pop('id')
            # Recria o dicionário com 'id' primeiro
            columns_definition = {'id': id_column, **columns_definition}

        return TableSchema(name=table_name, columns=list(columns_definition.values()), client_id=empresa_id)

    async def _get_table_schema_from_db(self, empresa_id: str, table_name: str) -> List[str]:
        """
        Busca os nomes das colunas de uma tabela existente no banco de dados.
        """
        query = f"""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = '{table_name}';
        """
        result = await self.execute_query(empresa_id, query)
        if result is not None:
            return [row['column_name'] for row in result]
        return []

    async def _get_primary_key_column(self, empresa_id: str, table_name: str) -> Optional[str]:
        """
        Detecta qual coluna é a PRIMARY KEY de uma tabela.
        """
        query = '''
        SELECT 
            kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        WHERE tc.table_schema = 'public' 
            AND tc.table_name = $1
            AND tc.constraint_type = 'PRIMARY KEY'
        LIMIT 1;
        '''
        
        try:
            result = await self.execute_query(empresa_id, query.replace('$1', f"'{table_name}'"))
            if result and len(result) > 0:
                pk_column = result[0]['column_name']
                self.logger.log_info(f"PRIMARY KEY detectada para tabela '{table_name}': '{pk_column}'")
                return pk_column
            else:
                self.logger.log_info(f"Nenhuma PRIMARY KEY encontrada para tabela '{table_name}'")
                return None
        except Exception as e:
            self.logger.log_error(f"Erro ao detectar PRIMARY KEY para tabela '{table_name}': {str(e)}")
            return None

    async def _compare_and_alter_table(self, empresa_id: str, table_name: str, inferred_schema: TableSchema):
        """
        Compara o esquema inferido com o esquema do banco e adiciona colunas ausentes.
        """
        existing_columns = await self._get_table_schema_from_db(empresa_id, table_name)
        
        added_columns = False
        for column in inferred_schema.columns:
            if column.name not in existing_columns:
                self.logger.log_info(f"Coluna '{column.name}' não encontrada na tabela '{table_name}'. Adicionando...")
                alter_sql = f'ALTER TABLE public."{table_name}" ADD COLUMN "{column.name}" {column.type};'
                await self.execute_query(empresa_id, alter_sql)
                added_columns = True

        if added_columns:
            self.logger.log_info(f"Colunas adicionadas à tabela '{table_name}'. Aguardando recarregamento do schema.")