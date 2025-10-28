# config/settings.py
from dataclasses import dataclass, field
from typing import Set
import os

@dataclass
class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")  # ← БІЛЬШ НЕ ХАРДКОДИМО
    ADMIN_IDS: Set[int] = field(default_factory=lambda: {1341099303})
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///schedule.db")
    NOTIFICATION_INTERVAL_MINUTES: int = int(os.getenv("NOTIF_MIN", "15"))

settings = Settings()
