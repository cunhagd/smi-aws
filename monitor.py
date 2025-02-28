import os
import psycopg2
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging

# Configuração de logs
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Exibe logs no terminal
        logging.FileHandler('monitor_debug.log')  # Salva logs em arquivo
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

# Configurações de e-mail
SENDER_EMAIL = "devssecom@gmail.com"
SENDER_PASSWORD = "qzzo ymcg kkwn sztb"  # Use uma senha de app
RECIPIENTS = ["devssecom@gmail.com", "gustavo.cunha@governo.mg.gov.br", "isabela.bento@governo.mg.gov.br",
              "monitoramentogovernodeminas@gmail.com", "camilakifer@gmail.com", "alinegbh@gmail.com",
              "gustavo.medeiros@governo.mg.gov.br"]  # Lista de destinatários
ERROR_RECIPIENT = ["gustavo.cunha@governo.mg.gov.br", "isabela.bento@governo.mg.gov.br"]  # E-mail para erros

# Configurações do Google Sheets
SHEET_ID = '1oU-1qLnJxctsEAd0oSN6UMCue6dTx14J0ULhvMopfLE'
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS_FILE = os.path.join(os.path.dirname(__file__), 'credentials.json')  # Caminho relativo na raiz

def get_max_id_from_db():
    """Conecta ao banco e retorna o maior ID da tabela 'noticias'."""
    logging.debug("Iniciando conexão ao banco para buscar o maior ID...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(id) FROM noticias")
        max_id = cursor.fetchone()[0] or 0  # Retorna 0 se NULL
        cursor.close()
        conn.close()
        logging.debug(f"Maior ID no banco: {max_id}")
        return max_id
    except Exception as e:
        logging.error(f"Erro ao acessar o banco: {e}")
        raise

def get_last_id_from_sheets():
    """Lê o último ID salvo na célula A1 da planilha Google Sheets."""
    logging.debug(f"Iniciando conexão com a planilha de ID {SHEET_ID}...")
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID)
        worksheet = sheet.get_worksheet(0)  # Assume a primeira aba
        logging.debug("Aba da planilha selecionada")

        # Ler o valor da célula A1 (linha 1, coluna 1)
        last_id = worksheet.acell('A1').value
        last_id = int(last_id.strip()) if last_id and last_id.strip().isdigit() else 0
        logging.debug(f"Último ID encontrado na célula A1: {last_id}")
        return last_id
    except FileNotFoundError as e:
        logging.error(f"Arquivo de credenciais não encontrado: {e}")
        raise
    except Exception as e:
        logging.error(f"Erro ao buscar ID na planilha: {e}")
        raise

def save_id_to_sheets(id_value):
    """Salva o novo ID na célula A1 da planilha Google Sheets."""
    logging.debug(f"Salvando novo ID {id_value} na planilha...")
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID)
        worksheet = sheet.get_worksheet(0)
        worksheet.update_acell('A1', str(id_value))  # Atualiza a célula A1 com o novo ID
        logging.debug(f"Novo ID {id_value} salvo na célula A1 da planilha")
    except Exception as e:
        logging.error(f"Erro ao salvar ID na planilha: {e}")
        raise

def send_email(subject, body, recipients):
    """Envia e-mail usando SMTP do Gmail."""
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

def monitor_system():
    """Função principal para monitoramento."""
    try:
        # Passo 3: Ler o maior ID no banco
        max_id_db = get_max_id_from_db()
        print(f"Maior ID no banco: {max_id_db}")

        # Passo 4: Ler o último ID salvo na planilha
        last_id_file = get_last_id_from_sheets()
        print(f"Último ID na planilha: {last_id_file}")

        # Passo 5: Calcular a diferença
        difference = max_id_db - last_id_file
        print(f"Diferença entre IDs: {difference}")

        # Depuração: Confirmar os valores antes de enviar o e-mail
        print(f"Verificando corpo do e-mail: Usando diferença = {difference}")

        # Passo 6: Enviar e-mail baseado na diferença
        if difference <= 0:
            subject = "Alerta: Sistema de Monitoramento de Imprensa - SECOM"
            body = "O Sistema de Monitoramento de Imprensa - SECOM não salvou nenhuma notícia na última hora."
            send_email(subject, body, RECIPIENTS)
        else:
            subject = "Relatório: Sistema de Monitoramento de Imprensa - SECOM"
            body = f"O Sistema de Monitoramento de Imprensa - SECOM captou {difference} notícias na última hora."
            send_email(subject, body, RECIPIENTS)

        # Salvar o novo ID na planilha para a próxima rodagem
        save_id_to_sheets(max_id_db)
        print(f"Novo ID ({max_id_db}) salvo na planilha para a próxima execução.")

    except Exception as e:
        subject = "Erro no Sistema de Monitoramento de Imprensa - SECOM"
        body = f"Ocorreu um erro ao processar o monitoramento: {str(e)}"
        send_email(subject, body, ERROR_RECIPIENT)

if __name__ == "__main__":
    monitor_system()