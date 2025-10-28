# load/server.py
import os
import sys
import sqlite3
import logging
from typing import Optional, List, Dict, Any

# Ensure project root is importable
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware

# Your project imports
from database import models

# ----------------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------------
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# ----------------------------------------------------------------------------
# App & CORS (keep wide-open for test adapter; tighten in production)
# ----------------------------------------------------------------------------
app = FastAPI(title="Perf Test Adapter")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------------------------------
# Schemas
# ----------------------------------------------------------------------------
class LoginReq(BaseModel):
    user: str
    pass_: Optional[str] = None  # kept for compatibility; not used here

class AddEventReq(BaseModel):
    date: str
    time: str
    title: str
    room: str
    group: str

# ----------------------------------------------------------------------------
# DB helpers
# ----------------------------------------------------------------------------

def _conn() -> sqlite3.Connection:
    """Return a DB connection either from project helper or local sqlite path."""
    if hasattr(models, "get_db_connection"):
        return models.get_db_connection()
    db_path = os.environ.get("APP_DB_PATH", os.path.join(os.getcwd(), "database.sqlite3"))
    try:
        return sqlite3.connect(db_path)
    except sqlite3.Error as e:
        logger.exception("Failed to connect to SQLite at %s", db_path)
        raise

# ----------------------------------------------------------------------------
# Lifecycle
# ----------------------------------------------------------------------------

@app.on_event("startup")
def _init_db() -> None:
    """Initialize DB once on startup. Log failures instead of silently passing."""
    if hasattr(models, "init_db"):
        try:
            models.init_db()
            logger.info("DB initialization finished")
        except Exception as e:  # noqa: BLE001 (we want to log full trace at startup)
            # NOTE: do not swallow errors; log them explicitly for diagnostics
            logger.exception("DB initialization failed: %s", e)
            # We deliberately don't re-raise to allow the adapter to start; tests may rely on this.

# ----------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------

@app.get("/api/health")
def health() -> Dict[str, bool]:
    return {"ok": True}

@app.get("/api/debug_counts")
def debug_counts(group: str = "КС-21") -> Dict[str, Any]:
    try:
        with _conn() as c:
            cur = c.cursor()
            cur.execute("SELECT COUNT(*) FROM events WHERE group_name = ?", (group,))
            n = cur.fetchone()[0]
            return {"group": group, "events_count": n}
    except Exception as e:  # keep broad -> converted to 500
        logger.exception("/api/debug_counts failed for group=%s: %s", group, e)
        raise HTTPException(status_code=500, detail=f"debug error: {e}") from e

@app.post("/api/login")
def login(body: LoginReq) -> Dict[str, str]:
    if not body.user:
        raise HTTPException(status_code=400, detail="user is required")
    # This is a dummy token for test adapter purposes only
    return {"token": f"token:{body.user}"}

@app.get("/api/schedule")
def schedule(group: str, date: Optional[str] = None, token: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    if not group:
        raise HTTPException(status_code=400, detail="group is required")

    events: Optional[List[Dict[str, Any]]] = None

    # Prefer project-level helpers if available
    try:
        if hasattr(models, "get_events_for_group"):
            events = models.get_events_for_group(group)
        elif hasattr(models, "get_events"):
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
        logger.exception("Project-level events fetch failed: %s", e)
        events = None

    # Fallback to direct SQL if helpers not present / failed
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
            logger.exception("DB error on /api/schedule: group=%s date=%s err=%s", group, date, e)
            raise HTTPException(status_code=500, detail=f"db error: {e}") from e

    return {"items": events or []}

@app.post("/api/add_event")
def add_event(body: AddEventReq, token: Optional[str] = None) -> Dict[str, Any]:
    try:
        if hasattr(models, "add_event"):
            new_id = models.add_event(body.date, body.time, body.title, body.room, body.group)
            return {"ok": True, "id": new_id if isinstance(new_id, int) else None}

        with _conn() as c:
            cur = c.cursor()
            cur.execute(
                "INSERT INTO events(date, time, title, room, group_name) VALUES(?,?,?,?,?)",
                (body.date, body.time, body.title, body.room, body.group),
            )
            c.commit()
            return {"ok": True, "id": cur.lastrowid}
    except Exception as e:
        logger.exception("/api/add_event failed: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
