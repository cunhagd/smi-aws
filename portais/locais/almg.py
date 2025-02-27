from bs4 import BeautifulSoup
from urllib.parse import urljoin
from config.keywords import palavras_obrigatorias, palavras_adicionais
from datetime import datetime
from config.classes import VerificarPalavrasChave
from config.classes import AcessarCodigoFonte
from config.classes import GerenciadorNoticias
from config.classes import ProcessadorTextoNoticias
from config.classes import VerificarDataAtual

url = "https://www.almg.gov.br/"
portal_chave = 'almg'

def extrair_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links_noticias = set()
    dominio_principal = "https://www.almg.gov.br"

    for link in soup.find_all("a", href=True):
        url = link["href"]
        if '/noticias/' in url:
            full_url = urljoin(dominio_principal, url)
            links_noticias.add(full_url)
    return list(links_noticias)

def formatar_data(data_str):
    try:
        data_sem_hora = data_str.split('-')[0].strip()
        data_formatada = datetime.strptime(data_sem_hora, "%d/%m/%Y").strftime("%d/%m/%Y")
        return data_formatada
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

    titulo = soup.select_one("h1.mb-4.ls--2")
    titulo_texto = titulo.get_text(strip=True) if titulo else "Título não encontrado"
    
    autor_texto = "Redação ALMG"

    data = soup.select_one("small.mb-6.d-block.text-gray-550")
    data_texto = formatar_data(data.get_text(strip=True)) if data else "Data não encontrada"

    corpo = soup.select("div.texto-com-ancoras p")
    corpo_paragrafos = [p.get_text(strip=True) for p in corpo if p.get_text(strip=True)]
    corpo_texto = processador_texto.formatar_corpo(corpo_paragrafos)
    
    link_texto = url

    return titulo_texto, autor_texto, data_texto, corpo_texto, link_texto

def main():
    nome_portal = "ALMG"
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