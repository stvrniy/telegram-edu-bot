from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from config.settings import settings
from database.models import add_user, get_user, update_user_group, get_events, toggle_notifications, update_user_name
from datetime import date, datetime
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

class UserStates(StatesGroup):
    waiting_for_name = State()

@router.message(Command("start"))
async def start_command(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    add_user(user_id, is_admin=1 if user_id in settings.ADMIN_IDS else 0)
    
    welcome_text = (
        f"👋 Вітаю, {username}!\n\n"
        "📚 Я бот для відстеження розкладу занять\n\n"
        "📋 *Доступні команди:*\n\n"
        "🏫 Встановити групу:\n"
        "`/setgroup <назва_групи>`\n"
        "Приклад: `/setgroup КС-21`\n\n"
        "👤 Встановити ім'я:\n"
        "`/setname <Ім'я Прізвище>`\n\n"
        "📅 Розклад на сьогодні:\n"
        "`/today`\n\n"
        "📋 Повний розклад:\n"
        "`/schedule`\n\n"
        "🔔 Керування сповіщеннями:\n"
        "`/notifications`\n\n"
        "ℹ️ Довідка:\n"
        "`/help`\n"
        "`/commands` - список всіх команд"
    )
    
    if user_id in settings.ADMIN_IDS:
        welcome_text += "\n\n👨‍💼 *Ви також адміністратор!*\n"
        welcome_text += "Доступні адмін-команди: `/admin_help` або `/admin_commands`"
    
    await message.answer(welcome_text, parse_mode="Markdown")

@router.message(Command("help"))
@router.message(Command("commands"))
async def help_command(message: Message):
    user_id = message.from_user.id
    is_admin = user_id in settings.ADMIN_IDS
    
    help_text = (
        "📚 *Список всіх команд студента:*\n\n"
        "🏫 Встановити групу:\n"
        "`/setgroup <назва_групи>`\n"
        "Приклад: `/setgroup КС-21`\n\n"
        "👤 Встановити ім'я:\n"
        "`/setname <Ім'я Прізвище>`\n"
        "Приклад: `/setname Іван Іванов`\n\n"
        "📅 Розклад на сьогодні:\n"
        "`/today` - показує заняття на сьогодні\n\n"
        "📋 Повний розклад:\n"
        "`/schedule` - показує весь розклад групи\n\n"
        "🔔 Керування сповіщеннями:\n"
        "`/notifications` - увімкнення/вимкнення сповіщень\n\n"
        "ℹ️ Довідка:\n"
        "`/help` - ця довідка\n"
        "`/commands` - список команд\n\n"
        "🚀 Початок роботи:\n"
        "`/start` - перезапустити бота"
    )
    
    if is_admin:
        help_text += "\n\n👨‍💼 *Адмін-команди:*\n"
        help_text += "`/admin_help` - довідка адміністратора\n"
        help_text += "`/admin_commands` - список адмін-команд"
    
    await message.answer(help_text, parse_mode="Markdown")

@router.message(Command("setname"))
async def set_name_command(message: Message, state: FSMContext):
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.answer("❌ Будь ласка, вкажіть ім'я та прізвище!\n"
                           "Приклад: `/setname Іван Іванов`", parse_mode="Markdown")
        return
    
    full_name = args[1].strip()
    
    if len(full_name) < 3:
        await message.answer("❌ Ім'я занадто коротке!")
        return
    
    update_user_name(message.from_user.id, full_name)
    await message.answer(f"✅ Ім'я встановлено: *{full_name}*", parse_mode="Markdown")

@router.message(Command("setgroup"))
async def set_group_command(message: Message):
    user_id = message.from_user.id
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.answer("❌ Будь ласка, вкажіть назву групи!\n"
                           "Приклад: `/setgroup КС-21`", parse_mode="Markdown")
        return
    
    group_name = args[1].strip()
    
    if len(group_name) > 20:
        await message.answer("❌ Назва групи занадто довга! Максимум 20 символів")
        return
    
    update_user_group(user_id, group_name)
    await message.answer(f"✅ Групу встановлено: *{group_name}*", parse_mode="Markdown")

@router.message(Command("schedule"))
async def schedule_command(message: Message):
    user = get_user(message.from_user.id)
    
    if not user or not user[1]:
        await message.answer("❌ Спочатку встановіть групу командою `/setgroup`", parse_mode="Markdown")
        return
    
    group_name = user[1]
    events = get_events(group_name)
    
    if not events:
        await message.answer(f"📭 Для групи *{group_name}* немає запланованих подій", parse_mode="Markdown")
        return
    
    response = f"📋 *Розклад для {group_name}:*\n\n"
    
    current_date = None
    for event in events:
        if event[1] != current_date:
            current_date = event[1]
            response += f"\n📅 *{current_date}:*\n"
        response += f"⏰ {event[2]}: {event[3]} (ауд. {event[4]})\n"
    
    await message.answer(response, parse_mode="Markdown")

@router.message(Command("today"))
async def today_command(message: Message):
    user = get_user(message.from_user.id)
    
    if not user or not user[1]:
        await message.answer("❌ Спочатку встановіть групу командою `/setgroup`", parse_mode="Markdown")
        return
    
    group_name = user[1]
    today = date.today().isoformat()
    events = get_events(group_name, today)
    
    if not events:
        await message.answer(f"📭 На сьогодні для *{group_name}* немає подій", parse_mode="Markdown")
        return
    
    response = f"📅 *Розклад на сьогодні для {group_name}:*\n\n"
    
    for event in events:
        response += f"⏰ {event[2]}: {event[3]} (ауд. {event[4]})\n"
    
    await message.answer(response, parse_mode="Markdown")

@router.message(Command("notifications"))
async def notifications_command(message: Message):
    user = get_user(message.from_user.id)
    
    if not user:
        await message.answer("❌ Спочатку запустіть бота командою `/start`")
        return
    
    current_status = "увімкнено" if user[3] == 1 else "вимкнено"
    new_status = not user[3]
    
    toggle_notifications(message.from_user.id, new_status)
    
    status_text = "увімкнено" if new_status else "вимкнено"
    await message.answer(f"🔔 Сповіщення {status_text}!")