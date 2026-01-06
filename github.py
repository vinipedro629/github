import requests

def get_user_repos(username):
    """
    Obtém a lista de repositórios públicos de um usuário do GitHub, ordenados do mais recente para o mais antigo.

    Parâmetros:
        username (str): Nome do usuário do GitHub.

    Retorno:
        list: Lista de dicionários representando os repositórios ou None se não foi possível conectar.
    """
    url = f'https://api.github.com/users/{username}/repos?per_page=100'
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            repos = response.json()
            repos.sort(key=lambda repo: repo.get('created_at', ''), reverse=True)
            return repos
        elif response.status_code == 404:
            return []
        else:
            return []
    except requests.ConnectionError:
        # Não foi possível conectar ao servidor GitHub (NS_ERROR_CONNECTION_REFUSED, etc)
        return None  # O app Python pode diferenciar e exibir mensagem "Não foi possível conectar"
    except requests.RequestException:
        return None

def get_repo_commits(owner, repo):
    """
    Retorna a lista de commits de um repositório público do GitHub.

    Parâmetros:
        owner (str): Dono do repositório.
        repo (str): Nome do repositório.

    Retorno:
        list: Lista de dicionários de commits, ou None caso não foi possível conectar.
    """
    url = f'https://api.github.com/repos/{owner}/{repo}/commits'
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return []
        else:
            return []
    except requests.ConnectionError:
        return None
    except requests.RequestException:
        return None

def get_user_info(username):
    """
    Obtém informações básicas de perfil do usuário GitHub.

    Parâmetros:
        username (str): Nome do usuário do GitHub.

    Retorno:
        dict: Dicionário com as informações do usuário, ou None se não encontrado ou não foi possível conectar.
    """
    url = f'https://api.github.com/users/{username}'
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None
        else:
            return None
    except requests.ConnectionError:
        return None
    except requests.RequestException:
        return None
