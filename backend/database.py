import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'keybox.db')

def init_db():
    """Initialise la base de donnees"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Table des logs
    c.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            room TEXT NOT NULL,
            state TEXT NOT NULL,
            key_uid TEXT,
            key_name TEXT,
            key_valid INTEGER,
            message TEXT,
            is_swap INTEGER DEFAULT 0,
            is_multi INTEGER DEFAULT 0
        )
    ''')

    # Table des etats actuels des salles
    c.execute('''
        CREATE TABLE IF NOT EXISTS room_states (
            room TEXT PRIMARY KEY,
            state TEXT NOT NULL,
            key_uid TEXT,
            key_name TEXT,
            key_valid INTEGER,
            last_update TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("[DB] Base de donnees initialisee")

def add_log(room, state, key_uid, key_name, key_valid, message, is_swap=False, is_multi=False):
    """Ajoute un log"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    c.execute('''
        INSERT INTO logs (timestamp, room, state, key_uid, key_name, key_valid, message, is_swap, is_multi)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, room, state, key_uid, key_name, 1 if key_valid else 0, message, 1 if is_swap else 0, 1 if is_multi else 0))

    conn.commit()
    conn.close()

def update_room_state(room, state, key_uid, key_name, key_valid):
    """Met a jour l'etat d'une salle"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    c.execute('''
        INSERT OR REPLACE INTO room_states (room, state, key_uid, key_name, key_valid, last_update)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (room, state, key_uid, key_name, 1 if key_valid else 0, timestamp))

    conn.commit()
    conn.close()

def get_logs(limit=100, offset=0, filter_type=None):
    """Recupere les logs"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    query = 'SELECT * FROM logs'
    params = []

    if filter_type:
        if filter_type == 'in':
            query += ' WHERE state = "IN" AND is_swap = 0'
        elif filter_type == 'out':
            query += ' WHERE state = "OUT"'
        elif filter_type == 'swap':
            query += ' WHERE is_swap = 1'
        elif filter_type == 'alert':
            query += ' WHERE is_swap = 1 OR is_multi = 1'

    query += ' ORDER BY id DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])

    c.execute(query, params)
    rows = c.fetchall()
    conn.close()

    return [dict(row) for row in rows]

def get_stats():
    """Recupere les statistiques"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('SELECT COUNT(*) FROM logs WHERE state = "IN" AND is_swap = 0')
    count_in = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM logs WHERE state = "OUT"')
    count_out = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM logs WHERE is_swap = 1 OR is_multi = 1')
    count_alert = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM logs')
    total = c.fetchone()[0]

    conn.close()

    return {'in': count_in, 'out': count_out, 'alert': count_alert, 'total': total}

def get_room_states():
    """Recupere l'etat actuel de toutes les salles"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute('SELECT * FROM room_states')
    rows = c.fetchall()
    conn.close()

    return {row['room']: dict(row) for row in rows}

def clear_logs():
    """Efface tous les logs"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM logs')
    conn.commit()
    conn.close()

# Init au chargement
init_db()
