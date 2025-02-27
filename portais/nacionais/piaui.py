from bs4 import BeautifulSoup
from config.keywords import palavras_obrigatorias, palavras_adicionais
from config.classes import VerificarPalavrasChave
from config.classes import AcessarCodigoFonte
from config.classes import GerenciadorNoticias
from config.classes import ProcessadorTextoNoticias
from config.classes import VerificarDataAtual

url = "https://piaui.folha.uol.com.br/"
portal_chave = 'piaui'

def extrair_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links_noticias = set()

    dominio_principal = "https://piaui.folha.uol.com.br"

    for link in soup.find_all("a", href=True):
        url = link["href"]
        if (
            dominio_principal in url  
            and url.count('-') > 3 
            and url.count('/') > 3 
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
        'dez': '12'
    }
    try:
        data_sem_hora = data_str.split(',')[0].strip() 
        dia, mes_abreviado, ano = data_sem_hora.split()  
        mes_numerico = meses.get(mes_abreviado.lower())
        if mes_numerico:
            data_formatada = f"{dia.zfill(2)}/{mes_numerico}/{ano}" 
            return data_formatada
        else:
            return "Mês inválido"
    except ValueError:
        return "Data não encontrada"
    
def extrair_dados_noticia(url):
    acesso = AcessarCodigoFonte(url, usar_headers=True)
    html = acesso.acessar()
    processador_texto = ProcessadorTextoNoticias(portal_chave)
    if html is None:
        print(f"Erro ao acessar a página: {url}")
        return None

    soup = BeautifulSoup(html, "html.parser")

    titulo = soup.select_one("h1.noticia__header--title")  
    autor = soup.select_one("span.noticia__header--autor--nome") 
    
    data_element = soup.select_one("span.noticia__header--autor--data span.bold")
    data_texto = data_element.get_text(strip=True) if data_element else "Data não encontrada"

    data_texto = formatar_data(data_texto)

    corpo = soup.select("div.noticia__main--materia p")
    link = soup.select_one("link[rel='canonical']")

    titulo_texto = titulo.get_text(strip=True) if titulo else "Título não encontrado"
    
    if autor:
        autor_texto = autor.get_text(strip=True)
        if autor_texto.lower().startswith("por"):
            autor_texto = autor_texto[3:].strip()
        autor_texto = autor_texto.split(",")[0]
    else:
        autor_texto = "Redação Revista Piauí"

    corpo_paragrafos = []
    for i, p in enumerate(corpo):
        paragrafo_texto = p.get_text(strip=True)
        if i == 0 and "Publicidade" in paragrafo_texto:
            print("Ignorando o primeiro parágrafo contendo 'Publicidade'.")
            continue
        corpo_paragrafos.append(paragrafo_texto)
    corpo_texto = processador_texto.formatar_corpo(corpo_paragrafos)

    link_texto = link.get("href") if link else "Link não encontrado"

    return titulo_texto, autor_texto, data_texto, corpo_texto, link_texto

def main():
    nome_portal = "Piauí"
    acesso = AcessarCodigoFonte(url, usar_headers=True)
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
