"""
Modelos base da aplicação usando Pydantic e POO
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum

class ColumnType(str, Enum):
    """Enum para tipos de colunas suportados"""
    INTEGER = "integer"
    BIGINT = "bigint"
    VARCHAR = "varchar"
    TEXT = "text"
    BOOLEAN = "boolean"
    TIMESTAMP = "timestamp"
    DATE = "date"
    DECIMAL = "decimal"
    REAL = "real"  # Adicionado para suportar tipos de ponto flutuante
    JSON = "json"
    UUID = "uuid"

class BaseEntity(BaseModel):
    """Classe base para todas as entidades"""
    
    class Config:
        from_attributes = True
        use_enum_values = True
        validate_assignment = True
        
    def to_dict(self) -> Dict[str, Any]:
        """Converte o modelo para dicionário"""
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Cria instância a partir de dicionário"""
        return cls(**data)

class ColumnDefinition(BaseEntity):
    """Modelo para definição de colunas de tabela"""
    
    name: str = Field(..., description="Nome da coluna")
    type: ColumnType = Field(..., description="Tipo da coluna")
    nullable: bool = Field(default=True, description="Se a coluna aceita NULL")
    primary_key: bool = Field(default=False, description="Se é chave primária")
    unique: bool = Field(default=False, description="Se tem constraint UNIQUE")
    default_value: Optional[Union[str, int, bool]] = Field(default=None, description="Valor padrão")
    max_length: Optional[int] = Field(default=None, description="Tamanho máximo (para VARCHAR)")
    
    @validator('name')
    def validate_column_name(cls, v):
        """Valida o nome da coluna"""
        if not v or not v.strip():
            raise ValueError("Nome da coluna não pode estar vazio")
        # Remove espaços e caracteres especiais
        return v.strip().lower().replace(' ', '_')
    
    @validator('max_length')
    def validate_max_length(cls, v, values):
        """Valida o tamanho máximo para VARCHAR"""
        if values.get('type') == ColumnType.VARCHAR and v is None:
            return 255  # Valor padrão para VARCHAR
        return v

class TableSchema(BaseEntity):
    """Modelo para schema de tabela"""
    
    name: str = Field(..., description="Nome da tabela")
    columns: List[ColumnDefinition] = Field(..., description="Lista de colunas")
    client_id: str = Field(..., description="ID do cliente")
    created_at: datetime = Field(default_factory=datetime.now, description="Data de criação")
    
    @validator('name')
    def validate_table_name(cls, v):
        """Valida o nome da tabela"""
        if not v or not v.strip():
            raise ValueError("Nome da tabela não pode estar vazio")
        return v.strip().lower().replace(' ', '_')
    
    @validator('columns')
    def validate_columns(cls, v):
        """Valida as colunas da tabela"""
        if not v:
            raise ValueError("Tabela deve ter pelo menos uma coluna")
        
        # Verifica se há pelo menos uma chave primária
        primary_keys = [col for col in v if col.primary_key]
        if not primary_keys:
            # Adiciona uma coluna ID como chave primária se não houver
            id_column = ColumnDefinition(
                name="id",
                type=ColumnType.UUID,
                nullable=False,
                primary_key=True,
                default_value="gen_random_uuid()"
            )
            v.insert(0, id_column)
        
        return v
    
    def get_create_table_sql(self) -> str:
        """Gera SQL para criar a tabela"""
        columns_sql = []
        
        for col in self.columns:
            col_sql = f'"{col.name}" {col.type}'
            
            # Adiciona tamanho para VARCHAR
            if col.type == ColumnType.VARCHAR and col.max_length:
                col_sql += f"({col.max_length})"
            
            # Adiciona NOT NULL se necessário
            if not col.nullable:
                col_sql += " NOT NULL"
            
            # Adiciona valor padrão
            if col.default_value is not None:
                if col.default_value == "gen_random_uuid()":
                    col_sql += f" DEFAULT {col.default_value}"
                elif isinstance(col.default_value, str):
                    col_sql += f" DEFAULT '{col.default_value}'"
                else:
                    col_sql += f" DEFAULT {col.default_value}"
            
            # Adiciona UNIQUE se necessário
            if col.unique:
                col_sql += " UNIQUE"

            columns_sql.append(col_sql)

        # Adiciona PRIMARY KEY se necessário
        primary_keys = [col.name for col in self.columns if col.primary_key]
        if primary_keys:
            pk_columns = ", ".join(f'"{pk}"' for pk in primary_keys)
            columns_sql.append(f'PRIMARY KEY ({pk_columns})')
        
        return f'CREATE TABLE IF NOT EXISTS "{self.name}" (\n  {",\n  ".join(columns_sql)}\n);'

