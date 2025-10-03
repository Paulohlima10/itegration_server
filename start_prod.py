"""
Script para iniciar a aplicação em modo produção
"""

import os
import sys
import subprocess
import signal
from pathlib import Path

def setup_production_environment():
    """
    Configura o ambiente de produção
    """
    print("🏭 CONFIGURANDO AMBIENTE DE PRODUÇÃO")
    print("=" * 50)
    
    # Verifica se o arquivo .env existe
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ Arquivo .env não encontrado!")
        print("O arquivo .env é obrigatório para produção!")
        return False
    
    # Verifica variáveis críticas
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_KEY", 
        "SECRET_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Variáveis obrigatórias não configuradas: {', '.join(missing_vars)}")
        return False
    
    # Configura variáveis de produção
    os.environ["APP_ENV"] = "production"
    os.environ["LOG_LEVEL"] = "WARNING"
    
    # Verifica diretórios necessários
    for directory in ["logs", "data", "backups"]:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True)
            print(f"✅ Diretório {directory} criado!")
    
    print("✅ Ambiente de produção configurado!")
    return True

def check_dependencies():
    """
    Verifica se todas as dependências estão instaladas
    """
    print("\n📦 VERIFICANDO DEPENDÊNCIAS")
    print("=" * 50)
    
    try:
        # Lista de pacotes críticos
        critical_packages = [
            "fastapi",
            "uvicorn", 
            "supabase",
            "sqlalchemy",
            "pydantic"
        ]
        
        for package in critical_packages:
            try:
                __import__(package)
                print(f"✅ {package}")
            except ImportError:
                print(f"❌ {package} - NÃO INSTALADO")
                return False
        
        print("✅ Todas as dependências estão instaladas!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar dependências: {e}")
        return False

def run_health_check():
    """
    Executa verificação de saúde antes de iniciar
    """
    print("\n🏥 VERIFICAÇÃO DE SAÚDE")
    print("=" * 50)
    
    try:
        # Importa e testa componentes críticos
        from services.supabase_service import SupabaseService
        from services.config_service import ConfigService
        from services.logging_service import LoggingService
        
        # Testa configuração
        config = ConfigService()
        if not config.get_supabase_config("default"):
            print("❌ Configuração do Supabase inválida")
            return False
        
        print("✅ Configuração válida")
        
        # Testa logging
        logger = LoggingService()
        logger.log_info("Health check - sistema iniciando")
        print("✅ Sistema de logs funcionando")
        
        print("✅ Verificação de saúde concluída!")
        return True
        
    except Exception as e:
        print(f"❌ Falha na verificação de saúde: {e}")
        return False

def start_production_server():
    """
    Inicia o servidor de produção
    """
    print("\n🚀 INICIANDO SERVIDOR DE PRODUÇÃO")
    print("=" * 50)
    print("Comando: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4")
    print("URL: http://localhost:8000")
    print("Modo: Produção (sem reload)")
    print("Workers: 4")
    print("\nPressione Ctrl+C para parar o servidor")
    print("=" * 50)
    
    try:
        # Inicia o servidor uvicorn em modo produção
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--host", "0.0.0.0",
            "--port", "8000", 
            "--workers", "4",
            "--access-log",
            "--log-level", "warning"
        ])
        
        # Aguarda o processo
        process.wait()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Parando servidor...")
        try:
            process.terminate()
            process.wait(timeout=10)
        except:
            process.kill()
        print("✅ Servidor parado!")
        
    except FileNotFoundError:
        print("❌ uvicorn não encontrado. Instale com: pip install uvicorn")
        return False
        
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")
        return False
    
    return True

def create_systemd_service():
    """
    Cria arquivo de serviço systemd (Linux)
    """
    if os.name != 'posix':
        return
    
    service_content = f"""[Unit]
Description=API de Recepção de Dados
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory={Path.cwd()}
Environment=PATH={Path.cwd()}/venv/bin
ExecStart={sys.executable} -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    service_file = Path("receptor-api.service")
    with open(service_file, "w") as f:
        f.write(service_content)
    
    print(f"✅ Arquivo de serviço criado: {service_file}")
    print("Para instalar: sudo cp receptor-api.service /etc/systemd/system/")
    print("Para habilitar: sudo systemctl enable receptor-api")
    print("Para iniciar: sudo systemctl start receptor-api")

def main():
    """
    Função principal
    """
    print("🏭 INICIADOR DE PRODUÇÃO")
    print("Projeto: API de Recepção de Dados")
    print("=" * 50)
    
    # Configura ambiente de produção
    if not setup_production_environment():
        print("\n❌ Falha na configuração do ambiente!")
        return 1
    
    # Verifica dependências
    if not check_dependencies():
        print("\n❌ Dependências não atendidas!")
        print("Execute: pip install -r requirements.txt")
        return 1
    
    # Executa verificação de saúde
    if not run_health_check():
        print("\n❌ Falha na verificação de saúde!")
        return 1
    
    # Pergunta sobre criação do serviço systemd
    if os.name == 'posix':
        create_service = input("\n🔧 Criar arquivo de serviço systemd? (s/N): ").lower().strip()
        if create_service in ['s', 'sim', 'y', 'yes']:
            create_systemd_service()
    
    # Inicia o servidor
    print("\n🚀 Iniciando servidor de produção...")
    if not start_production_server():
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())