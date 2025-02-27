from bs4 import BeautifulSoup
from datetime import datetime
from config.keywords import palavras_obrigatorias, palavras_adicionais
from config.classes import VerificarPalavrasChave
from config.classes import AcessarCodigoFonte
from config.classes import GerenciadorNoticias
from config.classes import ProcessadorTextoNoticias
from config.classes import VerificarDataAtual
from urllib.parse import urljoin
import re


portal_chave = 'em'
dominio_principal = "https://www.em.com.br/"
urls = [
    "https://www.em.com.br/",
    "https://www.em.com.br/politica",
    "https://www.em.com.br/economia",
    "https://www.em.com.br/gerais"
]


def extrair_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    links_noticias = set()
    ano_atual = datetime.now().year
    mes_atual = datetime.now().month

    for link in soup.find_all("a", href=True):
        url = link["href"]
        url = urljoin(base_url, url)

        if any(redes in url for redes in ["twitter.com", "facebook.com", "instagram.com"]):
            continue
        
        if (
            (f"/{ano_atual:04}/{mes_atual}/" in url or f"/{ano_atual}/{mes_atual:02}/" in url)
            and url.startswith('https://www.em.com.br')
            and "/esportes/" not in url
            and "/entretenimento/" not in url
            and "/horoscopo/" not in url
            and "/mundo/" not in url
        ):
            links_noticias.add(url)

    return list(links_noticias)

def formatar_data(data_str):
    try:
        data_obj = datetime.strptime(data_str, "%d/%m/%Y")
        return data_obj.strftime("%d/%m/%Y")
    except ValueError:
        return "Data não encontrada"
    
def extrair_dados_noticia(url):
    acesso = AcessarCodigoFonte(url)
    html = acesso.acessar()
    processador_texto = ProcessadorTextoNoticias(portal_chave)
    if html is None:
        return None
    soup = BeautifulSoup(html, "html.parser")

    titulo = soup.select_one("h1")
    autor = soup.select_one("div.author a span.author-name")
    
    # Captura a data diretamente no texto usando regex
    html_text = soup.get_text()
    data_regex = re.search(r"\d{2}/\d{2}/\d{4}", html_text)
    
    if data_regex:
        data_texto = data_regex.group(0)
        data_formatada = formatar_data(data_texto)
    else:
        # Caso o regex não encontre, tenta capturar via seletor
        data_element = soup.select_one("span.f-roboto.publication strong.f-roboto")
        if data_element:
            data_texto = data_element.get_text(strip=True)
            data_formatada = formatar_data(data_texto)
        else:
            data_formatada = "Data não encontrada"

    corpo = soup.select("p.texto")
    link = soup.select_one("link[rel='canonical']")

    titulo_texto = titulo.get_text(strip=True) if titulo else "Título não encontrado"
    
    # Corrige a vírgula entre os nomes dos autores
    if autor:
        autor_texto = autor.get_text(strip=True)
        autor_texto = autor_texto.replace(',', ', ')
    else:
        autor_texto = "Redação Estado de Minas"
    
    corpo_paragrafos = [p.get_text(strip=True) for p in corpo]
    corpo_texto = processador_texto.formatar_corpo(corpo_paragrafos)
    link_texto = link.get("href") if link else "Link não encontrado"

    return titulo_texto, autor_texto, data_formatada, corpo_texto, link_texto

def main():
    nome_portal = "EM"
    links_noticias = set()

    print(f"[DEBUG] Iniciando scraping para o portal: {nome_portal}")

    for url in urls:
        print(f"[DEBUG] Acessando URL: {url}")
        acesso = AcessarCodigoFonte(url)
        html = acesso.acessar()

        if html:
            print(f"[DEBUG] HTML obtido com sucesso de: {url}")
        else:
            print(f"[DEBUG] Falha ao acessar o HTML de: {url}")
            continue

        links_encontrados = extrair_links(html, url)
        print(f"[DEBUG] Links encontrados em {url}: {len(links_encontrados)}")
        links_noticias.update(links_encontrados)

    print(f"[DEBUG] Total de links coletados: {len(links_noticias)}")
    print("[DEBUG] Links coletados:")

    noticias_para_salvar = []

    processador_texto = ProcessadorTextoNoticias(portal_chave=portal_chave)
    pontuacao = processador_texto.buscar_pontos()
    abrangencia = processador_texto.buscar_abrangencia()

    # Instância da classe VerificarPalavrasChave
    verificacao = VerificarPalavrasChave(palavras_obrigatorias, palavras_adicionais)

    for link in links_noticias:
        try:
            dados_noticia = extrair_dados_noticia(link)

            if dados_noticia is None:
                print(f"Falha ao extrair dados da notícia em {link}. Ignorando.")
                continue

            titulo, autor, data, corpo, link_canonical = dados_noticia

            if not VerificarDataAtual.verificar_data_atual(data):
                continue

            # Verificar palavras no título
            contem_palavras, palavras_obrigatorias_encontradas, palavras_adicionais_encontradas = verificacao.verificar(titulo)

            # Se não contém as palavras no título, verificar no corpo
            if not contem_palavras:
                contem_palavras, palavras_obrigatorias_encontradas, palavras_adicionais_encontradas = verificacao.verificar(corpo)

            if contem_palavras:
                noticias_para_salvar.append((dados_noticia, palavras_obrigatorias_encontradas, palavras_adicionais_encontradas))

        except Exception as e:
            print(f"Erro ao processar a notícia no link {link}: {e}")
            continue

    gerenciador_noticias = GerenciadorNoticias(pontuacao, abrangencia, nome_portal)
    gerenciador_noticias.salvar_noticias(noticias_para_salvar)

if __name__ == "__main__":
    main()
