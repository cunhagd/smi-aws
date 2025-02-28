import subprocess
import os

def lambda_handler(event, context):
    print("Iniciando scraping de portais nacionais...")
    
    # Caminho para o requirements.txt no pacote
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        print(f"Instalando dependências a partir de {requirements_path}...")
        try:
            # Usar o pip do runtime Lambda
            pip_path = os.path.join('/var/lang/bin', 'pip3')
            if not os.path.exists(pip_path):
                pip_path = os.path.join('/var/lang/bin', 'pip')  # Fallback para pip
            if not os.path.exists(pip_path):
                raise FileNotFoundError("pip não encontrado no ambiente Lambda")
            
            # Instalar dependências em /tmp/pkgs
            subprocess.check_call([pip_path, 'install', '-r', requirements_path, '--target', '/tmp/pkgs'], env={'PATH': '/tmp/pkgs/bin:' + os.environ['PATH']})
            # Atualizar PATH para incluir os binários instalados
            os.environ['PATH'] = '/tmp/pkgs/bin:' + os.environ['PATH']
            print("Dependências instaladas com sucesso.")
        except subprocess.CalledProcessError as e:
            print(f"Erro ao instalar dependências: {e}")
            return {
                "statusCode": 500,
                "body": f"Erro ao instalar dependências: {e}"
            }
    else:
        print("requirements.txt não encontrado. Instalação de dependências ignorada.")
    
    # Importar e executar o código principal
    import main_nacional
    main_nacional.main()
    
    return {
        "statusCode": 200,
        "body": "Scraping nacional concluído!"
    }