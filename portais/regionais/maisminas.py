from bs4 import BeautifulSoup
from datetime import datetime
from config.keywords import palavras_obrigatorias, palavras_adicionais
from config.classes import VerificarPalavrasChave
from config.classes import AcessarCodigoFonte
from config.classes import GerenciadorNoticias
from config.classes import ProcessadorTextoNoticias
from config.classes import VerificarDataAtual


url = "https://jornalmaisminas.com.br/"
portal_chave = 'maisminas'


def extrair_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links_noticias = set()

    for link in soup.find_all("a", href=True):
        url = link["href"]
        if (
                url.count('-') > 3
                and url.count('/') > 2
        ):
            links_noticias.add(url)

    return list(links_noticias)


def formatar_data(data_str):
    try:
        meses = {
            "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4,
            "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
            "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12
        }
        data_str = data_str.strip()
        partes = data_str.split(" de ")

        dia = int(partes[0])
        mes_nome = partes[1].lower()
        mes = meses.get(mes_nome)
        if not mes:
            raise ValueError(f"Mês '{mes_nome}' não reconhecido.")
        ano = int(partes[2])
        data_obj = datetime(ano, mes, dia)
        data_format = data_obj.strftime("%d/%m/%Y")
        return data_format
    except (ValueError, IndexError) as e:
        print(f"Erro ao formatar data '{data_str}': {e}")
        return "Data não encontrada"


def extrair_dados_noticia(url):
    acesso = AcessarCodigoFonte(url)
    html = acesso.acessar()
    processador_texto = ProcessadorTextoNoticias(portal_chave)
    if html is None:
        print(f"Erro ao acessar a página: {url}")
        return None

    soup = BeautifulSoup(html, "html.parser")

    titulo = soup.select_one("h1.post-title.single-post-title.entry-title")
    titulo_texto = titulo.get_text(strip=True) if titulo else "Título não encontrado"

    paragrafos = soup.select("div.inner-post-entry.entry-content p")

    if paragrafos:
        textos_paragrafos = [p.get_text(separator=' ', strip=True) for p in paragrafos]
        corpo_texto = processador_texto.formatar_corpo(textos_paragrafos)
    else:
        corpo_texto = "Corpo da notícia não encontrado"

    autor = soup.select_one("span.author-post a.author-url")
    autor_texto = autor.get_text(strip=True) if autor else "Autor não encontrado"

    data = soup.select_one("time.entry-date")
    data_texto = formatar_data(data.get_text(strip=True)) if data else "Data não encontrada"

    link_texto = url

    return titulo_texto, autor_texto, data_texto, corpo_texto, link_texto


def main():
    nome_portal = "Jornal Mais Minas"
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
