from bs4 import BeautifulSoup
from datetime import datetime
from config.keywords import palavras_obrigatorias, palavras_adicionais
from config.classes import VerificarPalavrasChave
from config.classes import AcessarCodigoFonte
from config.classes import GerenciadorNoticias
from config.classes import ProcessadorTextoNoticias
from config.classes import VerificarDataAtual
from urllib.parse import urljoin

url = "https://plox.com.br/ipatinga/ultimas-noticias"
portal_chave = 'plox_ultimas'

def extrair_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links_noticias = set()
    dia_atual = datetime.now().day
    mes_atual = datetime.now().month
    ano_atual = datetime.now().year
    dia_atual_formatado = f"{dia_atual:02}"
    mes_atual_formatado = f"{mes_atual:02}"

    for link in soup.find_all("a", href=True):
        href = link["href"]
        full_url = urljoin(url, href)

        if f"/{dia_atual_formatado}/{mes_atual_formatado}/{ano_atual}/" in full_url:
            links_noticias.add(full_url)
            
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

    titulo = soup.select_one("h1.font-bold.text-dark")
    autor = soup.select_one("p.text-base.font-light.text-neutral200")
    corpo = soup.select("div.news-body p")
    link = soup.select_one("link[rel='canonical']")

    titulo_texto = titulo.get_text(strip=True) if titulo else "Título não encontrado"
    autor_texto = autor.get_text(strip=True).replace("Por", "").strip().split(",")[0] if autor else "Redação Plox"
    
    corpo_paragrafos = [p.get_text(strip=True) for p in corpo]
    corpo_texto = processador_texto.formatar_corpo(corpo_paragrafos)
    link_texto = link.get("href") if link else "Link não encontrado"
    data_texto = formatar_data()

    return titulo_texto, autor_texto, data_texto, corpo_texto, link_texto

def main():
    nome_portal = "Plox Últimas"
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
