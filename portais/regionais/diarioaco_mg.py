import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from config import api_conexao, api_formatar, keywords
from urllib.parse import urljoin
from config.portais import portais as portais
from frases_negativas import frases_negativas

portal_chave = 'diarioaco_mg'
url = 'https://www.diariodoaco.com.br/minas'
dominio_principal = 'https://www.diariodoaco.com.br'

def acessar_codigo_fonte(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def extrair_links(html, dominio_principal):
    soup = BeautifulSoup(html, 'html.parser')
    links_noticias = set()
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        
        if href.startswith('./'):
            href = href[1:]

        full_url = urljoin(dominio_principal, href)
        
        if (
            '/noticia/' in full_url
            and full_url.count('-') > 3
            and full_url.count('/') > 3
        ):
            links_noticias.add(full_url)

    return list(links_noticias)

def formatar_data(data_texto):
    meses = {
        "janeiro": "01",
        "fevereiro": "02",
        "março": "03",
        "abril": "04",
        "maio": "05",
        "junho": "06",
        "julho": "07",
        "agosto": "08",
        "setembro": "09",
        "outubro": "10",
        "novembro": "11",
        "dezembro": "12"
    }

    data_texto = data_texto.replace(',', '').replace(' ', '')
    partes_data = data_texto.split()
    dia = partes_data[0].zfill(2)
    mes = meses.get(partes_data[1].lower(), "00")
    ano = partes_data[2]

    return f"{dia}/{mes}/{ano}"

def verificar_data_atual(data_texto):
    data_atual = datetime.now().strftime("%d/%m/%Y")
    print(f"Data atual: {data_atual}")  # Depuração
    print(f"Data da notícia: {data_texto}")  # Depuração
    return data_texto == data_atual

def filtrar_corpo(corpo_texto, dominio):
    frases = frases_negativas.frases_negativas.get(dominio, set())
    for frase in frases:
        corpo_texto = corpo_texto.replace(frase, "")
    return corpo_texto.strip()

def formatar_corpo(paragrafos):
    return "\n\n".join(paragrafos)

def verificar_palavras_chave(texto_noticia, palavras_obrigatorias, palavras_adicionais):
    palavras_obrigatorias_encontradas = [palavra for palavra in palavras_obrigatorias if palavra in texto_noticia]
    palavras_adicionais_encontradas = [palavra for palavra in palavras_adicionais if palavra in texto_noticia]
    
    contem_palavra_obrigatoria = bool(palavras_obrigatorias_encontradas)
    contem_palavra_adicional = bool(palavras_adicionais_encontradas)
    
    return contem_palavra_obrigatoria and contem_palavra_adicional, palavras_obrigatorias_encontradas, palavras_adicionais_encontradas

def buscar_pontos():
    pontuacao = portais.get(portal_chave, {}).get('pontos', 'Pontuação não encontrada.')
    return pontuacao

def buscar_abrangencia():
    abrangencia = portais.get(portal_chave, {}).get('abrangencia', 'Abrangência não encontrada.')
    return abrangencia

def ajustar_pontuacao(texto):
    texto_ajustado = re.sub(r'(?<=[.!?])\s*(?=\w)', ' ', texto)
    return texto_ajustado.capitalize()

def encontrar_titulo_e_remover(texto, titulo):
    titulo_normalizado = titulo.lower().strip()
    partes = texto.lower().split(titulo_normalizado)

    if len(partes) > 1:
        corpo_apos_titulo = partes[1].strip()
        corpo_apos_titulo = re.sub(r'(?<=[.!?])\s*(?=\w)', ' ', corpo_apos_titulo).capitalize()

        return corpo_apos_titulo
    else:
        return "Título não encontrado no corpo do texto."

def extrair_dados_noticia(url):
    html = acessar_codigo_fonte(url)
    soup = BeautifulSoup(html, "html.parser")

    titulo = soup.select_one("h2")
    autor = soup.select_one("span.credito")
    data = soup.select_one("div.date time")
    corpo = soup.select("div.main-post.mt-30")
    link = soup.select_one("link[rel='canonical']")

    for elemento in soup.select("span.credito, span.titulo_legenda, div.row.mt-20.pr-20.text-right"):
        elemento.decompose()

    corpo_texto = " ".join(p.get_text(strip=True) for p in corpo)
    
    dominio = url.split('/')[2]

    titulo_texto = titulo.get_text(strip=True) if titulo else "Título não encontrado"
    
    if data and 'datetime' in data.attrs:
        data_texto = formatar_data(data['datetime'])
    else:
        corpo_texto = " ".join(p.get_text(strip=True) for p in corpo)
        data_possivel = corpo_texto.split('|')[0].strip()
        data_texto = formatar_data(data_possivel)
    
    corpo_texto = encontrar_titulo_e_remover(corpo_texto, titulo_texto)
    corpo_texto = filtrar_corpo(corpo_texto, dominio)
    corpo_texto = ajustar_pontuacao(corpo_texto)
    corpo_texto = formatar_corpo([paragrafo.strip() for paragrafo in corpo_texto.split('\n')])
    
    autor_texto = autor.get_text(strip=True) if autor else "Diário do Aço"

    return titulo_texto, autor_texto, data_texto, corpo_texto, link.get("href") if link else "Link não encontrado"

def verificar_link_existe(sheet, link):
    celulas = sheet.col_values(7)
    return link in celulas

def salvar_noticias(noticias, credenciais_json, pontuacao, abrangencia):
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    client = api_conexao.conectar_google_sheets(credenciais_json, scope)

    planilha = api_conexao.obter_planilha(client, "SIS de Monitoramento de Imprensa")
    api_formatar.formatar_planilha(planilha.sheet1)
    sheet = planilha.sheet1

    for noticia in noticias:
        titulo, autor, data, corpo, link_canonical, palavras_obrigatorias_encontradas, palavras_adicionais_encontradas = noticia

        if verificar_link_existe(sheet, link_canonical):
            print(f"Notícia com link {link_canonical} já existente. Ignorando.")
            continue

        # Concatenar palavras-chave em uma string separada por vírgulas
        palavras_chave = ', '.join(palavras_obrigatorias_encontradas + palavras_adicionais_encontradas)

        linha = [
            "Diario do Aço (MG)",
            data,
            autor,
            titulo,
            corpo,
            palavras_chave,
            link_canonical,
            pontuacao,
            abrangencia,
            "",
        ]

        try:
            sheet.append_row([str(col) for col in linha])
            print(f"Notícia adicionada: {titulo}")
        except Exception as e:
            print(f"Erro ao adicionar notícia: {e}")

def main():
    html = acessar_codigo_fonte(url)
    links_noticias = extrair_links(html, dominio_principal)
    noticias_para_salvar = []
    pontuacao = buscar_pontos()
    abrangencia = buscar_abrangencia()

    for link in links_noticias:
        dados_noticia = extrair_dados_noticia(link)
        titulo, autor, data, corpo, link_canonical = dados_noticia

        # Verificar se a data da notícia é igual à data atual
        if verificar_data_atual(data):
            print("A data da notícia é igual à data atual.")
        else:
            print(f"A data da notícia ({data}) é diferente da data atual. Ignorando.")
            continue  # Se a data for diferente da atual, ignorar a notícia

        # Verificação com a nova função de palavras-chave e depuração
        palavras_obrigatorias_encontradas = []  # Inicializa para cada notícia
        palavras_adicionais_encontradas = []    # Inicializa para cada notícia

        contem_palavras, palavras_obrigatorias_encontradas_tmp, palavras_adicionais_encontradas_tmp = verificar_palavras_chave(
            titulo.lower(), keywords.palavras_obrigatorias, keywords.palavras_adicionais
        )

        if not contem_palavras:
            contem_palavras, palavras_obrigatorias_encontradas_tmp, palavras_adicionais_encontradas_tmp = verificar_palavras_chave(
                corpo.lower(), keywords.palavras_obrigatorias, keywords.palavras_adicionais
            )

        # Adicionar as palavras encontradas na lista para a notícia atual
        palavras_obrigatorias_encontradas.extend(palavras_obrigatorias_encontradas_tmp)
        palavras_adicionais_encontradas.extend(palavras_adicionais_encontradas_tmp)

        # Adiciona notícia se atender aos critérios de palavras-chave
        if contem_palavras:
            noticias_para_salvar.append(dados_noticia + (palavras_obrigatorias_encontradas, palavras_adicionais_encontradas))
            print("A notícia CONTÉM SIM as palavras necessárias.")
        else:
            print("A notícia NÃO CONTÉM as palavras necessárias.")
        
        print("="*80)

    print(f"Total de links encontrados: {len(links_noticias)}")
    print(f"Total de notícias filtradas para salvar: {len(noticias_para_salvar)}")
    print("="*80)

    credenciais_json = CREDENCIAIS_PATH
    salvar_noticias(noticias_para_salvar, credenciais_json, pontuacao, abrangencia)
    
if __name__ == "__main__":
    main()