class ClientConfiguration(BaseEntity):
    """Modelo para configuração de cliente"""
    
    client_id: str = Field(..., description="ID único do cliente")
    client_name: str = Field(..., description="Nome do cliente")
    supabase_url: str = Field(..., description="URL do Supabase do cliente")
    supabase_key: str = Field(..., description="Chave do Supabase do cliente")
    active: bool = Field(default=True, description="Se o cliente está ativo")
    created_at: datetime = Field(default_factory=datetime.now, description="Data de criação")
    updated_at: Optional[datetime] = Field(default=None, description="Data de atualização")
    
    @validator('client_id')
    def validate_client_id(cls, v):
        """Valida o ID do cliente"""
        if not v or not v.strip():
            raise ValueError("ID do cliente não pode estar vazio")
        return v.strip()
    
    @validator('supabase_url')
    def validate_supabase_url(cls, v):
        """Valida a URL do Supabase"""
        if not v.startswith('https://'):
            raise ValueError("URL do Supabase deve começar com https://")
        return v

class DataRecord(BaseEntity):
    """Modelo para registro de dados recebidos"""
    
    table_name: str = Field(..., description="Nome da tabela de destino")
    client_id: str = Field(..., description="ID do cliente")
    data: Dict[str, Any] = Field(..., description="Dados a serem inseridos")
    operation: str = Field(default="INSERT", description="Tipo de operação (INSERT, UPDATE, DELETE)")
    received_at: datetime = Field(default_factory=datetime.now, description="Data de recebimento")
    
    @validator('operation')
    def validate_operation(cls, v):
        """Valida o tipo de operação"""
        allowed_operations = ["INSERT", "UPDATE", "DELETE"]
        if v.upper() not in allowed_operations:
            raise ValueError(f"Operação deve ser uma de: {allowed_operations}")
        return v.upper()

class WebhookPayload(BaseEntity):
    """Modelo para payload de webhook recebido"""
    
    event_type: str = Field(..., description="Tipo do evento")
    timestamp: datetime = Field(..., description="Timestamp do evento")
    data: Dict[str, Any] = Field(..., description="Dados do evento")
    source: str = Field(default="mysql_integrator", description="Origem do evento")
    
    def validate_payload(self) -> bool:
        """Valida se o payload está correto"""
        required_fields = ['event_type', 'timestamp', 'data']
        return all(hasattr(self, field) for field in required_fields)


class CompanyConfig(BaseEntity):
    """Modelo para configurações de empresa no banco principal"""
    
    empresa_id: str = Field(..., description="ID da empresa")
    chave: str = Field(..., description="Chave da configuração")
    valor: str = Field(..., description="Valor da configuração")
    descricao: str = Field(default="", description="Descrição da configuração")
    
    def validate_config(self) -> bool:
        """Valida se a configuração está correta"""
        if not self.empresa_id or not self.chave or not self.valor:
            return False
        return True
    
    def is_database_config(self) -> bool:
        """Verifica se é uma configuração de banco de dados"""
        return self.chave in ['DB_URL', 'DB_TOKEN']


