import sqlite3
import logging
from datetime import datetime
from config.settings import settings

logger = logging.getLogger(__name__)

def get_users_by_name(full_name):
    """Пошук користувачів за ім'ям (частковий збіг)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT user_id, group_name, full_name FROM users WHERE full_name LIKE ?',
        (f"%{full_name}%",)
    )
    users = cursor.fetchall()
    conn.close()
    return users


def init_db():
    """Ініціалізація бази даних"""
    conn = get_db_connection()  # ← ЗМІНИТИ ТУТ! Використовуємо get_db_connection() замість sqlite3.connect()
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        group_name TEXT,
        full_name TEXT,
        is_admin INTEGER DEFAULT 0,
        notifications_enabled INTEGER DEFAULT 1
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        title TEXT NOT NULL,
        room TEXT,
        group_name TEXT NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("База даних ініціалізована")
    
def get_db_connection():
    """Повертає підключення до бази даних"""
    db_path = settings.DATABASE_URL.replace('sqlite:///', '')
    return sqlite3.connect(db_path)

def add_user(user_id, group_name=None, is_admin=0):
    """Додає користувача"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR IGNORE INTO users (user_id, group_name, is_admin, notifications_enabled)
    VALUES (?, ?, ?, ?)
    ''', (user_id, group_name, is_admin, 1))
    conn.commit()
    conn.close()

def get_user(user_id):
    """Отримує дані користувача"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_user_group(user_id, group_name):
    """Оновлює групу користувача"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET group_name = ? WHERE user_id = ?', (group_name, user_id))
    conn.commit()
    conn.close()

def update_user_name(user_id, full_name):
    """Оновлює ім'я користувача"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET full_name = ? WHERE user_id = ?', (full_name, user_id))
    conn.commit()
    conn.close()

def toggle_notifications(user_id, enabled):
    """Перемикає сповіщення"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET notifications_enabled = ? WHERE user_id = ?', (enabled, user_id))
    conn.commit()
    conn.close()

def get_users_for_group(group_name):
    """Отримує всіх користувачів групи з увімкненими сповіщеннями"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE group_name = ? AND notifications_enabled = 1', (group_name,))
    users = cursor.fetchall()
    conn.close()
    return users

def add_event(date, time, title, room, group_name):
    """Додає подію"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR REPLACE INTO events (date, time, title, room, group_name)
    VALUES (?, ?, ?, ?, ?)
    ''', (date, time, title, room, group_name))
    conn.commit()
    conn.close()

def get_events(group_name, date=None):
    """Отримує події для групи"""
    conn = get_db_connection()
    cursor = conn.cursor()
    if date:
        cursor.execute('SELECT * FROM events WHERE group_name = ? AND date = ? ORDER BY time', (group_name, date))
    else:
        cursor.execute('SELECT * FROM events WHERE group_name = ? ORDER BY date, time', (group_name,))
    events = cursor.fetchall()
    conn.close()
    return events

def get_all_events():
    """Отримує всі події"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM events ORDER BY date, time')
    events = cursor.fetchall()
    conn.close()
    return events

def get_events_for_date(date):
    """Отримує всі події на дату для нагадувань"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM events WHERE date = ?', (date,))
    events = cursor.fetchall()
    conn.close()
    return events

def edit_event(event_id, date, time, title, room, group_name):
    """Редагує подію"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE events SET date = ?, time = ?, title = ?, room = ?, group_name = ?
    WHERE id = ?
    ''', (date, time, title, room, group_name, event_id))
    conn.commit()
    conn.close()

def delete_event(event_id):
    """Видаляє подію"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0