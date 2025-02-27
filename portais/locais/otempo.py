from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
from config.keywords import palavras_obrigatorias, palavras_adicionais
from config.classes import VerificarPalavrasChave
from config.classes import AcessarCodigoFonte
from config.classes import GerenciadorNoticias
from config.classes import ProcessadorTextoNoticias
from config.classes import VerificarDataAtual


portal_chave = 'otempo_ultimas'
dominio_principal = "https://www.otempo.com.br/"
urls = [
    "https://www.otempo.com.br/",
    "https://www.otempo.com.br/ultimas",
    "https://www.otempo.com.br/politica",
    "https://www.otempo.com.br/economia",
    "https://www.otempo.com.br/minas-sa"
]


def extrair_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links_noticias = set()
    ano_atual = datetime.now().year
    mes_atual = datetime.now().month
    dia_atual = datetime.now().day

    for link in soup.find_all("a", href=True):
        href = link["href"]
        full_url = urljoin(dominio_principal, href)

        if (
            f"/{ano_atual}/{mes_atual}/{dia_atual}/" in full_url
            and "/entretenimento/" not in full_url
            and "/sports/" not in full_url
            and "/mundo/" not in full_url
            and "/horoscopo/" not in full_url
        ):
            links_noticias.add(full_url)

    return list(links_noticias)

def formatar_data():
    hoje = datetime.now()
    return hoje.strftime("%d/%m/%Y")
    
def extrair_dados_noticia(url):
    acesso = AcessarCodigoFonte(url)
    html = acesso.acessar()
    processador_texto = ProcessadorTextoNoticias(portal_chave)
    soup = BeautifulSoup(html, "html.parser")

    titulo = soup.select_one("h1.cmp__title-title.font-inter.materia__tts")
    autor_span = soup.select("span.cmp__author-name")
    corpo_div = soup.select_one("div.body")
    data_texto = formatar_data()

    link = soup.select_one("link[rel='canonical']")

    titulo_texto = titulo.get_text(strip=True) if titulo else "Título não encontrado"
    autor_texto = autor_span[0].get_text(strip=True) if autor_span and len(autor_span) > 0 else "Autor não encontrado"

    if corpo_div:
        corpo_paragrafos = [p.get_text(strip=True) for p in corpo_div.select("p")]
        corpo_texto = processador_texto.formatar_corpo(corpo_paragrafos)
    else:
        corpo_texto = "Corpo da notícia não encontrado"

    link_texto = link.get("href") if link else "Link não encontrado"

    return titulo_texto, autor_texto, data_texto, corpo_texto, link_texto

def main():
    nome_portal = "O Tempo"
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

        links_encontrados = extrair_links(html)
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
