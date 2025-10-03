"""
Script para iniciar a aplicação em modo desenvolvimento
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_environment():
    """
    Configura o ambiente de desenvolvimento
    """
    print("🔧 CONFIGURANDO AMBIENTE DE DESENVOLVIMENTO")
    print("=" * 50)
    
    # Verifica se o arquivo .env existe
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  Arquivo .env não encontrado!")
        print("Criando arquivo .env de exemplo...")
        
        env_content = """# Configurações do Supabase
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here

# Configurações da aplicação
APP_ENV=development
LOG_LEVEL=INFO
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Configurações de segurança
SECRET_KEY=your_secret_key_here
"""
        
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(env_content)
        
        print("✅ Arquivo .env criado!")
        print("⚠️  IMPORTANTE: Configure as variáveis no arquivo .env antes de continuar!")
        return False
    
    # Verifica se o diretório de logs existe
    logs_dir = Path("logs")
    if not logs_dir.exists():
        logs_dir.mkdir(exist_ok=True)
        print("✅ Diretório de logs criado!")
    
    # Verifica se o diretório de testes existe
    tests_dir = Path("tests")
    if not tests_dir.exists():
        tests_dir.mkdir(exist_ok=True)
        print("✅ Diretório de testes criado!")
    
    return True

def install_dependencies():
    """
    Instala as dependências do projeto
    """
    print("\n📦 INSTALANDO DEPENDÊNCIAS")
    print("=" * 50)
    
    try:
        # Verifica se o pip está disponível
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True)
        
        # Instala as dependências
        print("Instalando dependências do requirements.txt...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dependências instaladas com sucesso!")
            return True
        else:
            print(f"❌ Erro ao instalar dependências: {result.stderr}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao verificar pip: {e}")
        return False
    except FileNotFoundError:
        print("❌ Python/pip não encontrado no PATH")
        return False

def start_development_server():
    """
    Inicia o servidor de desenvolvimento
    """
    print("\n🚀 INICIANDO SERVIDOR DE DESENVOLVIMENTO")
    print("=" * 50)
    print("Comando: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    print("URL: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    print("Health: http://localhost:8000/health")
    print("\nPressione Ctrl+C para parar o servidor")
    print("=" * 50)
    
    try:
        # Inicia o servidor uvicorn
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n\n🛑 Servidor parado pelo usuário")
    except FileNotFoundError:
        print("❌ uvicorn não encontrado. Instale com: pip install uvicorn")
        return False
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")
        return False
    
    return True

def main():
    """
    Função principal
    """
    print("🚀 INICIADOR DE DESENVOLVIMENTO")
    print("Projeto: API de Recepção de Dados")
    print("=" * 50)
    
    # Configura o ambiente
    if not setup_environment():
        print("\n❌ Configure o arquivo .env e execute novamente!")
        return 1
    
    # Pergunta se deve instalar dependências
    install_deps = input("\n📦 Instalar/atualizar dependências? (s/N): ").lower().strip()
    if install_deps in ['s', 'sim', 'y', 'yes']:
        if not install_dependencies():
            print("❌ Falha ao instalar dependências!")
            return 1
    
    # Inicia o servidor
    print("\n🚀 Iniciando servidor...")
    if not start_development_server():
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())