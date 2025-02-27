from bs4 import BeautifulSoup
from config.keywords import palavras_obrigatorias, palavras_adicionais
from config.classes import VerificarPalavrasChave
from config.classes import AcessarCodigoFonte
from config.classes import GerenciadorNoticias
from config.classes import ProcessadorTextoNoticias
from config.classes import VerificarDataAtual
from datetime import datetime

url = "https://portalc1.com.br/"
portal_chave = 'correiosul'

def extrair_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links_noticias = set()

    for link in soup.find_all("a", href=True):
        url = link["href"]
        if (
            url.count('/') > 3
            and url.count('-') > 2  
        ):
            links_noticias.add(url)
            
    return list(links_noticias)

def formatar_data(data_str):
    try:
        data = datetime.strptime(data_str, '%Y-%m-%d')
        return data.strftime('%d/%m/%Y')
    except Exception as e:
        print(f"Erro ao formatar a data: {e}")
        return "Data inválida"
    
def extrair_dados_noticia(url):
    acesso = AcessarCodigoFonte(url, usar_headers=True)
    html = acesso.acessar()
    processador_texto = ProcessadorTextoNoticias(portal_chave)
    if html is None:
        print(f"Erro ao acessar a página: {url}")
        return None
    
    soup = BeautifulSoup(html, "html.parser")

    titulo = soup.select_one("h1.tdb-title-text")
    titulo_texto = titulo.get_text(strip=True) if titulo else "Título não encontrado"
    
    autor = soup.select_one('meta[name=author]')
    autor_texto = autor.get('content') if autor else "Redação Correio do Sul"

    data = soup.select_one('time.entry-date.updated.td-module-date')
    if data and 'datetime' in data.attrs:
        data_texto = formatar_data(data['datetime'].split('T')[0])
    else:
        data_texto = "Data não encontrada"
        
    corpo = soup.select("div.tdb-block-inner.td-fix-index p")
    corpo_paragrafos = [span.get_text(separator=' ', strip=True) for span in corpo]
    corpo_texto = processador_texto.formatar_corpo(corpo_paragrafos)
    
    link = soup.select_one("link[rel='canonical']")
    link_texto = link.get("href") if link else "Link não encontrado"
    return titulo_texto, autor_texto, data_texto, corpo_texto, link_texto

def main():
    nome_portal = "Correio do Sul"
    acesso = AcessarCodigoFonte(url, usar_headers=True)
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
