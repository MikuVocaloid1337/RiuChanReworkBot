import os
from aiogram import Bot, Dispatcher, types, executor
from dotenv import load_dotenv

# Загрузка токена из .env
load_dotenv()
TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# --- ДАННЫЕ ---
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
        ],
        # Остальные категории аналогично добавь при необходимости
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

# --- ПОЛЬЗОВАТЕЛЬСКИЕ ДАННЫЕ ---
offers = {}
lookings = {}
admins = set()
adm_codes = {"#VagueOwner", "#ShapkaKrutoi", "#MikuPikuBeam"}

# --- ПОДДЕРЖКА КОМАНД ---
def format_catalog():
    result = []
    for typ, categories in skins.items():
        result.append(f"Категория: {typ.upper()}")
        for rarity, items in categories.items():
            result.append(f"  Редкость: {rarity}")
            for item in items:
                if isinstance(item, str):
                    result.append(f"    " + item + "")
                elif isinstance(item, dict):
                    result.append(f"    {item['name']}")
                    result.append("     " + ", ".join(item["parts"]))
    return "\n".join(result)

@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    await msg.reply("Бот активен. Напиши /help для списка команд.")

@dp.message_handler(commands=['help'])
async def help_command(msg: types.Message):
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
    await msg.reply(text)

@dp.message_handler(lambda msg: msg.text.startswith("+трейд"))
async def add_trade(msg: types.Message):
    user_id = msg.from_user.id
    lines = msg.text.split("\n")[1:] if "\n" in msg.text else [msg.text[7:]]
    offers[user_id] = offers.get(user_id, [])
    for line in lines:
        offers[user_id].append(line.strip())
    await msg.reply("Добавлено в трейд.")

@dp.message_handler(lambda msg: msg.text.startswith("+lf"))
async def add_lf(msg: types.Message):
    user_id = msg.from_user.id
    lines = msg.text.split("\n")[1:] if "\n" in msg.text else [msg.text[4:]]
    lookings[user_id] = lookings.get(user_id, [])
    for line in lines:
        lookings[user_id].append(line.strip())
    await msg.reply("Добавлено в лф.")

@dp.message_handler(lambda msg: msg.text == "!трейд")
async def show_trade(msg: types.Message):
    user_id = msg.from_user.id
    trades = offers.get(user_id, [])
    if not trades:
        await msg.reply("Трейд пуст.")
    else:
        await msg.reply("Твой трейд:\n" + "\n".join(f"- {t}" for t in trades), parse_mode='Markdown')

@dp.message_handler(lambda msg: msg.text == "!лф")
async def show_lf(msg: types.Message):
    user_id = msg.from_user.id
    lfs = lookings.get(user_id, [])
    if not lfs:
        await msg.reply("Лф пуст.")
    else:
        await msg.reply("Ты ищешь:\n" + "\n".join(f"- {t}" for t in lfs), parse_mode='Markdown')

@dp.message_handler(lambda msg: msg.text == "!очистить трейд")
async def clear_trade(msg: types.Message):
    user_id = msg.from_user.id
    offers[user_id] = []
    await msg.reply("Трейд очищен.")

@dp.message_handler(lambda msg: msg.text == "!очистить лф")
async def clear_lf(msg: types.Message):
    user_id = msg.from_user.id
    lookings[user_id] = []
    await msg.reply("Лф очищен.")

@dp.message_handler(lambda msg: msg.text.lower() in ["ss ст", "s вп", "сет a+", "itm b+", "крф s+"])
async def show_catalog(msg: types.Message):
    await msg.reply(format_catalog(), parse_mode='Markdown')

@dp.message_handler(lambda msg: msg.text.startswith("#VagueMessage"))
async def vague_message(msg: types.Message):
    if msg.chat.type != "private" or msg.from_user.id not in admins:
        return
    await msg.reply("Дай ссылку куда скинуть твой текст")

    @dp.message_handler()
    async def get_chat_link(m1: types.Message):
        chat_link = m1.text
        await m1.reply("Дай текст который ты хочешь опубликовать в этом чате")

        @dp.message_handler()
        async def get_text(m2: types.Message):
            await bot.send_message(chat_link, m2.text)

@dp.message_handler(lambda msg: msg.text in adm_codes)
async def activate_admin(msg: types.Message):
    user_id = msg.from_user.id
    admins.add(user_id)
    adm_codes.remove(msg.text)
    await msg.reply("Теперь ты админ. Тебе доступны админ-команды.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
    print("Бот запущен.")
    # Запуск бота