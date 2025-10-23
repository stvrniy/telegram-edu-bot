import pytest
import sqlite3
import sys
import os

# Додаємо корінь проекту до шляху Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def simple_db():
    """Проста фікстура бази даних для ізоляції тестів"""
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
            (123456789, 'КС-21', 'Іван Іванов', 0, 1),    # Користувач з увімкненими сповіщеннями
            (987654321, 'КС-21', 'Петро Петренко', 0, 0), # Користувач з вимкненими сповіщеннями
            (555555555, 'ІН-23', 'Марія Сидоренко', 0, 1), # Користувач іншої групи
        ]
    )
    
    cursor.executemany(
        "INSERT INTO events (date, time, title, room, group_name) VALUES (?, ?, ?, ?, ?)",
        [
            ('2025-09-16', '10:00', 'Математика', '301', 'КС-21'),
            ('2025-09-16', '12:00', 'Фізика', '201', 'КС-21'),
            ('2025-09-17', '09:00', 'Програмування', '101', 'ІН-23'),
        ]
    )
    
    conn.commit()
    yield conn
    conn.close()

def test_get_events_function(simple_db):
    """Тест вимоги R1.1 - отримання розкладу занять для групи"""
    import database.models as models
    
    # Тимчасово замінюємо get_db_connection
    original_get_conn = models.get_db_connection
    models.get_db_connection = lambda: simple_db
    
    try:
        # Act: викликаємо реальну функцію з models.py
        events = models.get_events('КС-21')
        
        # Assert: перевіряємо, що система коректно повертає розклад
        assert len(events) == 2  # Має бути 2 події для групи КС-21
        assert events[0][3] == 'Математика'  # title першої події
        assert events[1][3] == 'Фізика'      # title другої події
        
        # Додаткова перевірка структури даних
        for event in events:
            assert len(event) == 6  # id, date, time, title, room, group_name
            assert event[5] == 'КС-21'  # Всі події мають належати групі КС-21
        
    finally:
        models.get_db_connection = original_get_conn

def test_get_users_for_group_function(simple_db):
    """Тест вимоги R1.2 - отримання користувачів для сповіщень"""
    import database.models as models
    
    original_get_conn = models.get_db_connection
    models.get_db_connection = lambda: simple_db
    
    try:
        # Act: викликаємо реальну функцію
        users = models.get_users_for_group('КС-21')
        
        # Assert: перевіряємо, що система знаходить користувачів з увімкненими сповіщеннями
        assert len(users) == 1  # Тільки один користувач з увімкненими сповіщеннями
        assert users[0][2] == 'Іван Іванов'  # full_name
        assert users[0][4] == 1  # notifications_enabled = True
        
        # Перевіряємо, що користувач з вимкненими сповіщеннями не повертається
        user_ids = [user[0] for user in users]
        assert 987654321 not in user_ids  # Петро Петренко має вимкнені сповіщення
        
    finally:
        models.get_db_connection = original_get_conn

def test_get_events_for_date_function(simple_db):
    """Тест вимоги R1.1 - отримання розкладу на конкретну дату"""
    import database.models as models
    
    original_get_conn = models.get_db_connection
    models.get_db_connection = lambda: simple_db
    
    try:
        # Act: викликаємо реальну функцію
        events = models.get_events_for_date('2025-09-16')
        
        # Assert: перевіряємо, що система коректно повертає події на дату
        assert len(events) == 2  # Має бути 2 події на 2025-09-16
        assert all(event[1] == '2025-09-16' for event in events)  # Всі події мають потрібну дату
        
        # Перевіряємо, що подія з іншої дати не повертається
        event_dates = [event[1] for event in events]
        assert '2025-09-17' not in event_dates  # Подія з 17 вересня не має бути в результаті
        
    finally:
        models.get_db_connection = original_get_conn

def test_get_events_with_date_filter(simple_db):
    """Тест вимоги R1.1 - отримання розкладу для групи з фільтром по даті"""
    import database.models as models
    
    original_get_conn = models.get_db_connection
    models.get_db_connection = lambda: simple_db
    
    try:
        # Act: викликаємо функцію з фільтром по даті
        events = models.get_events('КС-21', '2025-09-16')
        
        # Assert: перевіряємо коректність фільтрації
        assert len(events) == 2  # Всі 2 події КС-21 на цю дату
        assert all(event[1] == '2025-09-16' for event in events)
        assert all(event[5] == 'КС-21' for event in events)
        
    finally:
        models.get_db_connection = original_get_conn