# split_db.py

from config.db_connection import DatabaseConnection
import logging

logging.basicConfig(filename='scrapgov.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def replicar_palavras_chave():
    db_connection = DatabaseConnection()
    db_connection.connect()
    connection = db_connection.get_connection()
    cursor = connection.cursor()

    try:
        # Seleciona todas as notícias da tabela noticias, incluindo a coluna 'data'
        cursor.execute("SELECT id, obrigatorias, adicionais, data FROM noticias")
        noticias = cursor.fetchall()

        for noticia in noticias:
            noticia_id, obrigatorias_str, adicionais_str, data_noticia = noticia

            if obrigatorias_str:
                obrigatorias = obrigatorias_str.split(', ')
                for obrigatorio in obrigatorias:
                    cursor.execute("""
                        INSERT INTO palavras_chave (id_noticia, obrigatorias, data)
                        VALUES (%s, %s, %s)
                    """, (noticia_id, obrigatorio, data_noticia))

            if adicionais_str:
                adicionais = adicionais_str.split(', ')
                for adicional in adicionais:
                    cursor.execute("""
                        INSERT INTO palavras_chave (id_noticia, adicionais, data)
                        VALUES (%s, %s, %s)
                    """, (noticia_id, adicional, data_noticia))

        connection.commit()
        logging.info("Replicação de palavras-chave concluída com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao replicar palavras-chave: {e}")
        connection.rollback()
    finally:
        cursor.close()
        db_connection.close()

if __name__ == "__main__":
    replicar_palavras_chave()