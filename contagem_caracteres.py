import os
import json
import psycopg2
from datetime import datetime
import logging

# Configuração de logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Exibe logs no terminal
        logging.FileHandler('contagem_caracteres_debug.log')  # Salva logs em arquivo
    ]
)

# Configurações do banco de dados
DB_CONFIG = {
    'dbname': 'railway',
    'user': 'postgres',
    'password': 'HomctJkRyZIGzYhrlmFRdKHZPJJmWylh',
    'host': 'metro.proxy.rlwy.net',
    'port': '30848'
}

# Função para conectar ao banco de dados
def connect_to_db():
    logging.debug("Iniciando conexão com o banco de dados...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        logging.debug("Conexão ao banco de dados estabelecida com sucesso")
        return conn
    except Exception as e:
        logging.error(f"Erro ao conectar ao banco de dados: {e}")
        raise

# Função para excluir notícia do banco
def delete_news_from_db(news_id, conn):
    logging.debug(f"Tentando excluir notícia com ID: {news_id}")
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM noticias WHERE id = %s", (news_id,))
        conn.commit()
        logging.info(f"Notícia com ID {news_id} excluída com sucesso")
        return True
    except Exception as e:
        logging.error(f"Erro ao excluir notícia com ID {news_id}: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()

# Função para contar caracteres e excluir notícias longas
def count_characters():
    logging.debug("Iniciando processo de contagem de caracteres...")

    # Conectar ao banco de dados
    conn = connect_to_db()
    cursor = conn.cursor()
    logging.debug("Cursor do banco de dados criado")

    try:
        # Obter a data atual
        current_date = datetime.now().date()  # Ex.: 2025-03-06
        logging.debug(f"Filtrando notícias para a data atual: {current_date}")

        # Consultar notícias do dia atual
        cursor.execute("SELECT id, corpo FROM noticias WHERE TO_DATE(data, 'DD/MM/YYYY') = %s", (current_date,))
        rows = cursor.fetchall()
        logging.debug(f"Consulta retornou {len(rows)} linhas da tabela 'noticias' para a data {current_date}")

        # Contar caracteres e excluir se >= 50.000
        deleted_count = 0
        for row in rows:
            news_id, corpo = row
            char_count = len(str(corpo) if corpo else "")
            logging.debug(f"Notícia ID {news_id} tem {char_count} caracteres")

            if char_count >= 50000:
                if delete_news_from_db(news_id, conn):
                    deleted_count += 1
                    logging.info(f"Notícia ID {news_id} excluída por exceder 50.000 caracteres")

        if deleted_count > 0:
            logging.info(f"Total de {deleted_count} notícias excluídas por exceder 50.000 caracteres.")
        else:
            logging.info("Nenhuma notícia com mais de 50.000 caracteres encontrada.")

    except Exception as e:
        logging.error(f"Erro no processo de contagem de caracteres: {e}")
        raise
    finally:
        logging.debug("Fechando cursor e conexão com o banco de dados...")
        cursor.close()
        conn.close()

if __name__ == "__main__":
    count_characters()