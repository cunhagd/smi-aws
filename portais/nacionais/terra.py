from bs4 import BeautifulSoup
from datetime import datetime
from config.keywords import palavras_obrigatorias, palavras_adicionais
from config.classes import VerificarPalavrasChave
from config.classes import AcessarCodigoFonte
from config.classes import GerenciadorNoticias
from config.classes import ProcessadorTextoNoticias
from config.classes import VerificarDataAtual

url = 'https://www.terra.com.br/noticias/'
portal_chave = 'terra'

def extrair_links(html, url):
    soup = BeautifulSoup(html, 'html.parser')
    links_noticias = set()
    
    for link in soup.find_all('a', href=True):
        url = link['href']
        if (
            url.startswith("https://www.terra.com.br")
            and url.count('/') > 3
            and url.count('-') > 3
            and "/story/" not in url
            and "/videos/" not in url
            and "/vida-e-estilo/" not in url
        ):
            links_noticias.add(url)
    
    return list(links_noticias)

def formatar_data(data_str):
    partes_data = data_str.split('-')
    ano = partes_data[0]
    mes = partes_data[1]
    dia = partes_data[2]
    data_formatada = f'{dia}/{mes}/{ano}'
    return data_formatada

def verificar_data_atual(data_texto):
    data_atual = datetime.now().strftime("%d/%m/%Y")
    return data_texto == data_atual
    
def extrair_dados_noticia(url):
    acesso = AcessarCodigoFonte(url)
    html = acesso.acessar()
    processador_texto = ProcessadorTextoNoticias(portal_chave)
    if html is None:
        print(f"Erro ao acessar a página: {url}")
        return None
    
    soup = BeautifulSoup(html, "html.parser")
    
    titulo = soup.select_one("div.article__header__headline h1")
    autor = soup.select_one("span.article__header__author__item__name")

    date_meta = soup.select_one('meta[itemprop="datePublished"]')
    
    if date_meta:
        data = date_meta['content'].split('T')[0]
    else:
        data = "Data não encontrada"

    corpo = soup.select("p.text")
    link = soup.select_one("link[rel='canonical']")
    
    data_texto = formatar_data(data) if data != "Data não encontrada" else "Data não encontrada"
    
    titulo_texto = titulo.get_text(strip=True) if titulo else "Título não encontrado"
    autor_texto = autor.get_text(strip=True) if autor else "Redação Terra"
    corpo_paragrafos = [p.get_text(separator=' ', strip=False) for p in corpo]
    corpo_texto = processador_texto.formatar_corpo(corpo_paragrafos)
    link_texto = link.get("href") if link else "Link não encontrado"
    
    return titulo_texto, autor_texto, data_texto, corpo_texto, link_texto

def main():
    nome_portal = "Terra"
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
