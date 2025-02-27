from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from config.keywords import palavras_obrigatorias, palavras_adicionais
from config.classes import VerificarPalavrasChave
from config.classes import AcessarCodigoFonte
from config.classes import GerenciadorNoticias
from config.classes import ProcessadorTextoNoticias
from config.classes import VerificarDataAtual

portal_chave = 'diarioaco'
url = 'https://www.diariodoaco.com.br/'
dominio_principal = 'https://www.diariodoaco.com.br'

def extrair_links(html, dominio_principal):
    soup = BeautifulSoup(html, 'html.parser')
    links_noticias = set()
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        
        if href.startswith('./'):
            href = href[1:]

        full_url = urljoin(dominio_principal, href)
        
        if (
            '/noticia/' in full_url
            and full_url.count('-') > 3
            and full_url.count('/') > 3
        ):
            links_noticias.add(full_url)

    return list(links_noticias)

def formatar_data(data_texto):
    meses = {
        "janeiro,": "01",
        "fevereiro,": "02",
        "março,": "03",
        "abril,": "04",
        "maio,": "05",
        "junho,": "06",
        "julho,": "07",
        "agosto,": "08",
        "setembro,": "09",
        "outubro,": "10",
        "novembro,": "11",
        "dezembro,": "12"
    }

    data_texto = data_texto.split('|')[0].strip()
    data_texto = data_texto.replace(' de ', ' ')
    partes_data = data_texto.split()

    if len(partes_data) != 3:
        return "Data não encontrada"
    
    dia = partes_data[0].zfill(2)
    mes = meses.get(partes_data[1].lower(), "00")

    if mes == "00":
        return "Data não encontrada"

    ano = partes_data[2]
    return f"{dia}/{mes}/{ano}"

def ajustar_pontuacao(texto):
    texto_ajustado = re.sub(r'(?<=[.!?])\s*(?=\w)', ' ', texto)
    return texto_ajustado.capitalize()

def encontrar_titulo_e_remover(texto, titulo):
    titulo_normalizado = titulo.lower().strip()
    partes = texto.lower().split(titulo_normalizado)

    if len(partes) > 1:
        corpo_apos_titulo = partes[1].strip()
        corpo_apos_titulo = re.sub(r'(?<=[.!?])\s*(?=\w)', ' ', corpo_apos_titulo).capitalize()

        return corpo_apos_titulo
    else:
        return "Título não encontrado no corpo do texto."

def extrair_dados_noticia(url):
    acesso = AcessarCodigoFonte(url, usar_headers=True)
    html = acesso.acessar()
    soup = BeautifulSoup(html, "html.parser")

    titulo = soup.select_one("h2")
    autor = soup.select_one("span.credito")
    data = soup.select_one("p.text-right")
    corpo = soup.select("div.main-post.mt-30")
    link = soup.select_one("link[rel='canonical']")

    if not titulo or not corpo:
        return None

    titulo_texto = titulo.get_text(strip=True)
    autor_texto = autor.get_text(strip=True) if autor else "Redação Diário do Aço"
    data_texto = formatar_data(data.get_text(strip=True)) if data else "Data não encontrada"

    # Remove os primeiros parágrafos que podem conter a data e categoria
    corpo_texto = " ".join(p.get_text(strip=True) for p in corpo)

    # Identificar e remover a data e categoria no início do texto
    if data_texto in corpo_texto:
        corpo_texto = corpo_texto.split(data_texto, 1)[-1].strip()  # Remove tudo até a data
    if titulo_texto in corpo_texto:
        corpo_texto = corpo_texto.split(titulo_texto, 1)[-1].strip()  # Remove o título que aparece no corpo

    link_canonical = link.get("href") if link else url

    return titulo_texto, autor_texto, data_texto, corpo_texto, link_canonical

def main():
    nome_portal = "Diário do Aço"
    acesso = AcessarCodigoFonte(url, usar_headers=True)
    html = acesso.acessar()
    links_noticias = extrair_links(html, dominio_principal)
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
            contem_palavras, palavras_obrigatorias_encontradas, palavras_adicionais_encontradas = verificacao.verificar(
                titulo)

            # Se não contém as palavras no título, verificar no corpo
            if not contem_palavras:
                contem_palavras, palavras_obrigatorias_encontradas, palavras_adicionais_encontradas = verificacao.verificar(
                    corpo)

            if contem_palavras:
                noticias_para_salvar.append(
                    (dados_noticia, palavras_obrigatorias_encontradas, palavras_adicionais_encontradas))

        except Exception as e:
            print(f"Erro ao processar a notícia no link {link}: {e}")
            continue

    gerenciador_noticias = GerenciadorNoticias(pontuacao, abrangencia, nome_portal)
    gerenciador_noticias.salvar_noticias(noticias_para_salvar)


if __name__ == "__main__":
    main()
