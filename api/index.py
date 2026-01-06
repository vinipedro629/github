from flask import Flask, render_template, request, session, redirect, url_for, flash
import github
from auth import auth_bp
import models  # Supondo que há um models.py conforme contexto

app = Flask(__name__)
app.secret_key = 'sua_chave_supersecreta_aqui'  # Troque por uma chave forte em produção!
app.register_blueprint(auth_bp, url_prefix='/auth')

@app.route('/', methods=['GET', 'POST'])
def index():
    user_info = None
    repos = []
    commits = []
    selected_repo = None
    error = None
    is_favorited = False

    # Permitir buscar via GET também (por ex: /?username=foobar)
    if request.method == 'POST':
        username = request.form.get('username')
        repo_name = request.form.get('repo')
    else:
        username = request.args.get('username', '').strip()
        repo_name = request.args.get('repo', '').strip() if 'repo' in request.args else None

    if username:
        user_info = github.get_user_info(username)
        if user_info:
            repos = github.get_user_repos(username)
            # Se repo_name vier da query ou POST, pega os commits
            selected_repo = repo_name
            if selected_repo:
                commits = github.get_repo_commits(username, selected_repo)
        else:
            error = 'Usuário não encontrado!'
    elif request.method == 'POST':
        error = 'Por favor, informe um nome de usuário.'

    # Verifica se user_info está preenchido e usuário está logado para mostrar coração
    if user_info and 'user_id' in session:
        is_favorited = models.is_github_user_favorited(session['user_id'], user_info['login'])

    return render_template(
        'index.html',
        user_info=user_info,
        repos=repos,
        commits=commits,
        selected_repo=selected_repo,
        error=error,
        is_favorited=is_favorited
    )

@app.route('/favorite/<github_username>', methods=['POST'])
def favorite_github_user(github_username):
    if 'user_id' not in session:
        flash("Você precisa estar logado para favoritar usuários.")
        return redirect(url_for('index'))
    user_id = session['user_id']
    if models.is_github_user_favorited(user_id, github_username):
        models.remove_github_user_favorite(user_id, github_username)
        flash(f"Usuário {github_username} removido dos favoritos.")
    else:
        models.add_github_user_favorite(user_id, github_username)
        flash(f"Usuário {github_username} adicionado aos favoritos.")
    return redirect(url_for('index', username=github_username))

@app.route('/favoritos')
def favoritos():
    if 'user_id' not in session:
        flash("Você precisa estar logado para ver seus favoritos.")
        return redirect(url_for('index'))
    user_id = session['user_id']
    favoritos_list = models.list_github_favorites(user_id)
    return render_template('favoritos.html', favoritos=favoritos_list)

# Handler específico para Vercel serverless (conforme README)
def handler(environ, start_response):
    return app(environ, start_response)
