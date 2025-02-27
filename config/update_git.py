# update_repo.py
# -*- coding: utf-8 -*-

import subprocess
from pathlib import Path
import sys

def sync_with_remote(repo_path):
    """
    Garante que o repositório local esteja sincronizado com o remoto,
    evitando conflitos antes de commit/push.
    Utiliza 'git pull --rebase --autostash' para automaticamente guardar
    e reaplicar mudanças locais não commitadas.
    """
    try:
        # 1. Faz pull com rebase e autostash
        subprocess.run(
            ["git", "-C", repo_path, "pull", "--rebase", "--autostash"],
            check=True
        )
        print("Repositório sincronizado com o remoto (pull --rebase com autostash).")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Erro ao sincronizar com remoto. Possível conflito a resolver. Detalhes: {e}"
        )

def git_commit_and_push(repo_path, commit_message="Atualização automática do repositório"):
    """
    Faz commit e push das alterações para o repositório do GitHub.
    """
    try:
        # Sincroniza primeiro para evitar conflitos:
        sync_with_remote(repo_path)

        # Agora adiciona os arquivos e faz o commit/push
        subprocess.run(["git", "-C", repo_path, "add", "."], check=True)
        subprocess.run(
            ["git", "-C", repo_path, "commit", "-m", commit_message],
            check=True,
        )
        subprocess.run(["git", "-C", repo_path, "push"], check=True)
        print("Alterações commitadas e enviadas para o GitHub.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Erro ao fazer commit e push: {e}")

def main():
    repo_path = r"C:\Users\m1603994\PycharmProjects\scrapgov-"

    print("Iniciando script de atualização do repositório Git.")

    try:
        # Sincroniza e envia as alterações
        git_commit_and_push(repo_path)

    except Exception as ex:
        print("Não foi possível atualizar o repositório corretamente.")
        print(f"Detalhes do erro: {ex}")
        sys.exit(1)  # Sai com status de erro

    print("Script de atualização do repositório finalizado.")
    sys.exit(0)  # Sai com sucesso

if __name__ == "__main__":
    main()