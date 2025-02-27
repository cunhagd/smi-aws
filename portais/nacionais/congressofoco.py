from bs4 import BeautifulSoup
from config.keywords import palavras_obrigatorias, palavras_adicionais
from config.classes import AcessarCodigoFonte
from config.classes import ProcessadorTextoNoticias
from config.classes import VerificarPalavrasChave
from config.classes import GerenciadorNoticias
from config.classes import VerificarDataAtual

url = "https://congressoemfoco.uol.com.br/"
portal_chave = 'congressofoco'

def extrair_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links_noticias = set()

    for link in soup.find_all("a", href=True):
        url = link["href"]
        if (
            "/area/" in url
            and url.count('/') > 5
            and url.count('-') > 3
        ):
            links_noticias.add(url)
            
    return list(links_noticias)

def formatar_data(data_str):
    try:
        partes_data = [parte for parte in data_str.split() if parte.count('.') == 2]
        if partes_data:
            data_formatada = partes_data[0].replace('.', '/')
            return data_formatada
        else:
            raise ValueError("Formato de data não encontrado")
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

    titulo = soup.select_one("div.font-xxxxl.font-black.font-work-sans.font-lh-1.color-black.text-uppercase.text-decoration-none")
    if not titulo:
        titulo = soup.select_one("h1.font-xxxxl.font-black.font-work-sans.font-lh-1.color-black.text-decoration-none")
    titulo_texto = titulo.get_text(strip=True) if titulo else "Título não encontrado"

    autor = soup.select_one("p.color-gray.font-sm.font-medium.text-uppercase.text-decoration-none.mt-1.mb-0 a[rel='author']")
    autor_texto = autor.get_text(strip=True) if autor else "Redação Congresso em Foco"

    data = soup.select_one("p.font-xs.color-gray.lh-11.my-1")
    data_texto = "Data não encontrada"
    if data:
        data_str = data.get_text(strip=True).split()[0]  
        data_texto = formatar_data(data_str)  

    corpo = soup.select("div.post-article p")
    corpo_paragrafos = [p.get_text(strip=True) for p in corpo]
    corpo_texto = processador_texto.formatar_corpo(corpo_paragrafos)

    link_texto = url 

    return titulo_texto, autor_texto, data_texto, corpo_texto, link_texto

def main():
    nome_portal = "Congresso em Foco"
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
