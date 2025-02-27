import os
import importlib
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def importar_portais(base_diretorio, categoria="nacionais"):
    """
    Importa dinamicamente todos os módulos Python dentro de `portais/nacionais`.
    """
    portais = []
    # Define o caminho específico para portais/nacionais a partir do base_diretorio
    diretorio_categoria = os.path.join(base_diretorio, "portais", categoria)
    
    # Debug: Mostra o caminho que está tentando acessar
    print(f"Tentando acessar o diretório: {diretorio_categoria}")
    
    # Verifica se o diretório existe
    if not os.path.exists(diretorio_categoria):
        print(f"Diretório {diretorio_categoria} não encontrado.")
        return portais
    
    # Percorre apenas o diretório portais/nacionais
    for root, _, files in os.walk(diretorio_categoria):
        for arquivo in files:
            if arquivo.endswith(".py") and arquivo != "__init__.py":
                # Calcula o caminho relativo a partir de portais/
                caminho_relativo = os.path.relpath(root, os.path.join(base_diretorio, "portais"))
                # Remove a categoria do início do caminho relativo, se presente
                nome_pasta = caminho_relativo.replace(os.sep, ".").replace(categoria, "").strip(".")
                nome_portal = arquivo[:-3]
                # Monta o caminho de importação correto
                if nome_pasta:
                    caminho_import = f"portais.{categoria}.{nome_pasta}.{nome_portal}"
                else:
                    caminho_import = f"portais.{categoria}.{nome_portal}"
                try:
                    modulo = importlib.import_module(caminho_import)
                    portais.append(modulo)
                    print(f"Importado com sucesso: {caminho_import}")
                except ModuleNotFoundError as e:
                    print(f"Erro ao importar {caminho_import}: {e}")
                except Exception as e:
                    print(f"Erro inesperado ao importar {caminho_import}: {e}")
    return portais

def executar_portal(portal):
    """
    Função auxiliar para executar um portal individualmente.
    Retorna um dicionário com os resultados do portal.
    """
    try:
        if hasattr(portal, "main"):
            portal.main()
            noticias_salvas = getattr(portal, 'noticias_salvas', 0)
            noticias_mapeadas = getattr(portal, 'noticias_mapeadas', 0)
            return {
                "nome": portal.__name__,
                "noticias_salvas": noticias_salvas,
                "noticias_mapeadas": noticias_mapeadas,
                "erro": None
            }
        else:
            return {
                "nome": portal.__name__,
                "noticias_salvas": 0,
                "noticias_mapeadas": 0,
                "erro": "Sem função 'main'"
            }
    except Exception as e:
        return {
            "nome": portal.__name__,
            "noticias_salvas": 0,
            "noticias_mapeadas": 0,
            "erro": str(e)
        }

def main():
    """
    Função principal que executa a raspagem de notícias nacionais.
    """
    try:
        # Define o base_diretorio como o diretório onde o script está
        base_diretorio = os.path.dirname(os.path.abspath(__file__))
        print(f"Base diretório: {base_diretorio}")
        
        # Importa os portais da categoria "nacionais"
        portais = importar_portais(base_diretorio, "nacionais")
        
        total_noticias_salvas = 0
        total_noticias_mapeadas = 0
        portais_com_erro = []
        total_portais = len(portais)
        inicio_tempo = time.time()

        # Executa os portais em paralelo
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(executar_portal, portal): portal for portal in portais}
            for future in as_completed(futures):
                resultado = future.result()
                if resultado["erro"]:
                    portais_com_erro.append(resultado["nome"])
                total_noticias_salvas += resultado["noticias_salvas"]
                total_noticias_mapeadas += resultado["noticias_mapeadas"]

        fim_tempo = time.time()
        duracao_total = fim_tempo - inicio_tempo

        # Relatório simples impresso no console (para logs no Lambda, usa CloudWatch)
        relatorio = f"""
        Relatório de Execução (Nacionais):
        ---------------------------------
        Total de módulos analisados: {total_portais}
        Módulos com erro: {', '.join(portais_com_erro) if portais_com_erro else 'Nenhum'}
        Total de notícias salvas: {total_noticias_salvas}
        Total de notícias mapeadas: {total_noticias_mapeadas}
        Duração total da raspagem: {duracao_total:.2f} segundos
        """
        print(relatorio)

    except Exception as e:
        print(f"Erro durante a execução da main_nacional: {e}")

if __name__ == "__main__":
    main()