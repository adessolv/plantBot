import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
import asyncpg

# === ЗАГРУЗКА .env ===
load_dotenv()

# === НАСТРОЙКИ ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

if not BOT_TOKEN or not DATABASE_URL:
    raise ValueError("❌ BOT_TOKEN или DATABASE_URL не найдены в .env!")

# === ГЛАВНОЕ МЕНЮ ===
MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить цветы"), KeyboardButton(text="🔍 Найти рядом")],
        [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="ℹ️ Помощь")],
    ],
    resize_keyboard=True,
    persistent=True
)

# === FSM СОСТОЯНИЯ ===
class FlowerBotStates(StatesGroup):
    waiting_for_location = State()
    waiting_for_photo = State()
    waiting_for_description = State()
    waiting_nearby_location = State()


async def create_db_pool():
    return await asyncpg.create_pool(DATABASE_URL)


    async with pool.acquire() as conn:
        await conn.execute(
            """
            """,
        )


    async with pool.acquire() as conn:
        spots = await conn.fetch(
            """
            from flower_spots
            where earth_box(ll_to_earth($1, $2), $3) @> ll_to_earth(latitude, longitude)
            order by earth_distance(ll_to_earth($1, $2), ll_to_earth(latitude, longitude))
            limit 5
            """,
            user_lat, user_lon, radius_km * 1000,
        )
        return spots


async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    db_pool = await create_db_pool()
    dp["db_pool"] = db_pool

    @dp.message(Command("start"))
    async def cmd_start(message: Message):
        await message.answer(
            "🌸 **Бот красивых цветов города!**\n\n"
            "**Что хочешь сделать?**\n\n"
            "➕ *Добавить цветы* — поделись местом\n"
            "🔍 *Найти рядом* — ближайшие цветы (1 км)\n"
            "📊 *Статистика* — сколько мест сохранено\n"
            "ℹ️ *Помощь* — инструкции\n\n"
            "_Нажми кнопку ниже!_",
            parse_mode="Markdown",
            reply_markup=MAIN_MENU
        )

    @dp.message(lambda m: m.text == "➕ Добавить цветы")
    @dp.message(Command("add"))
    async def cmd_add(message: Message, state: FSMContext):
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📍 Отправить локацию", request_location=True)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await message.answer(
            "📍 Поделись локацией, где ты увидел(а) красивые цветы:",
            reply_markup=kb,
        )
        await state.set_state(FlowerBotStates.waiting_for_location)

    @dp.message(FlowerBotStates.waiting_for_location, F.location)
    async def process_add_location(message: Message, state: FSMContext):
        await message.answer(
            "📸 Теперь пришли фото цветов (или `/skip` если фото нет):",
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.set_state(FlowerBotStates.waiting_for_photo)

    @dp.message(FlowerBotStates.waiting_for_photo, F.photo)
    async def process_photo(message: Message, state: FSMContext):
        photo_id = message.photo[-1].file_id
        await state.update_data(photo_id=photo_id)
        await message.answer("✍️ Напиши короткое описание места с цветами:")
        await state.set_state(FlowerBotStates.waiting_for_description)

    @dp.message(FlowerBotStates.waiting_for_photo, Command("skip"))
    async def skip_photo(message: Message, state: FSMContext):
        await state.update_data(photo_id=None)
        await message.answer("✍️ Напиши короткое описание места с цветами:")
        await state.set_state(FlowerBotStates.waiting_for_description)

    @dp.message(FlowerBotStates.waiting_for_description)
    async def save_spot(message: Message, state: FSMContext):
        data = await state.get_data()
        lat = data["lat"]
        lon = data["lon"]
        photo_id = data.get("photo_id")
        description = message.text.strip()

        pool = dp["db_pool"]

        google_maps = f"https://www.google.com/maps/search/?api=1&query={lat:.6f}%2C{lon:.6f}"

        text = (
            f"✅ **Место сохранено!** 🌺\n\n"
            f"📍 `{lat:.6f}, {lon:.6f}`\n"
            f"📝 {description}\n\n"
            f"🗺️ [Открыть в Google Maps]({google_maps})\n"
            f"🗺️ [OpenStreetMap](https://www.openstreetmap.org/?mlat={lat}&mlng={lon}#map=17/{lat}/{lon})"
        )

        await message.answer(text, parse_mode="Markdown", reply_markup=MAIN_MENU)
        await state.clear()

    @dp.message(lambda m: m.text == "🔍 Найти рядом")
    @dp.message(Command("nearby"))
    async def cmd_nearby(message: Message, state: FSMContext):
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📍 Моя локация", request_location=True)]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        await message.answer(
            "🔍 Покажи свою локацию — найду ближайшие цветы **в 1 км**!",
            parse_mode="Markdown",
            reply_markup=kb,
        )
        await state.set_state(FlowerBotStates.waiting_nearby_location)

    @dp.message(FlowerBotStates.waiting_nearby_location, F.location)
    async def process_nearby_location(message: Message, state: FSMContext):
        user_lat = message.location.latitude
        user_lon = message.location.longitude
        pool = dp["db_pool"]

        spots = await get_nearby_spots(pool, user_lat, user_lon)

        if not spots:
            await message.answer("😔 В радиусе 1 км цветы не найдены.")
        else:
            await message.answer(f"🌺 Найдено **{len(spots)}** мест поблизости **(1 км)**:")

            for i, spot in enumerate(spots, 1):
                lat, lon = spot["latitude"], spot["longitude"]
                desc = spot["description"] or "Красивые цветы"


                await message.bot.send_location(
                    chat_id=message.chat.id,
                    latitude=lat,
                    longitude=lon
                )

                if spot["photo_id"]:
                    await message.bot.send_photo(
                        chat_id=message.chat.id,
                        photo=spot["photo_id"],
                        caption="Фото с места 🌸"
                    )

        await state.clear()
        await message.answer("✅ Готово!", reply_markup=MAIN_MENU)

    @dp.message(lambda m: m.text == "📊 Статистика")
    async def menu_stats(message: Message):
        pool = dp["db_pool"]
        async with pool.acquire() as conn:
            total = await conn.fetchval("select count(*) from flower_spots")
            users = await conn.fetchval("select count(distinct user_id) from flower_spots")

        await message.answer(
            f"📊 **Статистика бота**\n\n"
            f"🌺 Всего мест: **{total}**\n"
            f"👥 Участников: **{users}**\n\n"
            f"Спасибо за вклад в карту цветов! 💐",
            parse_mode="Markdown",
            reply_markup=MAIN_MENU
        )

    @dp.message(lambda m: m.text == "ℹ️ Помощь")
    async def menu_help(message: Message):
        await message.answer(
            "ℹ️ **Как пользоваться**\n\n"
            "1️⃣ **➕ Добавить цветы**\n"
            "   📍 → 📸 → ✍️ описание\n\n"
            "2️⃣ **🔍 Найти рядом**\n"
            "   Ищешь в радиусе 1 км\n\n"
            "3️⃣ Ссылки на Google Maps + OSM\n\n"
            "_Меню всегда внизу!_ 🌸",
            parse_mode="Markdown",
            reply_markup=MAIN_MENU
        )

    try:
        print("🚀 Бот запущен!")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await db_pool.close()


if __name__ == "__main__":
    asyncio.run(main())
