from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from config.settings import settings
from functools import wraps

router = Router()

def admin_only(func):
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs):
        user_id = message.from_user.id
        if user_id not in settings.ADMIN_IDS:
            await message.answer("❌ Ця команда доступна лише адміністраторам")
            return
        return await func(message, *args, **kwargs)
    return wrapper

@router.message(Command("upload_schedule"))
@admin_only
async def upload_schedule_command(message: Message):
    await message.answer("📤 *Завантаження розкладу з PDF файлу*\n\n"
                       "🚧 Ця функція планується до додавання в майбутніх оновленнях\n\n"
                       "Наразі ви можете додавати події вручну командою:\n"
                       "`/add_event <дата> <час> <назва> <аудиторія> <група>`\n\n"
                       "Приклад: `/add_event 2025-09-16 10:00 Математика 301 КС-21`",
                       parse_mode="Markdown")