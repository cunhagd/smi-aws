import requests
from config import api_conexao, api_formatar


def acessar_codigo_fonte(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def formatar_corpo(paragrafos):
    return "\n\n".join(paragrafos)

def verificar_palavras_chave(texto, palavras_chave):
    texto = texto.lower()
    palavras_encontradas = {palavra for palavra in palavras_chave if palavra in texto}
    return palavras_encontradas

def verificar_link_existe(sheet, link):
    """ Verifica se o link já existe na coluna 'Link' da planilha """
    celulas = sheet.col_values(7)  # 7 corresponde à coluna G
    return link in celulas

def salvar_noticias(noticias, credenciais_json):
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    client = api_conexao.conectar_google_sheets(credenciais_json, scope)
    
    planilha = api_conexao.obter_planilha(client, "monitoramento_imprensa")
    
    api_formatar.formatar_planilha(planilha.sheet1)
    
    sheet = planilha.sheet1
    
    for noticia in noticias:
        titulo, autor, data, corpo, link_canonical = noticia
        
        if verificar_link_existe(sheet, link_canonical):
            print(f"Notícia com link {link_canonical} já existente. Ignorando.")
            continue
        
        palavras_titulo = verificar_palavras_chave(titulo, palavras_chave)
        palavras_corpo = verificar_palavras_chave(corpo, palavras_chave)
        todas_palavras = palavras_titulo.union(palavras_corpo)  # Combina palavras do título e do corpo

        if todas_palavras:
            linha = [
                "Correio de Minas",  # Portal
                data,                # Data
                autor,               # Autor
                titulo,              # Título
                corpo,               # Corpo
                ", ".join(todas_palavras),  # Palavras-Chave
                link_canonical,      # Link
                "",                  # Pontuação (vazio)
                ""                   # Classificação (vazio)
            ]
            
            try:
                sheet.append_row(linha)
                print(f"Notícia adicionada: {titulo}")
            except Exception as e:
                print(f"Erro ao adicionar notícia: {e}")

from config.keywords import palavras

def filtrar_noticias(titulo, corpo):
    if "Minas Gerais" not in titulo and "Minas Gerais" not in corpo and "MG" not in titulo and "MG" not in corpo:
        return False

    for palavra in palavras:
        if palavra in titulo or palavra in corpo:
            return True

    return False

# Exemplo de uso
titulo = "Economia de Minas Gerais em alta"
corpo = "A economia de MG continua crescendo apesar dos desafios."

if filtrar_noticias(titulo, corpo):
    print("Notícia relevante")
else:
    print("Notícia irrelevante")
