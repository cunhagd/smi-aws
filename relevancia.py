import psycopg2
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
from email.mime.text import MIMEText
import logging

# Configuração de logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Exibe logs no terminal
        logging.FileHandler('relevancia_debug.log')  # Salva logs em arquivo
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
MAIN_SHEET_ID = '19bUSdcegG6rE4Yml_diHb7tG80KmCfr7cNkyiesd_nU'  # Planilha principal
IRRELEVANT_SHEET_ID = '1f9WXqgddohATXJ9cTOb1n2ozR6UREQC95DyCYFYHelg'  # Planilha de irrelevantes
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS_MAIN_FILE = 'credentials.json'  # Credenciais para a planilha principal
CREDS_IRRELEVANT_FILE = 'credentials.json'  # Credenciais para a planilha de irrelevantes

# Configurações de e-mail
SENDER_EMAIL = "devssecom@gmail.com"
SENDER_PASSWORD = "qzzo ymcg kkwn sztb"  # Use uma senha de app
RECIPIENTS_EMAIL = ["gustavo.cunha@governo.mg.gov.br", "isabela.bento@governo.mg.gov.br"]

# Função para conectar ao Google Sheets
def connect_to_sheets(sheet_id, creds_file):
    logging.debug(f"Iniciando conexão com o Google Sheets (ID: {sheet_id})...")
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, SCOPE)
        logging.debug(f"Credenciais carregadas de {creds_file}")
        client = gspread.authorize(creds)
        logging.debug("Autenticação bem-sucedida")
        sheet = client.open_by_key(sheet_id)
        logging.debug(f"Planilha aberta com ID: {sheet_id}")
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

# Função para salvar notícias excluídas na planilha de irrelevantes
def save_irrelevant_news(news_data, worksheet):
    logging.debug("Salvando notícias excluídas na planilha de irrelevantes...")
    try:
        worksheet.append_row(news_data)
        logging.info(f"Notícia excluída adicionada à planilha: {news_data[0]}")
    except Exception as e:
        logging.error(f"Erro ao salvar na planilha de irrelevantes: {e}")
        raise

# Função para enviar e-mail
def send_email(subject, body, recipients):
    logging.debug(f"Preparando envio de e-mail para {', '.join(recipients)}")
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = ", ".join(recipients)

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipients, msg.as_string())
        logging.info(f"E-mail enviado para {', '.join(recipients)} com sucesso")
    except Exception as e:
        logging.error(f"Erro ao enviar e-mail: {e}")
        raise

# Função principal para verificar relevância e excluir notícias
def check_relevance():
    logging.debug("Iniciando processo de verificação de relevância...")

    # Conectar ao banco de dados
    conn = connect_to_db()

    try:
        # Conectar à planilha principal
        main_sheet = connect_to_sheets(MAIN_SHEET_ID, CREDS_MAIN_FILE)
        logging.debug("Conexão com a planilha principal estabelecida")

        # Conectar à planilha de irrelevantes
        irrelevant_sheet = connect_to_sheets(IRRELEVANT_SHEET_ID, CREDS_IRRELEVANT_FILE)
        logging.debug("Conexão com a planilha de irrelevantes estabelecida")

        # Obter a aba ativa (assumindo que é a primeira aba)
        worksheet = main_sheet.get_worksheet(0)  # Ajuste se a coluna RELEVANCIA estiver em outra aba
        logging.debug("Aba principal selecionada")

        # Obter todos os dados da planilha
        all_values = worksheet.get_all_values()
        logging.debug(f"Dados da planilha carregados: {len(all_values)} linhas")

        # Identificar a coluna RELEVANCIA (coluna M, índice 12 assumindo que a contagem começa em 0)
        headers = all_values[0]
        relevancia_index = headers.index('RELEVANCIA') if 'RELEVANCIA' in headers else -1
        id_index = headers.index('ID') if 'ID' in headers else -1

        if relevancia_index == -1 or id_index == -1:
            logging.error("Colunas 'RELEVANCIA' ou 'ID' não encontradas na planilha")
            raise ValueError("Colunas 'RELEVANCIA' ou 'ID' não encontradas")

        logging.debug(f"Índice da coluna RELEVANCIA: {relevancia_index}")
        logging.debug(f"Índice da coluna ID: {id_index}")

        # Listas para rastrear notícias excluídas
        excluded_news = []

        # Verificar cada linha (ignorando o cabeçalho)
        for row in all_values[1:]:
            if len(row) > relevancia_index and row[relevancia_index].strip().lower() == 'irrelevante':
                news_id = int(row[id_index]) if row[id_index] else None
                if news_id:
                    logging.debug(f"Notícia identificada como irrelevante com ID: {news_id}")
                    # Buscar dados completos da notícia no banco
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM noticias WHERE id = %s", (news_id,))
                    news_data = cursor.fetchone()
                    cursor.close()

                    if news_data:
                        logging.debug(f"Dados da notícia com ID {news_id} encontrados no banco")
                        if delete_news_from_db(news_id, conn):
                            excluded_news.append([str(cell) if cell is not None else '' for cell in news_data])
                    else:
                        logging.warning(f"Notícia com ID {news_id} não encontrada no banco")

        # Salvar notícias excluídas na planilha de irrelevantes
        if excluded_news:
            irrelevant_worksheet = irrelevant_sheet.get_worksheet(0)  # Usar a primeira aba
            for news in excluded_news:
                save_irrelevant_news(news, irrelevant_worksheet)

            # Enviar e-mail
            subject = "Notícias Excluídas por Irrelevância - SECOM"
            body = f"Algumas notícias foram excluídas por irrelevância. Detalhes salvos na planilha: https://docs.google.com/spreadsheets/d/{IRRELEVANT_SHEET_ID}/edit?gid=0"
            send_email(subject, body, RECIPIENTS_EMAIL)
        else:
            logging.info("Nenhuma notícia irrelevante encontrada para exclusão")

    except Exception as e:
        logging.error(f"Erro no processo de verificação de relevância: {e}")
        raise
    finally:
        logging.debug("Fechando conexão com o banco de dados...")
        conn.close()

if __name__ == "__main__":
    check_relevance()