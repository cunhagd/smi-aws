import logging
import relevancia
import espelho

# Configuração de logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Exibe logs no terminal
        logging.FileHandler('main_debug.log')  # Salva logs em arquivo
    ]
)

def main():
    logging.debug("Iniciando execução principal...")
    
    # Passo 1: Executar o módulo relevancia
    logging.info("Executando módulo de verificação de relevância...")
    try:
        relevancia.check_relevance()
        logging.info("Módulo de relevância concluído com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao executar módulo de relevância: {e}")
        raise
    
    # Passo 2: Executar o módulo espelho
    logging.info("Executando módulo de espelhamento de dados...")
    try:
        espelho.mirror_data()
        logging.info("Módulo de espelhamento concluído com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao executar módulo de espelhamento: {e}")
        raise
    
    logging.debug("Execução principal finalizada.")

if __name__ == "__main__":
    main()