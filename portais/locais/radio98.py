from bs4 import BeautifulSoup
from datetime import datetime
from config.keywords import palavras_obrigatorias, palavras_adicionais
from config.classes import VerificarPalavrasChave
from config.classes import AcessarCodigoFonte
from config.classes import GerenciadorNoticias
from config.classes import ProcessadorTextoNoticias
from config.classes import VerificarDataAtual
from urllib.parse import urljoin

url = "https://www.98live.com.br/"
portal_chave = 'radio98'

def extrair_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    links_noticias = set()
    base_url = "https://www.98live.com.br"

    for link in soup.find_all("a", href=True):
        url_fragmento = link["href"]
        url_completo = urljoin(base_url, url_fragmento)
        if (
            url_completo.count("/") > 4
            and url_completo.count("-") > 3
            and '/noticias/' in url_completo
        ):
            links_noticias.add(url_completo)
    
    return list(links_noticias)

def formatar_data(data_str):
    try:
        data_obj = datetime.strptime(data_str, "%d/%m/%Y")
        data_formatada = data_obj.strftime("%d/%m/%Y")
        return data_formatada
    except ValueError as e:
        return "Data inválida"
    
def extrair_dados_noticia(url):
    acesso = AcessarCodigoFonte(url)
    html = acesso.acessar()
    processador_texto = ProcessadorTextoNoticias(portal_chave)
    if html is None:
        return None
    soup = BeautifulSoup(html, "html.parser")

    titulo = soup.select_one('h1[itemprop="headline"]')
    autor = soup.select_one('span[itemprop="author publisher"]')
    data_element = soup.select_one('time[itemprop="dateCreated datePublished"]')
    corpo = soup.select('section[itemprop="articleBody"] p')

    titulo_texto = titulo.get_text(strip=True) if titulo else "Título não encontrado"
    autor_texto = autor.get_text(strip=True) if autor else "Redação Rádio 98"
    
    if data_element:
        data_texto = data_element.get_text(strip=True)
        data_formatada = formatar_data(data_texto)
    else:
        data_formatada = "Data não encontrada"

    corpo_paragrafos = [p.get_text(strip=True) for p in corpo]
    corpo_texto = processador_texto.formatar_corpo(corpo_paragrafos)

    link_texto = url

    return titulo_texto, autor_texto, data_formatada, corpo_texto, link_texto

def main():
    nome_portal = "Rádio 98"
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
