"""
github_activity.py

Script utilitário para consumir a API pública do GitHub
e exibir atividades recentes (eventos públicos) de um usuário.

Para integração com Flask, considere mover funções reutilizáveis
para github.py e importar no app principal. Veja estrutura sugerida em a.txt.
"""

import sys
import urllib.request
import ssl
import json
from datetime import datetime

def get_github_activity(username):
    """
    Busca eventos públicos recentes de um usuário do GitHub.
    Retorna uma lista de dicionários com informações formatadas para cada evento,
    ou levanta uma exceção adequada se houver erro de acesso.
    """
    api_url = f"https://api.github.com/users/{username}/events"

    # Ignora verificação SSL para compatibilidade ampla (não recomendado em produção)
    ctx = ssl._create_unverified_context()

    req = urllib.request.Request(api_url, headers={"User-Agent": "python-urllib"})

    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            if resp.status != 200:
                raise Exception(f"Erro ao buscar dados: {resp.status}")
            content = resp.read().decode()
            if not content.strip():
                return []
            data = json.loads(content)
            if not data:
                return []
            activities = []
            for event in data:
                tipo = event.get("type", "Evento")
                repo = event.get("repo", {}).get("name", "repositório desconhecido")
                time_iso = event.get("created_at")
                if time_iso:
                    try:
                        dt = datetime.strptime(time_iso, "%Y-%m-%dT%H:%M:%SZ")
                        time_br = dt.strftime("%d/%m/%Y %H:%M:%S")
                    except Exception:
                        time_br = time_iso
                else:
                    time_br = "Data desconhecida"

                desc = ""
                if tipo == "PushEvent":
                    commits = len(event.get("payload", {}).get("commits", []))
                    desc = f"Pushed {commits} commits to {repo}"
                elif tipo == "IssuesEvent":
                    action = event.get("payload", {}).get("action", "realizou uma ação")
                    desc = f"{action.capitalize()} uma issue em {repo}"
                elif tipo == "WatchEvent":
                    desc = f"Starred {repo}"
                else:
                    desc = f"{tipo} em {repo}"

                activities.append({
                    "tipo": tipo,
                    "repositorio": repo,
                    "datahora": time_br,
                    "descricao": desc,
                })
            return activities
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise ValueError("Usuário não encontrado.")
        raise Exception(f"Erro da API: {e}") from e
    except Exception as e:
        raise Exception(f"Ocorreu um erro: {e}") from e


def print_github_activity(username):
    """
    Função utilitária para rodar stand-alone. Imprime as atividades recentes do usuário.
    """
    try:
        atividades = get_github_activity(username)
        if not atividades:
            print("Nenhuma atividade encontrada.")
            return
        for evento in atividades:
            print(f"[{evento['datahora']}] {evento['descricao']}")
    except ValueError as ve:
        print(str(ve))
    except Exception as exc:
        print(str(exc))


if __name__ == "__main__":
    # Permite passar usuário por linha de comando para testar facilmente, ou usa valor padrão
    usuario = sys.argv[1] if len(sys.argv) > 1 else "vinipedro629"
    print_github_activity(usuario)
