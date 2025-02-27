from bs4 import BeautifulSoup
from config.keywords import palavras_obrigatorias, palavras_adicionais
from datetime import datetime
from config.classes import VerificarPalavrasChave
from config.classes import AcessarCodigoFonte
from config.classes import GerenciadorNoticias
from config.classes import ProcessadorTextoNoticias
from config.classes import VerificarDataAtual

url = "https://cbn.globo.com/programas/cbn-bh/"
portal_chave = 'cbn'

acesso = AcessarCodigoFonte(url)
    
def extrair_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links_noticias = set()

    for link in soup.find_all("a", href=True):
        url = link["href"]
        ano_atual = datetime.now().year
        mes_atual = datetime.now().month
        dia_atual = datetime.now().day
        mes_atual_formatado = f"{mes_atual:02}"
        dia_atual_formatado = f"{dia_atual:02}"

        if (
            f"-{ano_atual:04}{mes_atual_formatado}{dia_atual_formatado}" in url
            and url.count('/') > 2
            and url.count('-') > 3
            and '/podcasts/' not in url
        ):
            links_noticias.add(url)

    return list(links_noticias)

def formatar_data(data_str):
    try:
        data = datetime.fromisoformat(data_str[:-6])  
        return data.strftime("%d/%m/%Y")  
    except ValueError as e:
        print(f"Erro ao formatar data: {e}")
        return "Data não encontrada"

def extrair_dados_noticia(url):
    acesso = AcessarCodigoFonte(url)
    html = acesso.acessar()
    processador_texto = ProcessadorTextoNoticias(portal_chave)
    
    soup = BeautifulSoup(html, "html.parser")
    
    titulo = soup.select_one("div.title h1")
    titulo_texto = titulo.get_text(strip=True) if titulo else "Título não encontrado"
    
    autor = soup.select_one("address[itemprop='author'] span[itemprop='name']")
    autor_texto = autor.get_text(strip=True) if autor else "Redação CBN BH"
    
    data = soup.select_one("time[itemprop='datePublished']")
    data_texto = formatar_data(data['datetime']) if data else "Data não encontrada"

    corpo = soup.select("div.mc-column.content-text.active-extra-styles p.content-text__container, div.mc-column.content-text.active-extra-styles blockquote.content-blockquote")
    corpo_paragrafos = [p.get_text(separator=' ', strip=True) for p in corpo if p.get_text(strip=True)]
    corpo_texto = ' '.join(corpo_paragrafos) if corpo_paragrafos else "Corpo da notícia não encontrado"
    corpo_texto = processador_texto.formatar_corpo(corpo_paragrafos)
    
    link = soup.select_one("link[rel='canonical']")
    link_texto = link.get("href") if link else "Link não encontrado"

    return titulo_texto, autor_texto, data_texto, corpo_texto, link_texto

def main():
    nome_portal = "CBN BH"
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
