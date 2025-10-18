from dataclasses import dataclass, field
from typing import Set

@dataclass
class Settings:
    BOT_TOKEN: str = "8056743092:AAEPhwpz6dWVH4Go8HLGLBi1KBKR4es4SZE"
    ADMIN_IDS: Set[int] = field(default_factory=lambda: {1341099303})
    DATABASE_URL: str = "sqlite:///schedule.db"  # Додайте цей рядок
    NOTIFICATION_INTERVAL_MINUTES: int = 15  # Можна також додати

settings = Settings()