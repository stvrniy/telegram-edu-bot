from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import logging
from config.settings import settings
from database.models import get_events_for_date, get_users_for_group

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
    
    def start(self):
        self.scheduler.add_job(
            self.check_events,
            trigger="interval",
            minutes=1,
            next_run_time=datetime.now()
        )
        self.scheduler.start()
        logger.info("Scheduler started")
    
    async def check_events(self):
        now = datetime.now()
        target_time = now.strftime("%H:%M")
        date_str = now.date().isoformat()
        events = get_events_for_date(date_str)
        
        # Додаємо логування для діагностики
        logger.info(f"[Scheduler] Перевірка о {now}. Шукаємо події на {date_str} о {target_time}")
        
        if not events:
            logger.info(f"[Scheduler] Подій на {date_str} не знайдено.")
            return

        for event in events:
            logger.info(f"[Scheduler] Перевіряємо подію: {event}")
            
            # Виправлено індекси згідно структури бази даних:
            # event[0] - id, event[1] - date, event[2] - time, event[3] - title, 
            # event[4] - room, event[5] - group_name
            if event[2] == target_time:  # event[2] - час події
                group_name = event[5]    # event[5] - назва групи
                logger.info(f"[Scheduler] Знайдено відповідну подію для групи {group_name}")
                
                users = get_users_for_group(group_name)
                logger.info(f"[Scheduler] Знайдено {len(users)} користувачів для групи {group_name}")
                
                if not users:
                    logger.info(f"[Scheduler] Немає користувачів у групі {group_name} для сповіщення")
                    continue
                    
                for user in users:
                    # Виправлено індекси згідно структури бази даних:
                    # user[0] - user_id, user[1] - group_name, user[2] - full_name,
                    # user[3] - is_admin, user[4] - notifications_enabled
                    logger.info(f"[Scheduler] Перевіряємо користувача {user[0]}, сповіщення: {user[4] == 1}")
                    if user[4] == 1:  # notifications_enabled = 1 (індекс 4, а не 3)
                        try:
                            await self.bot.send_message(
                                user[0],  # user_id
                                f"⏰ Нагадування: {event[3]} о {event[2]}\n"
                                f"📅 Дата: {event[1]}\n"
                                f"🏫 Аудиторія: {event[4]}\n"
                                f"👥 Група: {event[5]}"
                            )
                            logger.info(f"[Scheduler] Сповіщення відправлено користувачу {user[0]}")
                        except Exception as e:
                            logger.error(f"[Scheduler] Помилка відправки для {user[0]}: {e}")
            else:
                logger.info(f"[Scheduler] Час не співпав: {event[2]} != {target_time}")