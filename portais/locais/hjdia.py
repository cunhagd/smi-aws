from bs4 import BeautifulSoup
from config.keywords import palavras_obrigatorias, palavras_adicionais
from config.classes import VerificarPalavrasChave
from config.classes import AcessarCodigoFonte
from config.classes import GerenciadorNoticias
from config.classes import ProcessadorTextoNoticias
from config.classes import VerificarDataAtual
from urllib.parse import urljoin

url = 'https://www.hojeemdia.com.br/'
dominio_principal = 'https://www.hojeemdia.com.br'
portal_chave = 'hjdia'

def extrair_links(html, dominio_principal):
    if html is None:
        print("Erro: HTML não obtido.")
        return []  # Retorna uma lista vazia se o HTML for None
    
    soup = BeautifulSoup(html, 'html.parser')
    links_noticias = set()
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        full_url = urljoin(dominio_principal, href)
        
        if (
            '/minas/' in full_url
            and full_url.count('-') > 3
            and full_url.count('/') > 3
        ):
            links_noticias.add(full_url)

    return list(links_noticias)

def formatar_data(data_str):
    return data_str.split(' ')[0]

def extrair_dados_noticia(url):
    acesso = AcessarCodigoFonte(url)
    html = acesso.acessar()
    processador_texto = ProcessadorTextoNoticias(portal_chave)
    soup = BeautifulSoup(html, "html.parser")

    titulo = soup.select_one("h1.styled__HeadingOne-sc-fdx3oi-0.bkwaWa")
    titulo_texto = titulo.get_text(strip=True) if titulo else "Título não encontrado"

    autor = soup.select_one("div.Block__Component-sc-1uj1scg-0 bMaved span.styled__Span-sc-fdx3oi-7 bLaGAa")
    autor_texto = autor.get_text(strip=True) if autor else "Redação Hoje em Dia"

    spans = soup.select("div.Block__Component-sc-1uj1scg-0 span.styled__Span-sc-fdx3oi-7.gQSNuO")
    
    data_texto = "Data não encontrada"
    for span in spans:
        span_texto = span.get_text(strip=True)
        if span_texto.count('/') == 2:  
            data_texto = formatar_data(span_texto)
            break 

    corpo = soup.select("div.Block__Component-sc-1uj1scg-0 p.styled__Paragraph-sc-fdx3oi-6.eValfS")
    corpo_paragrafos = [p.get_text(strip=True) for p in corpo]
    corpo_texto = processador_texto.formatar_corpo(corpo_paragrafos)

    link = soup.select_one("link[rel='canonical']")
    link_texto = link.get("href") if link else "Link não encontrado"

    return titulo_texto, autor_texto, data_texto, corpo_texto, link_texto

def main():
    nome_portal = "Hoje em Dia"
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
