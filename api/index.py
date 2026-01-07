import os

from flask import Flask, request, session, redirect, url_for, flash

from auth import auth_bp
import models  # models.py deve conter as funções usadas abaixo

app = Flask(__name__)

# Configuração segura para a chave secreta (usar variável de ambiente, padrão inseguro só para dev)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "chave_insegura_padrao_para_desenvolvimento")

app.register_blueprint(auth_bp, url_prefix="/auth")


def get_github_user_info(username):
    """
    Recupera informações de usuário do GitHub sem dependências externas.
    Retorna dict ou None.
    """
    import urllib.request
    import json

    if not username:
        return None

    url = f"https://api.github.com/users/{username}"
    try:
        with urllib.request.urlopen(url) as response:
            if response.status != 200:
                return None
            return json.load(response)
    except Exception:
        return None


def get_github_user_repos(username):
    """
    Busca os repositórios públicos de um usuário do GitHub.
    Retorna lista de dicts ou [].
    """
    import urllib.request
    import json

    if not username:
        return []

    url = f"https://api.github.com/users/{username}/repos"
    try:
        with urllib.request.urlopen(url) as response:
            if response.status != 200:
                return []
            return json.load(response)
    except Exception:
        return []


def get_github_repo_commits(username, repo_name):
    """
    Busca commits de um repositório público do GitHub.
    Retorna lista de dicts ou [].
    """
    import urllib.request
    import json

    if not username or not repo_name:
        return []

    url = f"https://api.github.com/repos/{username}/{repo_name}/commits"
    try:
        with urllib.request.urlopen(url) as response:
            if response.status != 200:
                return []
            return json.load(response)
    except Exception:
        return []


