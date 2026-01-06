import os

from flask import Flask, render_template, request, session, redirect, url_for, flash

from auth import auth_bp
import models  # models.py deve conter as funções usadas abaixo

app = Flask(__name__)

# Configuração segura para a chave secreta (usar variável de ambiente, padrão inseguro só para dev)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "chave_insegura_padrao_para_desenvolvimento")

app.register_blueprint(auth_bp, url_prefix="/auth")


def get_github_user_info(username):
    """
    Função inline para obter informação do GitHub (substituto dos helpers no módulo github.py).
    Usa apenas requests da lib padrão, já que dependências externas não estão disponíveis no ambiente serverless.
    Retorna dict ou None.
    """
    import urllib.request
    import json

    if not username:
        return None

    try:
        with urllib.request.urlopen(f"https://api.github.com/users/{username}") as response:
            if response.status != 200:
                return None
            return json.load(response)
    except Exception:
        return None


def get_github_user_repos(username):
    import urllib.request
    import json

    if not username:
        return []

    try:
        with urllib.request.urlopen(f"https://api.github.com/users/{username}/repos") as response:
            if response.status != 200:
                return []
            return json.load(response)
    except Exception:
        return []


def get_github_repo_commits(username, repo_name):
    import urllib.request
    import json

    if not username or not repo_name:
        return []

    try:
        with urllib.request.urlopen(f"https://api.github.com/repos/{username}/{repo_name}/commits") as response:
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

    return render_template(
        "index.html",
        user_info=user_info,
        repos=repos,
        commits=commits,
        selected_repo=selected_repo,
        error=error,
        is_favorited=is_favorited,
    )


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
    return render_template("favoritos.html", favoritos=favoritos_list)


# Adaptador para Vercel Serverless: expõe a aplicação Flask como handler WSGI
def handler(environ, start_response):
    return app(environ, start_response)
