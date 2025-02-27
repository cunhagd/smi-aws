import requests
from config.portais import portais
import re
from datetime import datetime
import logging
from config.db_connection import DatabaseConnection
from datetime import datetime

# Configuração de logs
logging.basicConfig(filename='scrapgov.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AcessarCodigoFonte:
    def __init__(self, url, usar_headers=False):
        self.url = url
        self.usar_headers = usar_headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }

    def acessar(self):
        """Acessa o código-fonte da URL com ou sem cabeçalhos."""
        try:
            if self.usar_headers:
                response = requests.get(self.url, headers=self.headers)
            else:
                response = requests.get(self.url)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"Erro HTTP ao acessar {self.url}: {http_err}")
            return None
        except Exception as err:
            logging.error(f"Erro inesperado ao acessar {self.url}: {err}")
            return None

    def set_headers(self, headers):
        """Permite configurar ou atualizar os cabeçalhos da requisição."""
        self.headers.update(headers)
        self.usar_headers = True

    def acessar_com_novos_headers(self, headers):
        """Acessa a URL com novos cabeçalhos temporários."""
        try:
            response = requests.get(self.url, headers=headers)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"Erro HTTP ao acessar {self.url}: {http_err}")
            return None
        except Exception as err:
            logging.error(f"Erro inesperado ao acessar {self.url}: {err}")
            return None

class ProcessadorTextoNoticias:
    def __init__(self, portal_chave):
        self.portal_chave = portal_chave

    def formatar_corpo(self, paragrafos):
        """Formata o corpo do texto para que cada parágrafo fique em uma linha separada."""
        corpo_formatado = ""
        for paragrafo in paragrafos:
            paragrafo_formatado = ' '.join(paragrafo.split())
            if paragrafo_formatado.strip():
                if corpo_formatado:
                    corpo_formatado += "\n\n"
                corpo_formatado += paragrafo_formatado
        return corpo_formatado.strip()

    def buscar_pontos(self):
        """Busca a pontuação associada ao portal atual."""
        return portais.get(self.portal_chave, {}).get('pontos', 'Pontuação não encontrada.')

    def buscar_abrangencia(self):
        """Busca a abrangência associada ao portal atual."""
        return portais.get(self.portal_chave, {}).get('abrangencia', 'Abrangência não encontrada.')

class GerenciadorNoticias:
    def __init__(self, pontuacao, abrangencia, nome_portal):
        self.pontuacao = pontuacao
        self.abrangencia = abrangencia
        self.nome_portal = nome_portal
        self.db_connection = DatabaseConnection()
        self.db_connection.connect()

    def _link_ja_existe(self, link):
        """Verifica se o link já existe no banco de dados."""
        connection = self.db_connection.get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM noticias WHERE link = %s", (link,))
            count = cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            logging.error(f"Erro ao verificar link duplicado: {e}")
            return False
        finally:
            cursor.close()

    def salvar_noticias(self, noticias):
        """Salva as notícias no banco de dados, evitando links duplicados."""
        connection = self.db_connection.get_connection()
        cursor = connection.cursor()
        try:
            for noticia, palavras_obrigatorias_encontradas, palavras_adicionais_encontradas in noticias:
                titulo, autor, data, corpo, link_canonical = noticia

                # Verifica se o link já existe
                if self._link_ja_existe(link_canonical):
                    print(f"Link duplicado ignorado: {link_canonical}")
                    continue

                palavras_chave_obrigatorias = ', '.join(palavras_obrigatorias_encontradas)
                palavras_chave_adicionais = ', '.join(palavras_adicionais_encontradas)

                # Insere a notícia na tabela
                cursor.execute("""
                    INSERT INTO noticias (data, titulo, corpo, link, autor, abrangencia, pontos, obrigatorias, adicionais)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    data, titulo, corpo, link_canonical, autor, self.abrangencia,
                    self.pontuacao, palavras_chave_obrigatorias, palavras_chave_adicionais
                ))

                logging.info(f"Notícia adicionada: {titulo}")

            # Commit das alterações
            connection.commit()
            logging.info("Notícias salvas com sucesso no banco de dados.")
        except Exception as e:
            logging.error(f"Erro ao salvar notícias no banco de dados: {e}")
            connection.rollback()
        finally:
            cursor.close()

    def fechar(self):
        """Fecha a conexão com o banco de dados."""
        self.db_connection.close()

class VerificarPalavrasChave:
    def __init__(self, palavras_obrigatorias, palavras_adicionais):
        self.palavras_obrigatorias = palavras_obrigatorias
        self.palavras_adicionais = palavras_adicionais

    @staticmethod
    def palavra_isolada_regex(palavra):
        return r'\b' + re.escape(palavra) + r'\b'

    def verificar(self, texto_noticia):
        palavras_obrigatorias_encontradas = [
            palavra for palavra in self.palavras_obrigatorias
            if self.verificar_palavra(palavra, texto_noticia)
        ]

        palavras_adicionais_encontradas = [
            palavra for palavra in self.palavras_adicionais
            if self.verificar_palavra(palavra, texto_noticia)
        ]

        contem_palavra_obrigatoria = bool(palavras_obrigatorias_encontradas)
        contem_palavra_adicional = bool(palavras_adicionais_encontradas)

        return contem_palavra_obrigatoria and contem_palavra_adicional, palavras_obrigatorias_encontradas, palavras_adicionais_encontradas

    def verificar_palavra(self, palavra, texto_noticia):
        if palavra.isupper():  # Para siglas
            return re.search(self.palavra_isolada_regex(palavra), texto_noticia)
        else:
            return re.search(self.palavra_isolada_regex(palavra.lower()), texto_noticia.lower())

class VerificarDataAtual:
    @staticmethod
    def verificar_data_atual(data_texto):
        """Verifica se a data fornecida corresponde à data atual."""
        data_atual = datetime.now().strftime("%d/%m/%Y")
        return data_texto == data_atual
