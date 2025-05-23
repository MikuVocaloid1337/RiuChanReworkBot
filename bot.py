# bot.py
import asyncpg
import os
import signal
import json
import logging
import time
import datetime
import aiocron
from scam_rules import SCAM_KEYWORDS, SCAM_DOMAINS, SCAM_PATTERNS
from aiogram import Bot, Dispatcher, types, F, BaseMiddleware
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import Message, Update, ChatMemberAdministrator, ChatMemberOwner
from collections import defaultdict, deque

db_pool: asyncpg.Pool = None
async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(
        dsn=os.getenv("DATABASE_URL")  # Лучше переместить в переменные окружения
    )

    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                username TEXT,
                item TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS lookings (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                username TEXT,
                item TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)

class AntiSpamMiddleware(BaseMiddleware):
    def __init__(self, rate_limit=5, per_seconds=60, ban_time=60):
        super().__init__()
        self.rate_limit = rate_limit
        self.per_seconds = per_seconds
        self.ban_time = ban_time
        self.user_timestamps = defaultdict(lambda: deque(maxlen=rate_limit))
        self.banned_users = {}

    async def __call__(self, handler, event: Message, data):
        bot = data["bot"]
        user_id = event.from_user.id
        chat_id = event.chat.id

        # ⛔ Пропускаем админов
        member = await bot.get_chat_member(chat_id, user_id)
        if isinstance(member, (ChatMemberAdministrator, ChatMemberOwner)):
            return await handler(event, data)

        now = time.time()

        # Проверка на бан
        if user_id in self.banned_users:
            if now < self.banned_users[user_id]:
                return
            else:
                del self.banned_users[user_id]

        timestamps = self.user_timestamps[user_id]
        timestamps.append(now)

        if len(timestamps) == self.rate_limit and (now - timestamps[0] < self.per_seconds):
            self.banned_users[user_id] = now + self.ban_time
            await event.answer(f"⚠️ Ты слишком активно отправляешь сообщения. Подожди {self.ban_time} секунд.")
            return

        return await handler(event, data)
        
class ScamFilterMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data):
        bot = data["bot"]
        user_id = event.from_user.id
        chat_id = event.chat.id

        # ⛔ Пропускаем админов
        member = await bot.get_chat_member(chat_id, user_id)
        if isinstance(member, (ChatMemberAdministrator, ChatMemberOwner)):
            return await handler(event, data)

        msg_text = event.text.lower()

        if any(word in msg_text for word in SCAM_KEYWORDS):
            await event.delete()
            await event.answer(f"⚠️ {event.from_user.full_name}, твоё сообщение похоже на скам.")
            return

        if any(domain in msg_text for domain in SCAM_DOMAINS):
            await event.delete()
            await event.answer(f"🚫 Запрещенная ссылка удалена.")
            return

        for pattern in SCAM_PATTERNS:
            if pattern.search(msg_text):
                await event.delete()
                await event.answer(f"🛡️ Обнаружен потенциальный скам.")
                return

        return await handler(event, data)

logging.basicConfig(
    level=logging.INFO,  # можно DEBUG для подробностей
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

file_handler = logging.FileHandler("bot.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
))
logger.addHandler(file_handler)

DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)


TOKEN = os.environ["TOKEN"]
MAX_LINES = 5
MAX_LINE_LENGTH = 100

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)

dp = Dispatcher()