class DataPayload(BaseEntity):
    """Modelo para payload de dados recebidos do integrador MySQL"""
    
    table_name: str = Field(..., description="Nome da tabela de destino")
    data: List[Dict[str, Any]] = Field(..., description="Lista de dados a serem inseridos")
    empresa_id: str = Field(default="", description="ID da empresa")
    operation: str = Field(default="insert", description="Tipo de operação")
    
    def validate_payload(self) -> bool:
        """Valida se o payload de dados está correto"""
        if not self.table_name or not isinstance(self.data, list):
            return False
        if not self.data:  # Lista vazia
            return False
        # Verifica se todos os itens da lista são dicionários
        return all(isinstance(item, dict) for item in self.data)
    
    def get_record_count(self) -> int:
        """Retorna o número de registros no payload"""
        return len(self.data) if self.data else 0
    
    def get_columns(self) -> List[str]:
        """Retorna as colunas presentes nos dados"""
        if not self.data:
            return []
        # Pega as chaves do primeiro registro como referência
        return list(self.data[0].keys()) if self.data[0] else []


class SchemaPayload(BaseEntity):
    """Modelo para payload de schema recebido via webhook"""
    
    schema: str = Field(..., description="Schema SQL")
    table_name: str = Field(default="", description="Nome da tabela")
    empresa_id: str = Field(default="", description="ID da empresa")
    schema_type: str = Field(default="mysql", description="Tipo do schema")
    
    def validate_schema(self) -> bool:
        """Valida se o schema está correto"""
        if not self.schema or not isinstance(self.schema, str):
            return False
        # Verifica se contém palavras-chave básicas de SQL
        schema_lower = self.schema.lower()
        return any(keyword in schema_lower for keyword in ['create table', 'alter table', 'drop table'])
    
    def extract_table_name(self) -> str:
        """Extrai o nome da tabela do schema SQL"""
        if self.table_name:
            return self.table_name
        
        # Tenta extrair do SQL
        import re
        schema_lower = self.schema.lower()
        
        # Padrão para CREATE TABLE
        create_match = re.search(r'create\s+table\s+(?:if\s+not\s+exists\s+)?`?(\w+)`?', schema_lower)
        if create_match:
            return create_match.group(1)
        
        # Padrão para ALTER TABLE
        alter_match = re.search(r'alter\s+table\s+`?(\w+)`?', schema_lower)
        if alter_match:
            return alter_match.group(1)
        
        return ""
    
    def save_to_file(self, directory: str) -> str:
        """Salva o schema em arquivo e retorna o caminho"""
        try:
            from pathlib import Path
            
            empresa_dir = Path(directory) / self.empresa_id
            empresa_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.extract_table_name() or 'unknown_table'}_{timestamp}.sql"
            file_path = empresa_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"-- Schema for {self.extract_table_name() or 'unknown_table'}\n")
                f.write(f"-- Company: {self.empresa_id}\n")
                f.write(f"-- Type: {self.schema_type}\n")
                f.write(f"-- Generated at: {datetime.now().isoformat()}\n")
                f.write("\n")
                f.write(self.schema)
                f.write("\n")
            
            return str(file_path)
        except Exception as e:
            raise ValueError(f"Failed to save schema to file: {str(e)}")


class TableColumn(BaseModel):
    """Model for table column definition"""
    name: str
    type: str
    nullable: bool = True
    is_primary_key: bool = False
    max_length: Optional[int] = None

class TableDefinition(BaseModel):
    """Model for table definition"""
    name: str
    columns: List[TableColumn]
    record_count: Optional[int] = None

class DatabaseSchema(BaseModel):
    """Model for database schema structure"""
    database_name: str
    tables: List[TableDefinition]

