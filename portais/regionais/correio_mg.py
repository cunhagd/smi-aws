from bs4 import BeautifulSoup
from datetime import datetime
from config.keywords import palavras_obrigatorias, palavras_adicionais
from config.classes import AcessarCodigoFonte
from config.classes import ProcessadorTextoNoticias
from config.classes import VerificarPalavrasChave
from config.classes import GerenciadorNoticias
from config.classes import VerificarDataAtual

url = "https://correiodeminas.com.br/"
portal_chave = 'correio_mg'

def extrair_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links_noticias = set()
    ano_atual = datetime.now().year
    mes_atual = datetime.now().month
    dia_atual = datetime.now().day
    mes_atual_formatado = f"{mes_atual:02}"
    dia_atual_formatado = f"{dia_atual:02}"
    
    for link in soup.find_all('a', href=True):
        url = link["href"]

        if (
            f"/{ano_atual}/{mes_atual_formatado}/{dia_atual_formatado}/" in url
            and url.count('-') > 1
        ):
            links_noticias.add(url)

    return list(links_noticias)

def formatar_data(data_str):
    meses = {
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4,
        'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
        'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
    }
    try:
        data_str = data_str.lower()
        partes = data_str.split(' ')
        dia = int(partes[0])
        mes = meses[partes[2]]
        ano = int(partes[4])
        data_obj = datetime(ano, mes, dia)
        return data_obj.strftime("%d/%m/%Y")
    
    except (ValueError, KeyError, IndexError):
        return "Data não encontrada"

def extrair_dados_noticia(url):
    acesso = AcessarCodigoFonte(url)
    html = acesso.acessar()
    processador_texto = ProcessadorTextoNoticias(portal_chave)
    
    soup = BeautifulSoup(html, "html.parser")

    titulo = soup.select_one("div.elementor-widget-container h1")
    titulo_texto = titulo.get_text(strip=True) if titulo else "Título não encontrado"

    corpo = soup.select("div.elementor-widget-container p")
    corpo_paragrafos = corpo[:-1]
    corpo_texto = processador_texto.formatar_corpo([p.get_text(strip=True) for p in corpo_paragrafos])

    autor = corpo[-1] if corpo else None
    if autor:
        autor_texto = autor.get_text(strip=True)
        if autor_texto.lower().startswith("informações"):
            autor_texto = autor_texto[len("Informações"):].strip()
        autor_texto = autor_texto.split(",")[0]
    else:
        autor_texto = "Redação Correio (MG)"

    data = soup.select_one("div.elementor-widget-container time")
    data_texto = formatar_data(data.get_text(strip=True)) if data else "Data não encontrada"

    link = soup.select_one("link[rel='canonical']")
    link_texto = link.get("href") if link else "Link não encontrado"

    return titulo_texto, autor_texto, data_texto, corpo_texto, link_texto

def main():
    nome_portal = "Correio (MG)"
    acesso = AcessarCodigoFonte(url)
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
