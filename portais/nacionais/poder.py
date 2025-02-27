from bs4 import BeautifulSoup
from config.keywords import palavras_obrigatorias, palavras_adicionais
from config.classes import VerificarPalavrasChave
from config.classes import AcessarCodigoFonte
from config.classes import GerenciadorNoticias
from config.classes import ProcessadorTextoNoticias
from config.classes import VerificarDataAtual

url = 'https://www.poder360.com.br/poder-hoje/'
portal_chave = 'poder'

def extrair_links(html):
    soup = BeautifulSoup(html, 'html.parser')
    links_noticias = set()
    
    for link in soup.find_all('a', href=True):
        url = link['href']
        if(
            url.count('-') > 4
            and url.count('/') > 3
            and '/opiniao/' not in url
            and '/poder-sportsmkt/' not in url
            and '/poder-gente/' not in url
        ):
            links_noticias.add(url)
    
    return list(links_noticias)

def formatar_data(data_str):
    meses = {
        'jan': '01',
        'fev': '02',
        'mar': '03',
        'abr': '04',
        'mai': '05',
        'jun': '06',
        'jul': '07',
        'ago': '08',
        'set': '09',
        'out': '10',
        'nov': '11',
        'dez': '12',
    }
    data_str = data_str.strip()
    data_str = data_str.split(' ')[0]
    data_str = [parte.strip() for parte in data_str.split('.')]
    dia = data_str[0]
    mes = meses.get(data_str[1])
    ano = data_str[2]
    
    return f'{dia.zfill(2)}/{mes.zfill(2)}/{ano.zfill(4)}'

def extrair_dados_noticia(url):
    acesso = AcessarCodigoFonte(url)
    html = acesso.acessar()
    processador_texto = ProcessadorTextoNoticias(portal_chave)
    if html is None:
        print(f"Erro ao acessar a página: {url}")
        return None
    
    soup = BeautifulSoup(html, "html.parser")
    
    titulo = soup.select_one("h1.inner-page-section__title.title-1")
    titulo_texto = titulo.get_text(strip=True) if titulo else "Título não encontrado"

    autor = soup.select_one("span.inner-page-section__author-link a")
    autor_texto = autor.get_text(strip=True) if autor else "Redação Poder360"
    data = soup.select_one("time.inner-page-section__date")
    if data:
        data_texto = formatar_data(data.get_text('datetime'))
    else:
        data_texto = "Data não encontrada"
        
    corpo = soup.select("div.inner-page-section__text p")
    corpo_paragrafos = [p.get_text(separator=' ', strip=True) for p in corpo]
    corpo_texto = processador_texto.formatar_corpo(corpo_paragrafos)

    link = soup.select_one("link[rel='canonical']")
    link_texto = link.get("href") if link else "Link não encontrado"

    return titulo_texto, autor_texto, data_texto, corpo_texto, link_texto

def main():
    nome_portal = "Poder 360"
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
