from bs4 import BeautifulSoup
from datetime import datetime
from config.keywords import palavras_obrigatorias, palavras_adicionais
from config.classes import VerificarPalavrasChave
from config.classes import AcessarCodigoFonte
from config.classes import GerenciadorNoticias
from config.classes import ProcessadorTextoNoticias
from config.classes import VerificarDataAtual

url = "https://www1.folha.uol.com.br/folha-topicos/minas-gerais-estado/"
portal_chave = 'folha'

def extrair_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links_noticias = set()
    ano_atual = datetime.now().year
    mes_atual = datetime.now().month

    for link in soup.find_all("a", href=True):
        url = link["href"]
        if (
            f"/{ano_atual:04}/{mes_atual:02}/" in url
            and "/esportes/" not in url
            and "/entretenimento/" not in url
            and "/seminariosfolha/" not in url
        ):
            links_noticias.add(url)
            
    return list(links_noticias)

def formatar_data(data_str):
    if not data_str:
        return "Data não encontrada"
    try:
        data_str = data_str.split(' ')[0]
        ano, mes, dia = data_str.split('-')
        return f'{dia}/{mes}/{ano}'
    except Exception as e:
        print(f"Erro ao formatar a data: {e}")
        return "Data inválida"

def extrair_dados_noticia(url):
    acesso = AcessarCodigoFonte(url)
    html = acesso.acessar()
    processador_texto = ProcessadorTextoNoticias(portal_chave)
    if html is None:
        print(f"Erro ao acessar a página: {url}")
        return None
    
    soup = BeautifulSoup(html, "html.parser")

    titulo = soup.select_one("h1.c-content-head__title")
    autor = soup.select_one("div.c-signature")
    data = soup.select_one("time.c-more-options__published-date")
    corpo = soup.select("div.c-news__body p")
    link = soup.select_one("link[rel='canonical']")

    titulo_texto = titulo.get_text(strip=True) if titulo else "Título não encontrado"
    if autor:
        autor_texto = autor.get_text(strip=True)
        if autor_texto.lower().startswith("por"):
            autor_texto = autor_texto[3:].strip()
        autor_texto = autor_texto.split(",")[0]
    else:
        autor_texto = "Folha de SP"

    data_texto = data.get('datetime') if data else "Data não encontrada"
    data_texto = formatar_data(data_texto)

    corpo_paragrafos = [p.get_text(separator=' ', strip=False) for p in corpo]
    corpo_texto = processador_texto.formatar_corpo(corpo_paragrafos)
    link_texto = link.get("href") if link else "Link não encontrado"

    return titulo_texto, autor_texto, data_texto, corpo_texto, link_texto

def main():
    nome_portal = "Folha (MG)"
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
