
import sqlite3
from pathlib import Path
import bcrypt

DB_PATH = Path(__file__).parent / "system.db"

def get_conn():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        fullname TEXT,
        email TEXT
    )''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS metas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendedor TEXT NOT NULL,
        meta_min REAL,
        meta_100 REAL,
        gratificacao_100 REAL,
        bonus_pct REAL
    )''')
    conn.commit()
    # default admin user
    cur.execute("SELECT * FROM users WHERE username = ?", ('admin',))
    if cur.fetchone() is None:
        pw = 'admin'.encode('utf-8')
        hashed = bcrypt.hashpw(pw, bcrypt.gensalt()).decode('utf-8')
        cur.execute("INSERT INTO users (username, password_hash, role, fullname, email) VALUES (?,?,?,?,?)",
                    ('admin', hashed, 'ADMIN', 'Administrador', 'admin@example.com'))
        conn.commit()
    conn.close()

def create_user(username, password, role='USER', fullname=None, email=None):
    conn = get_conn()
    cur = conn.cursor()
    pw = password.encode('utf-8')
    hashed = bcrypt.hashpw(pw, bcrypt.gensalt()).decode('utf-8')
    try:
        cur.execute("INSERT INTO users (username, password_hash, role, fullname, email) VALUES (?,?,?,?,?)",
                    (username, hashed, role.upper(), fullname, email))
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def authenticate(username, password):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        return False, None
    stored = row['password_hash'].encode('utf-8')
    try:
        ok = bcrypt.checkpw(password.encode('utf-8'), stored)
    except Exception:
        ok = False
    if ok:
        return True, {'id': row['id'], 'username': row['username'], 'role': row['role'], 'fullname': row['fullname'], 'email': row['email']}
    return False, None

def list_users():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, username, role, fullname, email FROM users ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_user(username):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def change_password(username, new_password):
    conn = get_conn()
    cur = conn.cursor()
    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cur.execute("UPDATE users SET password_hash = ? WHERE username = ?", (hashed, username))
    conn.commit()
    conn.close()

def set_meta(vendedor, meta_min=None, meta_100=None, grat_100=None, bonus_pct=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM metas WHERE vendedor = ?", (vendedor,))
    r = cur.fetchone()
    if r:
        cur.execute("UPDATE metas SET meta_min = COALESCE(?,meta_min), meta_100 = COALESCE(?,meta_100), gratificacao_100 = COALESCE(?,gratificacao_100), bonus_pct = COALESCE(?,bonus_pct) WHERE vendedor = ?",
                    (meta_min, meta_100, grat_100, bonus_pct, vendedor))
    else:
        cur.execute("INSERT INTO metas (vendedor, meta_min, meta_100, gratificacao_100, bonus_pct) VALUES (?,?,?,?,?)",
                    (vendedor, meta_min, meta_100, grat_100, bonus_pct))
    conn.commit()
    conn.close()

def get_meta(vendedor):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM metas WHERE vendedor = ?", (vendedor,))
    r = cur.fetchone()
    conn.close()
    if r:
        return dict(r)
    return None

def list_metas():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM metas ORDER BY vendedor")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]
