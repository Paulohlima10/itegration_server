# Receptor de Dados MySQL → Supabase

Serviço web FastAPI que recebe dados do integrador MySQL e os replica automaticamente no Supabase de cada cliente.

## 🎯 Objetivo

Este serviço funciona como um receptor central que:
1. Recebe dados do integrador MySQL
2. Cria automaticamente a estrutura de tabelas no Supabase do cliente
3. Grava os dados recebidos no banco do cliente
4. Recebe schemas via webhook e os salva em arquivos

## 🏗️ Arquitetura

- **API FastAPI**: Receptor principal de dados
- **Supabase Principal**: Configurações das empresas
- **Múltiplos Supabase**: Um banco por cliente
- **Sistema de arquivos**: Armazenamento de schemas

## 📁 Estrutura do Projeto

```
receptor_dados/
├── main.py                    # FastAPI app principal
├── config/                    # Configurações
│   ├── __init__.py
│   └── settings.py
├── models/                    # Modelos de dados
│   └── __init__.py
├── services/                  # Lógica de negócio
│   ├── __init__.py
│   └── logging_service.py
├── api/                       # Endpoints
│   ├── __init__.py
│   └── routes.py
├── schemas/                   # Arquivos de schema
├── logs/                      # Logs da aplicação
├── requirements.txt
├── .env.example
└── README.md
```

## 🚀 Instalação

1. Clone o repositório
2. Copie `.env.example` para `.env` e configure as variáveis
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Execute a aplicação:
   ```bash
   python main.py
   ```

## 📝 Configuração

Configure as seguintes variáveis no arquivo `.env`:

- `SUPABASE_MAIN_URL`: URL do Supabase principal
- `SUPABASE_MAIN_KEY`: Chave do Supabase principal
- `SECRET_KEY`: Chave secreta para JWT
- Outras configurações conforme `.env.example`

## 🔗 Endpoints

- `GET /`: Status geral do serviço
- `GET /health`: Verificação de saúde
- `GET /api/v1/status`: Status da API
- `POST /api/v1/receive-data`: Receber dados (em desenvolvimento)
- `POST /api/v1/receive-schema`: Receber schemas (em desenvolvimento)

## 🛠️ Desenvolvimento

O projeto utiliza programação orientada a objetos (POO) e segue as melhores práticas:

- Classes para configurações (`Settings`)
- Serviços especializados (`LoggingService`)
- Estrutura modular e escalável
- Sistema de logs robusto
- Tratamento de erros adequado

## 📊 Logs

Os logs são salvos em `logs/app.log` com rotação automática. Tipos de log:
- Requisições HTTP
- Operações de banco de dados
- Erros e exceções
- Status geral da aplicação