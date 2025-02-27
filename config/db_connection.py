import psycopg2
import logging

# Configuração da string de conexão com o banco de dados PostgreSQL
DB_HOST = "metro.proxy.rlwy.net"
DB_PORT = 30848
DB_NAME = "railway"
DB_USER = "postgres"
DB_PASSWORD = "HomctJkRyZIGzYhrlmFRdKHZPJJmWylh"

class DatabaseConnection:
    def __init__(self):
        self.connection = None

    def connect(self):
        """Conecta ao banco de dados PostgreSQL."""
        try:
            self.connection = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            logging.info("Conexão com o banco de dados estabelecida com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao conectar ao banco de dados: {e}")
            raise

    def close(self):
        """Fecha a conexão com o banco de dados."""
        if self.connection:
            self.connection.close()
            logging.info("Conexão com o banco de dados fechada com sucesso.")

    def get_connection(self):
        """Retorna a conexão atual."""
        return self.connection