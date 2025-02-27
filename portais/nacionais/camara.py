from bs4 import BeautifulSoup
from datetime import datetime
import re
from config.keywords import palavras_obrigatorias, palavras_adicionais
from config.classes import AcessarCodigoFonte
from config.classes import ProcessadorTextoNoticias
from config.classes import VerificarPalavrasChave
from config.classes import GerenciadorNoticias
from config.classes import VerificarDataAtual

url = "https://www.camara.leg.br/"
portal_chave = 'camara'
    
def extrair_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links_noticias = set()

    for link in soup.find_all("a", href=True):
        url = link["href"]
        if (
            url.count('/') > 4
            and url.count('-') > 3
            and "/noticias/" in url
        ):
            links_noticias.add(url)
            
    return list(links_noticias)

def formatar_data(data_str):
    try:
        data = data_str.split('-')[0].strip()
        data_formatada = datetime.strptime(data, "%d/%m/%Y").strftime("%d/%m/%Y")
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

    titulo = soup.select_one("h1.g-artigo__titulo")
    titulo = titulo.get_text(strip=True) if titulo else "Título não encontrado"

    autor = soup.select_one("p[style='font-size: 0.8rem; font-weight: 700;']")
    if autor:
        autor_raw = autor.get_text(strip=True)
        autor_formatado = re.sub(r"(Reportagem|Edição)", "", autor_raw)
        autor_formatado = autor_formatado.replace(" –", ", ").replace("–", "").strip()

        autores = [nome.strip() for nome in autor_formatado.split(",") if nome.strip()]
        autor = ', '.join(autores)
    else:
        autor = "Redação Câmara"

    data = soup.select_one("p.g-artigo__data-hora")
    data_texto = "Data não encontrada"
    if data:
        data_str = data.get_text(strip=True)
        data_texto = formatar_data(data_str)

    corpo_paragrafos = soup.select("div.g-artigo__texto-principal p")
    if len(corpo_paragrafos) > 2:
        corpo_paragrafos = corpo_paragrafos[1:-1]
    else:
        corpo_paragrafos = [] 
    corpo_texto = processador_texto.formatar_corpo([p.get_text(strip=True) for p in corpo_paragrafos])

    link_texto = url 
    
    return titulo, autor, data_texto, corpo_texto, link_texto

def main():
    nome_portal = "Câmara"
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
        
        except Exception as e:
            print(f"Erro ao processar a notícia no link {link}: {e}")
            continue

    gerenciador_noticias = GerenciadorNoticias(pontuacao, abrangencia, nome_portal)
    gerenciador_noticias.salvar_noticias(noticias_para_salvar)

if __name__ == "__main__":
    main()
