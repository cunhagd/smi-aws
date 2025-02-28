import psycopg2
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os
import logging

# Configuração de logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Exibe logs no terminal
        logging.FileHandler('espelho_debug.log')  # Salva logs em arquivo
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

# Configurações do Google Sheets
SHEET_ID = '19bUSdcegG6rE4Yml_diHb7tG80KmCfr7cNkyiesd_nU'
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS_FILE = 'credentials.json'  # Caminho para o arquivo de credenciais

# Função para conectar ao Google Sheets
def connect_to_sheets():
    logging.debug("Iniciando conexão com o Google Sheets...")
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        logging.debug(f"Credenciais carregadas de {CREDS_FILE}")
        client = gspread.authorize(creds)
        logging.debug("Autenticação bem-sucedida")
        sheet = client.open_by_key(SHEET_ID)
        logging.debug(f"Planilha aberta com ID: {SHEET_ID}")
        return sheet
    except FileNotFoundError as e:
        logging.error(f"Arquivo de credenciais não encontrado: {e}")
        raise
    except Exception as e:
        logging.error(f"Erro ao conectar ao Google Sheets: {e}")
        raise

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

# Função para obter o nome da aba baseado no mês atual
def get_month_sheet_name():
    logging.debug("Obtendo nome da aba baseado no mês atual...")
    month_names = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    current_month = datetime.now().month
    sheet_name = month_names[current_month]
    logging.debug(f"Mês atual identificado: {sheet_name}")
    return sheet_name

# Função para obter os cabeçalhos da tabela do banco
def get_table_headers(cursor):
    logging.debug("Obtendo cabeçalhos da tabela 'noticias'...")
    cursor.execute("SELECT * FROM noticias LIMIT 0")  # Executa uma consulta vazia para pegar a estrutura
    colnames = [desc[0] for desc in cursor.description]
    logging.debug(f"Cabeçalhos encontrados: {colnames}")
    return colnames

# Função para espelhar os dados
def mirror_data():
    logging.debug("Iniciando processo de espelhamento de dados...")

    # Conectar ao banco de dados
    conn = connect_to_db()
    cursor = conn.cursor()
    logging.debug("Cursor do banco de dados criado")

    try:
        # Obter os cabeçalhos da tabela noticias
        headers = get_table_headers(cursor)
        logging.debug(f"Cabeçalhos da tabela: {headers}")

        # Buscar todos os dados da tabela noticias
        logging.debug("Executando consulta SQL para buscar dados da tabela 'noticias'...")
        cursor.execute("SELECT * FROM noticias")
        rows = cursor.fetchall()
        logging.debug(f"Consulta retornou {len(rows)} linhas da tabela 'noticias'")

        # Conectar ao Google Sheets
        sheet = connect_to_sheets()
        month_sheet_name = get_month_sheet_name()
        logging.debug(f"Selecionando ou criando aba: {month_sheet_name}")

        # Verificar ou criar a aba do mês atual
        try:
            worksheet = sheet.worksheet(month_sheet_name)
            logging.debug(f"Aba {month_sheet_name} encontrada")
        except gspread.WorksheetNotFound:
            logging.debug(f"Aba {month_sheet_name} não encontrada, criando nova aba...")
            worksheet = sheet.add_worksheet(title=month_sheet_name, rows="1000", cols=len(headers))
            logging.debug(f"Aba {month_sheet_name} criada")
            # Adicionar cabeçalhos da tabela
            worksheet.append_row(headers)
            logging.debug("Cabeçalhos adicionados à nova aba")

        # Obter dados existentes na aba para evitar duplicatas (baseado em id)
        logging.debug("Obtendo IDs existentes na aba para evitar duplicatas...")
        existing_ids = [int(row[0]) for row in worksheet.get_all_values()[1:]]  # Ignora o cabeçalho
        logging.debug(f"IDs existentes na aba: {existing_ids}")

        # Preparar novos dados para inserção
        logging.debug("Filtrando novos dados para inserção...")
        new_data = []
        for row in rows:
            row_id = row[0]
            if row_id not in existing_ids:
                new_data.append([str(cell) if cell is not None else '' for cell in row])  # Converter para string
                logging.debug(f"Novo ID encontrado para inserção: {row_id}")
        logging.debug(f"Total de novos dados a serem inseridos: {len(new_data)}")

        # Inserir novos dados na aba
        if new_data:
            logging.debug("Inserindo novos dados na aba...")
            worksheet.append_rows(new_data)
            logging.info(f"{len(new_data)} novas notícias espelhadas na aba {month_sheet_name}.")
        else:
            logging.info("Nenhum novo dados para espelhar.")

    except Exception as e:
        logging.error(f"Erro ao espelhar dados: {e}")
        raise
    finally:
        logging.debug("Fechando cursor e conexão com o banco de dados...")
        cursor.close()
        conn.close()

if __name__ == "__main__":
    mirror_data()