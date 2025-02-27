from bs4 import BeautifulSoup
from config.keywords import palavras_obrigatorias, palavras_adicionais
from config.classes import VerificarPalavrasChave
from config.classes import AcessarCodigoFonte
from config.classes import GerenciadorNoticias
from config.classes import ProcessadorTextoNoticias
from config.classes import VerificarDataAtual
from datetime import datetime
import locale

url = "https://sindsaudemg.org.br/"
portal_chave = 'sindsaude'

def extrair_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links_noticias = set()

    for link in soup.find_all("a", href=True):
        url = link["href"]
        if (
            url.count('/') > 2
            and url.count('-') > 3
        ):
            links_noticias.add(url)

    return list(links_noticias)

def formatar_data(data_str):
    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')  
        data = datetime.strptime(data_str, "%d de %B de %Y") 
        return data.strftime("%d/%m/%Y")  
    except ValueError as e:
        return "Data não encontrada"

def formatar_data(data_str):
    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
        data = datetime.strptime(data_str, "%Y-%m-%dT%H:%M:%S%z")
        return data.strftime("%d/%m/%Y")
    except ValueError as e:
        print(f"Erro ao formatar data: {e}")
        return "Data não encontrada"

def extrair_dados_noticia(url):
    acesso = AcessarCodigoFonte(url)
    html = acesso.acessar()
    processador_texto = ProcessadorTextoNoticias(portal_chave)
    if html is None:
        print(f"Erro ao acessar a página: {url}")
        return None

    soup = BeautifulSoup(html, "html.parser")

    titulo = soup.select_one("h1.entry-title")
    titulo_texto = titulo.get_text(strip=True) if titulo else "Título não encontrado"

    data = soup.select_one("time.entry-date.published")
    if data and data.has_attr('datetime'):
        data_texto = formatar_data(data['datetime'])
    else:
        data_texto = "Data não encontrada"

    autor = soup.select_one("span.author.vcard a.url.fn.n")
    autor_texto = autor.get_text(strip=True) if autor else "Redação Sind Saude"

    corpo = soup.select("div.entry-content.clearfix p")
    corpo_paragrafos = list(set([p.get_text(separator=' ', strip=True) for p in corpo if p.get_text(strip=True) not in ['.', '']]))
    corpo_texto = processador_texto.formatar_corpo(corpo_paragrafos) if corpo_paragrafos else "Corpo da notícia não encontrado"

    link = soup.select_one("link[rel='canonical']")
    link_texto = link.get("href") if link else "Link não encontrado"

    return titulo_texto, autor_texto, data_texto, corpo_texto, link_texto

def main():
    nome_portal = "Sind-Saúde (MG)"
    acesso = AcessarCodigoFonte(url)
    html = acesso.acessar()
    links_noticias = extrair_links(html)
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