class MySQLIntegratorSchema(BaseEntity):
    """Model for MySQL Integrator schema format"""
    schema: DatabaseSchema
    timestamp: datetime
    source: str
    empresa_id: str
    
    def convert_to_sql(self) -> str:
        """Convert JSON schema to SQL CREATE TABLE statements"""
        try:
            database_name = self.schema.database_name
            tables = self.schema.tables
            
            sql_statements = []
            
            for table in tables:
                table_name = table.name
                if not table_name:
                    continue
                    
                columns = table.columns
                column_definitions = []
                
                for column in columns:
                    col_name = column.name
                    col_type = column.type
                    nullable = column.nullable
                    is_primary_key = column.is_primary_key
                    max_length = column.max_length
                    
                    # Mapear tipos MySQL para tipos comuns
                    if col_type.lower() == 'int':
                        sql_type = 'INTEGER'
                    elif col_type.lower() == 'varchar' and max_length:
                        sql_type = f'VARCHAR({max_length})'
                    elif col_type.lower() == 'text':
                        sql_type = 'TEXT'
                    elif col_type.lower() == 'datetime':
                        sql_type = 'TIMESTAMP'
                    elif col_type.lower() == 'decimal':
                        sql_type = 'DECIMAL(10,2)'
                    else:
                        sql_type = col_type.upper()
                    
                    col_def = f"{col_name} {sql_type}"
                    
                    if is_primary_key:
                        col_def += " PRIMARY KEY"
                    elif not nullable:
                        col_def += " NOT NULL"
                    elif nullable:
                        col_def += " NULL"
                    
                    column_definitions.append(col_def)
                
                if column_definitions:
                    create_table_sql = f"CREATE TABLE {table_name} (\n  "
                    create_table_sql += ",\n  ".join(column_definitions)
                    create_table_sql += "\n);"
                    sql_statements.append(create_table_sql)
            
            return "\n\n".join(sql_statements)
            
        except Exception as e:
            raise ValueError(f"Failed to convert JSON schema to SQL: {str(e)}")
    
    def save_to_file(self, directory: str, table_name: str) -> str:
        """Save converted schema to file"""
        try:
            from pathlib import Path
            
            empresa_dir = Path(directory) / self.empresa_id
            empresa_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{table_name}_{timestamp}.sql"
            file_path = empresa_dir / filename
            
            sql_content = self.convert_to_sql()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"-- Schema converted from MySQL Integrator\n")
                f.write(f"-- Database: {self.schema.database_name}\n")
                f.write(f"-- Company: {self.empresa_id}\n")
                f.write(f"-- Source: {self.source}\n")
                f.write(f"-- Timestamp: {self.timestamp.isoformat()}\n")
                f.write(f"-- Generated at: {datetime.now().isoformat()}\n")
                f.write("\n")
                f.write(sql_content)
                f.write("\n")
            
            return str(file_path)
        except Exception as e:
            raise ValueError(f"Failed to save schema to file: {str(e)}")


class IntegratorDataPayload(BaseEntity):
    """Modelo para payload de dados multi-tabelas do integrador MySQL"""
    timestamp: datetime = Field(..., description="Timestamp da coleta")
    data: Dict[str, List[Dict[str, Any]]] = Field(..., description="Mapa de tabelas para listas de registros")
    source: str = Field(default="mysql_integrator", description="Fonte dos dados")
    empresa_id: str = Field(default="", description="ID da empresa")
    
    def validate_payload(self) -> bool:
        """Valida se o payload multi-tabelas está correto"""
        if not isinstance(self.data, dict) or not self.data:
            return False
        for table_name, records in self.data.items():
            if not isinstance(table_name, str):
                return False
            if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
                return False
        return True
    
    def get_tables(self) -> List[str]:
        """Retorna a lista de nomes de tabelas presentes no payload"""
        return list(self.data.keys()) if self.data else []
    
    def get_total_records(self) -> int:
        """Retorna o total de registros em todas as tabelas"""
        return sum(len(records) for records in self.data.values()) if self.data else 0