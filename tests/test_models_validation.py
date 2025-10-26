# tests/test_models_validation.py
import pytest
from datetime import date, timedelta

# Припускаємо, що в database/models.py є такі функції:
# - get_db_connection() -> sqlite3.Connection
# - add_event(date, time, title, room, group_name) -> int (id)
# - get_events_for_date(date) -> list[tuple] або list[dict]
# - get_users_for_group(group_name) -> list[...]
#
# Якщо імена інші — напишу під твої після того, як ти надаси їх (див. розділ "Що мені від тебе потрібно").

def test_add_event_rejects_past_date(monkeypatch, simple_db):
    from database import models

    # підміняємо з’єднання на тимчасову БД зі схеми з conftest.py
    monkeypatch.setattr(models, "get_db_connection", lambda: simple_db)

    past = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    with pytest.raises((ValueError, AssertionError, RuntimeError)):
        models.add_event(date=past, time="10:00", title="Математика", room="101", group_name="КС-21")

def test_add_event_rejects_empty_title(monkeypatch, simple_db):
    from database import models
    monkeypatch.setattr(models, "get_db_connection", lambda: simple_db)

    today = date.today().strftime("%Y-%m-%d")
    with pytest.raises((ValueError, AssertionError)):
        models.add_event(date=today, time="10:00", title="", room="101", group_name="КС-21")

def test_add_event_inserts_and_is_queryable(monkeypatch, simple_db):
    from database import models
    monkeypatch.setattr(models, "get_db_connection", lambda: simple_db)

    today = date.today().strftime("%Y-%m-%d")
    new_id = models.add_event(date=today, time="09:00", title="Прога", room="101", group_name="КС-21")
    assert isinstance(new_id, int)

    rows = models.get_events_for_date(today)
    # не покладаємось на порядок — звіримо за множиною назв
    titles = {r[3] if isinstance(r, tuple) else r["title"] for r in rows}
    assert "Прога" in titles

def test_get_users_for_group_handles_empty(monkeypatch, simple_db):
    from database import models
    monkeypatch.setattr(models, "get_db_connection", lambda: simple_db)

    users = models.get_users_for_group("НЕІСНУЮЧА")
    assert users == [] or len(users) == 0
