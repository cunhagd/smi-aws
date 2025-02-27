from bs4 import BeautifulSoup
from datetime import datetime
from config.keywords import palavras_obrigatorias, palavras_adicionais
from config.classes import VerificarPalavrasChave
from config.classes import AcessarCodigoFonte
from config.classes import GerenciadorNoticias
from config.classes import ProcessadorTextoNoticias
from config.classes import VerificarDataAtual

url = "https://noticias.r7.com/"
portal_chave = "record"

def extrair_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links_noticias = set()

    for link in soup.find_all('a', href=True):
        url = link["href"]
        ano_atual = datetime.now().year 
        mes_atual = datetime.now().month
        dia_atual = datetime.now().day
        mes_atual_formatado = f"{mes_atual:02}"
        dia_atual_formatado = f"{dia_atual:02}"

        if(
            f"-{dia_atual_formatado}{mes_atual_formatado}{ano_atual}/" in url
        ):
            links_noticias.add(url)

    return list(links_noticias)

def formatar_data(html):
    soup = BeautifulSoup(html, "html.parser")
    time_element = soup.find("time", {"itemprop": "datePublished"})
    
    if time_element and 'datetime' in time_element.attrs:
        data_iso = time_element['datetime']
        data_obj = datetime.strptime(data_iso.split("T")[0], "%Y-%m-%d")
        data_formatada = data_obj.strftime("%d/%m/%Y")
        return data_formatada
    else:
        return "Data não encontrada"

def extrair_dados_noticia(url):
    acesso = AcessarCodigoFonte(url)
    html = acesso.acessar()
    soup = BeautifulSoup(html, "html.parser")

    titulo = soup.find("h1", class_="base-font-primary")
    autor = soup.find("p", class_="article-text-xxxs")
    corpo = soup.select_one("p.dark\\:base-text-neutral-high-400.base-text-\\[calc\\(theme\\(fontSize\\.xs\\)_\\*_var\\(--font-size\\,_1\\)\\)\\].base-font-normal.base-font-primary.base-text-neutral-low-500.base-text-left").get_text(" ", strip=True)

    titulo_texto = titulo.get_text(strip=True) if titulo else "Título não encontrado"
    
    if autor:
        autor_texto = autor.get_text(strip=True)
        if autor_texto.lower().startswith("por"):
            autor_texto = autor_texto[3:].strip()
        autor_texto = autor_texto.split(",")[0]
    else:
        autor_texto = "Redação R7"

    data_texto = formatar_data(html)  
    corpo_texto = corpo
    
    link_canonical = url

    return titulo_texto, autor_texto, data_texto, corpo_texto, link_canonical

def main():
    nome_portal = "Record R7"
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
