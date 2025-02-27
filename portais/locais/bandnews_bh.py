from bs4 import BeautifulSoup
from urllib.parse import urljoin
from config.keywords import palavras_obrigatorias, palavras_adicionais
from config.classes import AcessarCodigoFonte
from config.classes import ProcessadorTextoNoticias
from config.classes import VerificarPalavrasChave
from config.classes import GerenciadorNoticias
from config.classes import VerificarDataAtual

url = "https://www.band.uol.com.br/bandnews-fm/belo-horizonte"
portal_chave = 'bandnews_bh'

def extrair_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links_noticias = set()
    dominio_principal = "https://www.band.uol.com.br"

    for link in soup.find_all("a", href=True):
        url = link["href"]

        full_url = urljoin(dominio_principal, url)
        if (
            '/noticias/' in full_url  
            and full_url.count('-') > 4 
            and full_url.count('/') > 3 
        ):
            links_noticias.add(full_url)

    return list(links_noticias)

def formatar_data(data_texto):
    try:
        data_partes = data_texto.split(' ')[0] 
        ano, mes, dia = data_partes.split('-')  
        data_formatada = f"{dia.zfill(2)}/{mes.zfill(2)}/{ano.zfill(4)}"
        return data_formatada
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

    titulo = soup.select_one("h1.title")
    titulo_texto = titulo.get_text(strip=True) if titulo else "Título não encontrado"
    
    data = soup.select_one("time[datetime]")
    data_texto = "Data não encontrada"
    if data:
        data_texto = formatar_data(data['datetime'])
    
    autor = soup.select_one("p.author__name i")
    if autor:
        autor_texto = autor.get_text(strip=True)
        if autor_texto.lower().startswith("por"):
            autor_texto = autor_texto[3:].strip()
        autor_texto = autor_texto.split(",")[0]
    else:
        autor_texto = "Redação Band News"

    corpo = soup.select("div.article__content p")
    corpo_paragrafos = [p.get_text(strip=True) for p in corpo]
    corpo_texto = processador_texto.formatar_corpo(corpo_paragrafos)

    link = soup.select_one("link[rel='canonical']")
    link_texto = link.get("href") if link else "Link não encontrado"

    return titulo_texto, autor_texto, data_texto, corpo_texto, link_texto

def main():
    nome_portal = "Band News BH"
    acesso = AcessarCodigoFonte(url, usar_headers=True)
    html = acesso.acessar()
    links_noticias = extrair_links(html)
    noticias_para_salvar = []
    
    processar_texto = ProcessadorTextoNoticias(portal_chave=portal_chave)
    pontuacao = processar_texto.buscar_pontos()
    abrangencia = processar_texto.buscar_abrangencia()
    
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
        
            print("="*80)
            print(f"Título: {titulo}")
            print(f"Autor: {autor}")
            print(f"Data: {data}")
            print(f"Link: {link_canonical}")
            print(f"Pontuação de '{portal_chave}': {pontuacao}")
            print(f"Abrangência de '{portal_chave}': {abrangencia}")
            print(f"Palavras obrigatórias encontradas: {palavras_obrigatorias_encontradas}")
            print(f"Palavras adicionais encontradas: {palavras_adicionais_encontradas}")
        
            print("="*80)
        
        except Exception as e:
            print(f"Erro ao processar a notícia no link {link}: {e}")
            continue

    gerenciador_noticias = GerenciadorNoticias(pontuacao, abrangencia, nome_portal)
    gerenciador_noticias.salvar_noticias(noticias_para_salvar)

if __name__ == "__main__":
    main()
