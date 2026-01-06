import sqlite3

DATABASE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_by_email(email):
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE email = ?', (email,)
    ).fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE id = ?', (user_id,)
    ).fetchone()
    conn.close()
    return user

def create_user(name, email, password_hash):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
        (name, email, password_hash)
    )
    conn.commit()
    conn.close()

# Funções de favoritos do GitHub

def add_github_user_favorite(user_id, github_username):
    """Adiciona um favorito de usuário do GitHub para o usuário app."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'INSERT OR IGNORE INTO user_github_favorites (user_id, github_username) VALUES (?, ?)',
        (user_id, github_username)
    )
    conn.commit()
    conn.close()

def remove_github_user_favorite(user_id, github_username):
    """Remove usuário do GitHub dos favoritos do usuário app."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'DELETE FROM user_github_favorites WHERE user_id = ? AND github_username = ?',
        (user_id, github_username)
    )
    conn.commit()
    conn.close()

def is_github_user_favorited(user_id, github_username):
    """Verifica se um usuário do GitHub está nos favoritos."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'SELECT 1 FROM user_github_favorites WHERE user_id = ? AND github_username = ?',
        (user_id, github_username)
    )
    result = cur.fetchone()
    conn.close()
    return result is not None

def list_github_favorites(user_id):
    """Lista todos os usernames do GitHub favoritados pelo usuário."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'SELECT github_username FROM user_github_favorites WHERE user_id = ?',
        (user_id,)
    )
    results = cur.fetchall()
    conn.close()
    return [row['github_username'] for row in results]
