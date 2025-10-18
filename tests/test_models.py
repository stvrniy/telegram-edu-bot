import pytest
import sqlite3
import sys
import os

# Додаємо корінь проекту до шляху Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def simple_db():
    """Проста фікстура бази даних"""
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    # Створюємо таблиці
    cursor.execute('''
    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY,
        group_name TEXT,
        full_name TEXT,
        is_admin INTEGER DEFAULT 0,
        notifications_enabled INTEGER DEFAULT 1
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        title TEXT NOT NULL,
        room TEXT,
        group_name TEXT NOT NULL
    )
    ''')
    
    # Додаємо тестові дані
    cursor.executemany(
        "INSERT INTO users VALUES (?, ?, ?, ?, ?)",
        [
            (123456789, 'КС-21', 'Іван Іванов', 0, 1),
            (987654321, 'КС-21', 'Петро Петренко', 0, 0),
        ]
    )
    
    cursor.executemany(
        "INSERT INTO events (date, time, title, room, group_name) VALUES (?, ?, ?, ?, ?)",
        [
            ('2025-09-16', '10:00', 'Математика', '301', 'КС-21'),
            ('2025-09-16', '12:00', 'Фізика', '201', 'КС-21'),
        ]
    )
    
    conn.commit()
    yield conn
    conn.close()

def test_get_events_function(simple_db):
    """Тест функції get_events з models.py"""
    import database.models as models
    
    # Тимчасово замінюємо get_db_connection
    original_get_conn = models.get_db_connection
    models.get_db_connection = lambda: simple_db
    
    try:
        # Act: викликаємо реальну функцію з models.py
        events = models.get_events('КС-21')
        
        # Assert
        assert len(events) == 2
        assert events[0][3] == 'Математика'  # title
        assert events[1][3] == 'Фізика'
        
    finally:
        models.get_db_connection = original_get_conn

def test_get_users_for_group_function(simple_db):
    """Тест функції get_users_for_group з models.py"""
    import database.models as models
    
    original_get_conn = models.get_db_connection
    models.get_db_connection = lambda: simple_db
    
    try:
        # Act: викликаємо реальну функцію
        users = models.get_users_for_group('КС-21')
        
        # Assert
        assert len(users) == 1  # Тільки один користувач з увімкненими сповіщеннями
        assert users[0][2] == 'Іван Іванов'  # full_name
        
    finally:
        models.get_db_connection = original_get_conn

def test_get_events_for_date_function(simple_db):
    """Тест функції get_events_for_date з models.py"""
    import database.models as models
    
    original_get_conn = models.get_db_connection
    models.get_db_connection = lambda: simple_db
    
    try:
        # Act: викликаємо реальну функцію
        events = models.get_events_for_date('2025-09-16')
        
        # Assert
        assert len(events) == 2
        assert all(event[1] == '2025-09-16' for event in events)
        
    finally:
        models.get_db_connection = original_get_conn