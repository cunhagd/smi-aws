from bs4 import BeautifulSoup
from datetime import datetime
from config.keywords import palavras_obrigatorias, palavras_adicionais
from config.classes import VerificarPalavrasChave
from config.classes import AcessarCodigoFonte
from config.classes import GerenciadorNoticias
from config.classes import ProcessadorTextoNoticias
from config.classes import VerificarDataAtual
from urllib.parse import urljoin
import locale

url = "https://www.gentedeopiniao.com.br/"
portal_chave = 'gentedeopniao'
    
def extrair_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    links_noticias = set()
    
    for link in soup.find_all("a", href=True):
        url_relativa = link["href"]
        url_completa = urljoin(base_url, url_relativa)

        if url_completa.count('-') > 2:

            links_noticias.add(url_completa)

    return list(links_noticias)

locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
def formatar_data(data_str):
    try:
        data_bruta = data_str.split(",")[1].split("-")[0].strip()
        data_formatada = datetime.strptime(data_bruta, '%d de %B de %Y').strftime('%d/%m/%Y')
        return data_formatada
    except ValueError as e:
        print(f"Erro ao formatar data '{data_str}': {e}")
        return "Data não encontrada"

def extrair_dados_noticia(url):
    acesso = AcessarCodigoFonte(url)
    html = acesso.acessar()
    processador_texto = ProcessadorTextoNoticias(portal_chave)
    if html is None:
        print(f"Erro ao acessar a página: {url}")
        return None
    
    soup = BeautifulSoup(html, "html.parser")
    
    titulo = soup.select_one("h1.article-title")
    titulo_texto = titulo.get_text(strip=True) if titulo else "Título não encontrado"

    autor = soup.select_one("h6.custom-h a.custom-link-noticia")
    autor_texto = autor.get_text(strip=True) if autor else "Redação Gente de Opnião"

    data = soup.select_one("p.article-published")
    data_texto = formatar_data(data.get_text(strip=True)) if data else "Data não encontrada"

    corpo = soup.select("div.texto p")
    corpo_paragrafos = [p.get_text(separator=' ', strip=True) for p in corpo]
    corpo_texto = processador_texto.formatar_corpo(corpo_paragrafos) if corpo_paragrafos else "Corpo da notícia não encontrado"

    link_texto = url

    return titulo_texto, autor_texto, data_texto, corpo_texto, link_texto

def main():
    nome_portal = "Gente de Opnião"
    acesso = AcessarCodigoFonte(url)
    html = acesso.acessar()
    links_noticias = extrair_links(html, url)
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
