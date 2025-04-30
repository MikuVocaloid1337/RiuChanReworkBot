# bot.py

import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.filters import Command
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

# Логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN, parse_mode=ParseMode.MARKDOWN)
dp = Dispatcher()

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

offers = {}
lookings = {}
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
async def cmd_start(msg: Message):
    await msg.answer("Бот активен. Напиши /help для списка команд.")

@dp.message(Command("help"))
async def cmd_help(msg: Message):
    text = (
        "Основные команды:\n"
        "/help — показать эту справку\n"
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
    await msg.answer(text)

@dp.message(F.text.startswith("+трейд"))
async def add_trade(msg: Message):
    user_id = msg.from_user.id
    lines = msg.text.split("\n")[1:] if "\n" in msg.text else [msg.text[7:]]
    offers.setdefault(user_id, []).extend([line.strip() for line in lines])
    await msg.answer("Добавлено в трейд.")

@dp.message(F.text.startswith("+lf"))
async def add_lf(msg: Message):
    user_id = msg.from_user.id
    lines = msg.text.split("\n")[1:] if "\n" in msg.text else [msg.text[4:]]
    lookings.setdefault(user_id, []).extend([line.strip() for line in lines])
    await msg.answer("Добавлено в лф.")

@dp.message(F.text == "!трейд")
async def show_trade(msg: Message):
    user_id = msg.from_user.id
    trades = offers.get(user_id, [])
    if trades:
        await msg.answer("Твой трейд:\n" + "\n".join(f"- {t}" for t in trades))
    else:
        await msg.answer("Трейд пуст.")

@dp.message(F.text == "!лф")
async def show_lf(msg: Message):
    user_id = msg.from_user.id
    lfs = lookings.get(user_id, [])
    if lfs:
        await msg.answer("Ты ищешь:\n" + "\n".join(f"- {t}" for t in lfs))
    else:
        await msg.answer("Лф пуст.")

@dp.message(F.text == "!очистить трейд")
async def clear_trade(msg: Message):
    offers[msg.from_user.id] = []
    await msg.answer("Трейд очищен.")

@dp.message(F.text == "!очистить лф")
async def clear_lf(msg: Message):
    lookings[msg.from_user.id] = []
    await msg.answer("Лф очищен.")

@dp.message(F.text.in_(["ss ст", "s вп", "сет a+", "itm b+", "крф s+"]))
async def show_catalog_handler(msg: Message):
    await msg.answer(format_catalog())

@dp.message(F.text.in_(adm_codes))
async def activate_admin(msg: Message):
    user_id = msg.from_user.id
    admins.add(user_id)
    adm_codes.remove(msg.text)
    await msg.answer("Теперь ты админ. Тебе доступны админ-команды.")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