def save_json(data, filename):
    path = os.path.join(DATA_FOLDER, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json(filename):
    path = os.path.join(DATA_FOLDER, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# --- Данные ---
skins = {
    "ст": {
        "Ss+": ["summer Riu chan"],
        "S+": [],
        "A+": [],
    },
    "вп": {
        "S+": [],
        "A+": [],
        "B+": [],
        "C+": [],
        "D+": [],
    },
    "сет": {
        "S+": [
            {"name": "77 rings set", "parts": ["Top", "Mid", "Low"]},
            {"name": "Puchi heaven set", "parts": ["Mid", "Low"]},
            {"name": "Bruno set", "parts": ["Mid", "Low"]},
            {"name": "Fugo set", "parts": ["Mid", "Low"]},
        ]
    },
    "itm": {
        "SS+": ["Green baby"],
        "S+": ["Skull", "Heart", "Left arm of the saint corpse", "Pure arrow"],
        "A+": ["eye of the saint corpse", "Rib cage of the saint corpse", "Right arm of the saint corpse", "Tommy gun", "Double shot gun"],
        "B+": ["Axe", "Electric hilibard", "Poisonous scimitar", "Right leg of the saint corpse", "Left leg of the saint corpse", "Dio bone"],
        "C+": ["Pluck", "Revolver", "Pistol", "Requiem arrow", "Dio diary", "Locacaca"],
        "D+": ["Arrow", "Stone mask", "Steel ball"]
    },
    "крф": {
        "S+": ["Bruno zipper", "Fugo tie", "Blackmore mask", "Blackmore umbrella", "Johnny horseshoe", "Gyro taddybear"],
        "A+": ["Boss tie", "Pure meteor shard", "Passion badge", "Ladybug brush", "Killer tie"],
        "C+": ["Gold ingot", "Fabric", "Vampire blood", "Leather", "Meteor shards"],
        "D+": ["Steel ingot", "Wood", "Stone"]
    }
}

offers = load_json("offers.json")
lookings = load_json("lookings.json")
admins = set()
adm_codes = {"#VagueOwner", "#ShapkaKrutoi", "#MikuPikuBeam"}

def format_catalog():
    result = []
    for typ, categories in skins.items():
        result.append(f"*Категория: {typ.upper()}*")
        for rarity, items in categories.items():
            result.append(f"  _Редкость: {rarity}_")
            for item in items:
                if isinstance(item, str):
                    result.append(f"    {item}")
                elif isinstance(item, dict):
                    result.append(f"    {item['name']}")
                    result.append("     " + ", ".join(item["parts"]))
    return "\n".join(result)

# --- Хендлеры ---
@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    logger.info(f"/start от {msg.from_user.id} (@{msg.from_user.username})")
    await msg.reply("Бот активен. Напиши /help для списка команд.")

@dp.message(Command("ялох"))
async def cmd_help(msg: types.Message):
    logger.info(f"/ялох от {msg.from_user.id} (@{msg.from_user.username})")
    text = (
        "Основные команды:\n"
        "/ялох — я - овощь, мне нужна помощь\n"
        "!трейд — показать твой трейд\n"
        "!лф — показать твой лф(looking for)\n"
        "!очистить трейд — очистить трейд\n"
        "!очистить лф — очистить лф\n"
        "+трейд [тип] [название] — добавить в трейд\n"
        "+лф [тип] [название] — добавить в лф(looking for)\n"
        "Пример сета:\n"
        "+трейд сет 77 rings set: Top, Mid\n"
        "+lf сет 77 rings set: Mid, Low"
    )
    await msg.reply(text)

def validate_lines(lines: list[str]) -> str | None:
    if len(lines) > MAX_LINES:
        return f"Максимум {MAX_LINES} строк."

    for line in lines:
        stripped = line.strip()
        if not stripped:
            return "Обнаружена пустая строка или строка из одних пробелов."
        if len(stripped) > MAX_LINE_LENGTH:
            return f"Строка слишком длинная (максимум {MAX_LINE_LENGTH} символов):\n{stripped}"

    return None

@dp.message(lambda msg: msg.text.lower().startswith("+трейд"))
async def add_trade(msg: types.Message):
    logger.info(f"+трейд от {msg.from_user.id} (@{msg.from_user.username})")
    user_id = msg.from_user.id
    username = msg.from_user.username or "неизвестно"
    lines = msg.text.split("\n")[1:] if "\n" in msg.text else [msg.text[7:]]

    error = validate_lines(lines)
    if error:
        await msg.answer(error)
        return

    clean_lines = [line.strip() for line in lines]

    async with db_pool.acquire() as conn:
        await conn.executemany(
            "INSERT INTO trades (user_id, username, item) VALUES ($1, $2, $3)",
            [(user_id, username, line) for line in clean_lines]
        )
    await msg.answer("Добавлено в трейд.")


@dp.message(lambda msg: msg.text.lower().startswith("+лф"))
async def add_lf(msg: types.Message):
    logger.info(f"+лф от {msg.from_user.id} (@{msg.from_user.username})")
    user_id = msg.from_user.id
    username = msg.from_user.username or "неизвестно"
    lines = msg.text.split("\n")[1:] if "\n" in msg.text else [msg.text[4:]]

    error = validate_lines(lines)
    if error:
        await msg.answer(error)
        return

    clean_lines = [line.strip() for line in lines]

    async with db_pool.acquire() as conn:
        await conn.executemany(
            "INSERT INTO lookings (user_id, username, item) VALUES ($1, $2, $3)",
            [(user_id, username, line) for line in clean_lines]
        )
    await msg.answer("Добавлено в лф.")



@dp.message(lambda msg: msg.text.lower().startswith("!трейд"))
async def show_trade(msg: types.Message):
    logger.info(f"!трейд от {msg.from_user.id} (@{msg.from_user.username})")
    user_id = msg.from_user.id
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT username, item FROM trades ORDER BY user_id")

    if not rows:
        await msg.answer("Трейд пуст.")
        return

    # Сгруппируем по пользователям
    trades = {}
    for row in rows:
        uname = row["username"] or "неизвестно"
        trades.setdefault(uname, []).append(row["item"])

    text = "Трейд-лист:\n"
    for username, items in trades.items():
        text += f"\n{username}:\n" + "\n".join(f"- {item}" for item in items)
        
    await msg.answer(text)
        
@dp.message(lambda msg: msg.text.lower().startswith("!лф"))
async def show_lf(msg: types.Message):
    logger.info(f"!лф от {msg.from_user.id} (@{msg.from_user.username})")
    user_id = msg.from_user.id
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT username, item FROM lookings ORDER BY user_id")

    if not rows:
        await msg.answer("ЛФ пуст.")
        return

    lookings = {}
    for row in rows:
        uname = row["username"] or "неизвестно"
        lookings.setdefault(uname, []).append(row["item"])

    text = "ЛФ:\n"
    for username, items in lookings.items():
        text += f"\n{username}:\n" + "\n".join(f"- {item}" for item in items)

    await msg.answer(text)

@dp.message(lambda msg: msg.text.lower().startswith("!очистить трейд"))
async def clear_trade(msg: types.Message):
    user_id = msg.from_user.id
    async with db_pool.acquire() as conn:
        # Удаляем все записи, связанные с пользователем из таблицы трейдов
        await conn.execute('DELETE FROM trades WHERE user_id = $1', user_id)
    await msg.answer("Трейд очищен.")

@dp.message(lambda msg: msg.text.lower().startswith("!очистить лф"))
async def clear_lf(msg: types.Message):
    user_id = msg.from_user.id
    async with db_pool.acquire() as conn:
        # Удаляем все записи, связанные с пользователем из таблицы лф
        await conn.execute('DELETE FROM lookings WHERE user_id = $1', user_id)
    await msg.answer("Лф очищен.")

async def delete_old_records():
    # Текущая дата
    now = datetime.datetime.now()
    # Дата, старше которой будем удалять записи (7 дней назад)
    threshold_date = now - datetime.timedelta(days=7)
    
    async with db_pool.acquire() as conn:
        # Удаляем записи из трейдов, старше 30 дней
        await conn.execute('DELETE FROM trades WHERE created_at < $1', threshold_date)
        # Удаляем записи из лф, старше 30 дней
        await conn.execute('DELETE FROM lookings WHERE created_at < $1', threshold_date)


@dp.message(F.text.in_(["ss ст", "s вп", "сет a+", "itm b+", "крф s+"]))
async def show_catalog_handler(msg: types.Message):
    await msg.answer(format_catalog())

@dp.message(F.text.in_(adm_codes))
async def activate_admin(msg: types.Message):
    user_id = msg.from_user.id
    admins.add(user_id)
    adm_codes.remove(msg.text)
    logger.info(f"Пользователь {user_id} активировал админ-доступ.")
    await msg.answer("Теперь ты админ. Тебе доступны админ-команды.")

# ID публичного чата или канала, куда бот будет отправлять сообщения
TARGET_CHAT_ID = -1002170558932  # замените на ID своего чата/канала

# Список ID пользователей, которым разрешено вещать
ALLOWED_USERS = {690469640, 5762585402}  # Используем множество (set) для быстрого поиска

#@dp.message_handler(commands=['ban'], user_id=ALLOWED_USERS)
#async def ban_user(msg: types.Message):
#    user_id_to_ban = int(msg.get_args())
#    try:
#        await msg.chat.kick_member(user_id_to_ban)
#        await msg.answer(f"Пользователь с ID {user_id_to_ban} забанен.")
#    except Exception as e:
#        await msg.answer(f"Не удалось забанить пользователя: {e}")

@dp.message(F.chat.type == "private")
async def forward_to_channel(message: Message):
    if message.from_user.id not in ALLOWED_USERS:
        return  # Игнорируем остальных

    # Пересылка текста
    if message.text:
        logger.info(f"Пользователь {message.from_user.id} отправил сообщение через бота")
        await bot.send_message(chat_id=TARGET_CHAT_ID, text=message.text)

    elif message.photo:
        await bot.send_photo(chat_id=TARGET_CHAT_ID, photo=message.photo[-1].file_id, caption=message.caption or "")
    elif message.video:
        await bot.send_video(chat_id=TARGET_CHAT_ID, video=message.video.file_id, caption=message.caption or "")
    elif message.document:
        await bot.send_document(chat_id=TARGET_CHAT_ID, document=message.document.file_id, caption=message.caption or "")
    else:
        await message.answer("⛔ Этот тип сообщений пока не поддерживается.")

@dp.error()
async def error_handler(update: Update, exception: Exception):
    logger.exception(f"Ошибка при обработке события {update}: {exception}")
    return True

@dp.message()
async def echo_handler(message: Message):
    logger.info(f"сообщение.")

@aiocron.crontab('0 0 * * *')
async def scheduled_delete_old_records():
    await delete_old_records()
    
# Запуск бота
async def main():
    logger.info("Бот запущен.")
    dp.message.middleware(AntiSpamMiddleware(rate_limit=5, per_seconds=60, ban_time=60))
    dp.message.middleware(ScamFilterMiddleware())
    try:
        await init_db()
        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
