# load/server.py
from config.settings import settings
import os, sys, sqlite3
from typing import Optional
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

# імпорти твого коду
from database import models

app = FastAPI(title="Perf Test Adapter")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ---- DTO ----
class LoginReq(BaseModel):
    user: str
    pass_: Optional[str] = None

class AddEventReq(BaseModel):
    date: str
    time: str
    title: str
    room: str
    group: str

# ---- helpers ----
def _conn():
    """Універсальне отримання з'єднання: якщо в models є get_db_connection() — беремо її, інакше шукаємо sqlite."""
    if hasattr(models, "get_db_connection"):
        return models.get_db_connection()
    # fallback: якщо десь у config/settings.py є шлях — можна підхопити; інакше дефолт
    db_path = os.environ.get("APP_DB_PATH", os.path.join(os.getcwd(), "database.sqlite3"))
    return sqlite3.connect(db_path)

@app.on_event("startup")
def _init_db():
    # ініціалізація, якщо є
    if hasattr(models, "init_db"):
        try:
            models.init_db()
        except Exception:
            pass

@app.get("/api/health")
def health():
    return {"ok": True}

@app.get("/api/debug_counts")
def debug_counts(group: str = "КС-21"):
    # показує скільки подій бачить САМ сервер у таблиці events
    try:
        with _conn() as c:
            cur = c.cursor()
            cur.execute("SELECT COUNT(*) FROM events WHERE group_name = ?", (group,))
            n = cur.fetchone()[0]
            return {"group": group, "events_count": n}
    except Exception as e:
        raise HTTPException(500, f"debug error: {e}")

# ---- API ----
@app.post("/api/login")
def login(body: LoginReq):
    if not body.user:
        raise HTTPException(400, "user is required")
    return {"token": f"token:{body.user}"}

@app.get("/api/schedule")
def schedule(group: str, date: Optional[str] = None, token: Optional[str] = None):
    if not group:
        raise HTTPException(400, "group is required")

    events = None
    # 1) пробуємо використати функції з models: різні проєкти мають різні назви/сигнатури
    try:
        if hasattr(models, "get_events_for_group"):
            # найчастіший кейс
            events = models.get_events_for_group(group)
        elif hasattr(models, "get_events"):
            # намагаємося з різними сигнатурами
            try:
                events = models.get_events(group, date)
            except TypeError:
                try:
                    events = models.get_events(group)
                except TypeError:
                    events = models.get_events()
        elif date and hasattr(models, "get_events_for_date"):
            events = models.get_events_for_date(date)
    except Exception as e:
        # не падаємо, підемо в SQL-fallback
        events = None

    # 2) SQL-fallback, якщо models не дав результат
    if events is None:
        try:
            with _conn() as c:
                cur = c.cursor()
                if date:
                    cur.execute(
                        "SELECT date, time, title, room, group_name FROM events WHERE group_name=? AND date=?",
                        (group, date),
                    )
                else:
                    cur.execute(
                        "SELECT date, time, title, room, group_name FROM events WHERE group_name=?",
                        (group,),
                    )
                rows = cur.fetchall()
                events = [
                    {"date": r[0], "time": r[1], "title": r[2], "room": r[3], "group": r[4]}
                    for r in rows
                ]
        except Exception as e:
            raise HTTPException(500, f"db error: {e}")

    return {"items": events or []}

@app.post("/api/add_event")
def add_event(body: AddEventReq, token: Optional[str] = None):
    try:
        if hasattr(models, "add_event"):
            new_id = models.add_event(body.date, body.time, body.title, body.room, body.group)
            return {"ok": True, "id": new_id if isinstance(new_id, int) else None}
        # SQL-fallback
        with _conn() as c:
            cur = c.cursor()
            cur.execute(
                "INSERT INTO events(date, time, title, room, group_name) VALUES(?,?,?,?,?)",
                (body.date, body.time, body.title, body.room, body.group),
            )
            c.commit()
            return {"ok": True, "id": cur.lastrowid}
    except Exception as e:
        raise HTTPException(400, str(e))

@app.get("/api/debug_dbpath")
def debug_dbpath():
    return {"DATABASE_URL": settings.DATABASE_URL}
