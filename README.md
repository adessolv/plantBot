🌸 PlantBot — Карта красивых цветов города

Telegram-бот для совместного сбора и поиска красивых цветочных мест в городе! 🌺

Пользователи отмечают места с цветами (📍 + 📸 + описание), другие находят ближайшие точки в радиусе 1 км.

✨ Возможности      Функция	        Описание

➕ Добавить цветы	Локация → Фото → Описание → Сохранение в Supabase
🔍 Найти рядом	    Ближайшие цветы в 1 км с картами и фото
📊 Статистика	    Количество мест и пользователей
🗺️ Карты	        Google Maps + OpenStreetMap ссылки
📱 Главное меню	    Удобные кнопки вместо команд

🎮 Демо
text
👤 /start
🤖 🌸 Бот красивых цветов города!

➕ Добавить цветы  🔍 Найти рядом
📊 Статистика      ℹ️ Помощь

🛠️ Технологии
text
• Python 3.11+ + aiogram 3.x
• PostgreSQL (Supabase)
• Гео-поиск (earthdistance + cube)
• dotenv для секретов

🚀 Быстрый старт
1. Клонируй репозиторий
bash
git clone https://github.com/yourusername/plant-bot.git
cd plant-bot
2. Установи зависимости
bash
pip install -r requirements.txt
3. Создай .env
text
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
DATABASE_URL=postgres://postgres:pass@db_xxx.supabase.co:5432/postgres
4. Настрой Supabase
SQL Editor:

sql
-- Таблица
CREATE TABLE flower_spots (
    id bigserial PRIMARY KEY,
    user_id bigint,
    latitude double precision NOT NULL,
    longitude double precision NOT NULL,
    photo_id text,
    description text,
    created_at timestamptz DEFAULT now()
);

-- Гео-поиск (для /nearby)
CREATE EXTENSION IF NOT EXISTS cube;
CREATE EXTENSION IF NOT EXISTS earthdistance;

5. Запусти!
bash
python main.py
🚀 Бот запущен!
