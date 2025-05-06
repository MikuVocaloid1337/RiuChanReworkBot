# bot.py

import os
import signal
import json
import logging
import time
from scam_rules import SCAM_KEYWORDS, SCAM_DOMAINS, SCAM_PATTERNS
from aiogram import Bot, Dispatcher, types, F, BaseMiddleware
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import Message
from collections import defaultdict, deque

class AntiSpamMiddleware(BaseMiddleware):
    def __init__(self, rate_limit=5, per_seconds=60, ban_time=60):
        super().__init__()
        self.rate_limit = rate_limit
        self.per_seconds = per_seconds
        self.ban_time = ban_time
        self.user_timestamps = defaultdict(lambda: deque(maxlen=rate_limit))
        self.banned_users = {}

    async def __call__(self, handler, event: Message, data):
        user_id = event.from_user.id
        now = time.time()

        # Проверка на бан
        if user_id in self.banned_users:
            if now < self.banned_users[user_id]:
                return  # Игнорируем сообщение
            else:
                del self.banned_users[user_id]

        timestamps = self.user_timestamps[user_id]
        timestamps.append(now)

        if len(timestamps) == self.rate_limit and (now - timestamps[0] < self.per_seconds):
            self.banned_users[user_id] = now + self.ban_time
            await event.answer(f"⚠️ Вы слишком активно отправляете сообщения. Подождите {self.ban_time} секунд.")
            return

        return await handler(event, data)

class ScamFilterMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data):
        msg_text = event.text.lower()

        # Поиск по ключевым словам
        if any(word in msg_text for word in SCAM_KEYWORDS):
            await event.delete()
            await event.chat.send_message(f"⚠️ {event.from_user.full_name}, ваше сообщение похоже на скам.")
            return

        # Поиск по доменам
        if any(domain in msg_text for domain in SCAM_DOMAINS):
            await event.delete()
            await event.chat.send_message(f"🚫 Запрещенная ссылка удалена.")
            return

        # Поиск по регуляркам
        for pattern in SCAM_PATTERNS:
            if pattern.search(msg_text):
                await event.delete()
                await event.chat.send_message(f"🛡️ Обнаружен потенциальный скам.")
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
        "!лф — показать твой лф\n"
        "!очистить трейд — очистить трейд\n"
        "!очистить лф — очистить лф\n"
        "+трейд [тип] [название] — добавить в трейд\n"
        "+lf [тип] [название] — добавить в лф\n"
        "Пример сета:\n"
        "+трейд сет 77 rings set: Top, Mid\n"
        "+lf сет 77 rings set: Mid, Low"
    )
    await msg.reply(text)

@dp.message(F.text.startswith("+трейд"))
async def add_trade(msg: types.Message):
    logger.info(f"+трейд от {msg.from_user.id} (@{msg.from_user.username})")
    user_id = msg.from_user.id
    lines = msg.text.split("\n")[1:] if "\n" in msg.text else [msg.text[7:]]
    offers.setdefault(user_id, []).extend([line.strip() for line in lines])
    save_json(offers, "offers.json")
    await msg.answer("Добавлено в трейд.")

@dp.message(F.text.startswith("+lf"))
async def add_lf(msg: types.Message):
    logger.info(f"+lf от {msg.from_user.id} (@{msg.from_user.username})")
    user_id = msg.from_user.id
    lines = msg.text.split("\n")[1:] if "\n" in msg.text else [msg.text[4:]]
    lookings.setdefault(user_id, []).extend([line.strip() for line in lines])
    save_json(lookings, "lookings.json")
    await msg.answer("Добавлено в лф.")

@dp.message(F.text == "!трейд")
async def show_trade(msg: types.Message):
    logger.info(f"!трейд от {msg.from_user.id} (@{msg.from_user.username})")
    user_id = msg.from_user.id
    trades = offers.get(user_id, [])
    if trades:
        await msg.answer("Твой трейд:\n" + "\n".join(f"- {t}" for t in trades))
    else:
        await msg.answer("Трейд пуст.")

@dp.message(F.text == "!лф")
async def show_lf(msg: types.Message):
    logger.info(f"!лф от {msg.from_user.id} (@{msg.from_user.username})")
    user_id = msg.from_user.id
    lfs = lookings.get(user_id, [])
    if lfs:
        await msg.answer("Ты ищешь:\n" + "\n".join(f"- {t}" for t in lfs))
    else:
        await msg.answer("Лф пуст.")

@dp.message(F.text == "!очистить трейд")
async def clear_trade(msg: types.Message):
    offers[msg.from_user.id] = []
    save_json(offers, "offers.json")
    await msg.answer("Трейд очищен.")

@dp.message(F.text == "!очистить лф")
async def clear_lf(msg: types.Message):
    lookings[msg.from_user.id] = []
    save_json(lookings, "lookings.json")
    await msg.answer("Лф очищен.")

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

@dp.errors()
async def error_handler(event, exception):
    logger.exception(f"Ошибка при обработке события {event}: {exception}")

#@dp.message()
#async def echo_handler(message: Message):
#   await message.answer("Сообщение прошло фильтр.")
    
# Запуск бота
async def main():
    logger.info("Бот запущен.")
    dp.message.middleware(AntiSpamMiddleware(rate_limit=5, per_seconds=60, ban_time=60))
    dp.message.middleware(ScamFilterMiddleware())
    try:
        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