@app.route("/", methods=["GET", "POST"])
def index():
    user_info = None
    repos = []
    commits = []
    selected_repo = None
    error = None
    is_favorited = False

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        repo_name = request.form.get("repo", "").strip()
    else:
        username = request.args.get("username", "").strip()
        repo_name = request.args.get("repo", "").strip() if "repo" in request.args else None

    if username:
        user_info = get_github_user_info(username)
        if user_info:
            repos = get_github_user_repos(username)
            selected_repo = repo_name if repo_name else None
            if selected_repo:
                commits = get_github_repo_commits(username, selected_repo)
        else:
            error = "Usuário não encontrado!"
    elif request.method == "POST":
        error = "Por favor, informe um nome de usuário."

    # Exibe botão de favorito apenas se o usuário está logado e consultou um perfil válido
    if user_info and session.get("user_id"):
        is_favorited = models.is_github_user_favorited(session["user_id"], user_info.get("login"))

    # Em vez de render_template, renderize HTML diretamente (evita erro TemplateNotFound)
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <title>GitHub User Lookup</title>
        <style>
          body {{ font-family: Arial, sans-serif; padding: 2em; max-width: 700px; margin: auto; }}
          .error {{ color: red; }}
          .favorito {{ background: #f7f7aa; padding: .5em 1em; border-radius: 6px; }}
        </style>
    </head>
    <body>
        <h1>Consulta de Usuário GitHub</h1>
        <form method="post">
            <label for="username">Usuário GitHub:</label>
            <input name="username" id="username" required value="{username}">
            <button type="submit">Buscar</button>
            <br><br>
            {repos_select}
        </form>
        {error_html}
        {user_info_html}
        <hr>
        <a href="{favoritos_url}">Meus Favoritos</a>
    </body>
    </html>
    """

    # Repositórios select
    repos_select = ""
    if user_info and repos:
        repos_select += '<label for="repo">Selecionar repositório:</label>'
        repos_select += '<select name="repo" id="repo" onchange="this.form.submit()">'
        repos_select += '<option value="">--</option>'
        for repo in repos:
            selected = 'selected' if repo["name"] == (selected_repo or "") else ''
            repos_select += f'<option value="{repo["name"]}" {selected}>{repo["name"]}</option>'
        repos_select += '</select><br><br>'

    # Erros
    error_html = ""
    if error:
        error_html = f'<p class="error">{error}</p>'

    # Favorito (para usuário logado)
    favorito_btn = ""
    if user_info and session.get("user_id"):
        fav_form = f'''
        <form style="display:inline" method="post" action="{url_for('favorite_github_user', github_username=user_info['login'])}">
            <button type="submit" class="favorito">{'Remover dos favoritos' if is_favorited else 'Adicionar aos favoritos'}</button>
        </form>
        '''
        favorito_btn = fav_form

    # Exibir user_info
    user_info_html = ""
    if user_info:
        user_info_html += "<h2>Perfil</h2>"
        avatar = user_info.get("avatar_url", "")
        if avatar:
            user_info_html += f'<img src="{avatar}" alt="avatar" width="80"><br>'
        user_info_html += f'<b>Login:</b> {user_info.get("login", "")}<br>'
        user_info_html += f'<b>Nome:</b> {user_info.get("name","")}<br>' if user_info.get("name") else ""
        user_info_html += f'<b>Bio:</b> {user_info.get("bio","")}<br>' if user_info.get("bio") else ""
        user_info_html += f'<b>Repositórios públicos:</b> {user_info.get("public_repos","")}'
        user_info_html += "<br>" + favorito_btn + "<br>"
        # Exibir repositórios
        if repos:
            user_info_html += "<h3>Repositórios</h3>"
            user_info_html += "<ul>"
            for repo in repos:
                repo_url = repo.get("html_url", "")
                name = repo.get("name","")
                li_selected = ' style="font-weight:bold;"' if selected_repo == name else ""
                user_info_html += f'<li{li_selected}><a href="{repo_url}" target="_blank">{name}</a></li>'
            user_info_html += "</ul>"
        # Exibir commits do repo selecionado
        if selected_repo and commits:
            user_info_html += f"<h3>Commits do repositório: {selected_repo}</h3>"
            user_info_html += "<ul>"
            for commit in commits[:10]:
                msg = commit.get("commit", {}).get("message", "")
                sha = commit.get("sha", "")[:7]
                author = commit.get("commit", {}).get("author",{}).get("name","")
                user_info_html += f"<li><b>{sha}</b> {msg} <i>(por {author})</i></li>"
            user_info_html += "</ul>"
        elif selected_repo and not commits:
            user_info_html += "<p>Nenhum commit encontrado ou não foi possível obter commits.</p>"

    favoritos_url = url_for('favoritos')
    # Use SafeDict to avoid KeyError with curly braces from CSS
    class SafeDict(dict):
        def __missing__(self, key):
            return '{' + key + '}'
    return html.format_map(SafeDict(
        username=(username or ""),
        repos_select=repos_select,
        error_html=error_html,
        user_info_html=user_info_html,
        favoritos_url=favoritos_url
    ))


@app.route("/favorite/<github_username>", methods=["POST"])
def favorite_github_user(github_username):
    if "user_id" not in session:
        flash("Você precisa estar logado para favoritar usuários.")
        return redirect(url_for("index"))
    user_id = session["user_id"]
    if models.is_github_user_favorited(user_id, github_username):
        models.remove_github_user_favorite(user_id, github_username)
        flash(f"Usuário {github_username} removido dos favoritos.")
    else:
        models.add_github_user_favorite(user_id, github_username)
        flash(f"Usuário {github_username} adicionado aos favoritos.")
    return redirect(url_for("index", username=github_username))


@app.route("/favoritos")
def favoritos():
    if "user_id" not in session:
        flash("Você precisa estar logado para ver seus favoritos.")
        return redirect(url_for("index"))
    user_id = session["user_id"]
    favoritos_list = models.list_github_favorites(user_id)

    # Renderiza diretamente os favoritos para evitar dependência de template externo
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <title>Favoritos do GitHub</title>
        <style>body {{ font-family: Arial, sans-serif; padding: 2em; max-width: 700px; margin: auto; }}</style>
    </head>
    <body>
      <h1>Favoritos</h1>
      {mensagem}
      <ul>
        {favoritos_li}
      </ul>
      <a href="{index_url}">Voltar</a>
    </body>
    </html>
    """
    if not favoritos_list:
        mensagem = "<i>Nenhum favorito ainda.</i>"
    else:
        mensagem = f"<p>Total: {len(favoritos_list)}</p>"
    favoritos_li = ""
    for fav in favoritos_list:
        # fav pode ser str (login) ou dict - depende da model
        if isinstance(fav, dict) and "github_username" in fav:
            login = fav["github_username"]
        else:
            login = str(fav)
        favoritos_li += f'<li><a href="{url_for("index")}?username={login}">{login}</a></li>'
    class SafeDict(dict):
        def __missing__(self, key):
            return '{' + key + '}'
    return html.format_map(SafeDict(
        mensagem=mensagem,
        favoritos_li=favoritos_li,
        index_url=url_for("index")
    ))


# ATENÇÃO: Vercel/Python Runtime espera o objeto WSGI "app" neste arquivo.
# Não defina handler() ou funções equivalentes que retornem o app (isso gera TypeError esperados em logs serverless).
# Apenas exporte o objeto Flask "app".
