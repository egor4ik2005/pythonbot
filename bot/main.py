import random
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import psycopg2
import os
import math

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

db_config = {
    'dbname': os.getenv('DB_NAME', 'egor'),
    'user': os.getenv('DB_USER', 'egor2005'),
    'password': os.getenv('DB_PASSWORD', '123'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', 5432)
}

BOT_TOKEN = str(os.environ.get("BOT_TOKEN"))
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

HEROES_PER_PAGE = 8

class QuizStates(StatesGroup):
    waiting_for_answer = State()

class TeamBuildingStates(StatesGroup):
    choosing_heroes = State()

def get_heroes_from_db():
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        query = "SELECT name, info_data, COALESCE(base_damage, 5) FROM heroes_info;"
        cursor.execute(query)
        heroes = cursor.fetchall()
        cursor.close()
        conn.close()
        return heroes
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        return []

def create_start_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Викторина", callback_data="quiz")],
        [InlineKeyboardButton(text="Сбор команды", callback_data="team_building")]
    ])
    return keyboard

@dp.message(Command("start"))
async def start(message: types.Message):
    keyboard = create_start_keyboard()
    await message.answer("Добро пожаловать! Выберите одну из опций:", reply_markup=keyboard)

@dp.callback_query()
async def handle_callback(callback_query: CallbackQuery, state: FSMContext):
    if callback_query.data == "quiz":
        await start_quiz(callback_query.message, state)

    elif callback_query.data == "team_building":
        heroes = get_heroes_from_db()
        if not heroes:
            await callback_query.message.answer("Героев не найдено в базе данных.")
            return

        total_pages = math.ceil(len(heroes) / HEROES_PER_PAGE)
        current_page = 0

        await state.update_data(selected_heroes=[], total_damage=0)
        await state.set_state(TeamBuildingStates.choosing_heroes)

        await send_team_building_page(callback_query.message.chat.id, heroes, current_page, total_pages, callback_query.message)

    elif callback_query.data.startswith("hero_"):
        selected_hero = callback_query.data.split("_")[1]
        data = await state.get_data()
        selected_heroes = data.get("selected_heroes", [])
        total_damage = data.get("total_damage", 0)

        heroes = get_heroes_from_db()
        hero_data = next((h for h in heroes if h[0] == selected_hero), None)

        if not hero_data:
            await callback_query.message.answer("Ошибка: герой не найден в базе данных.")
            return
        
        hero_name, hero_info, base_damage = hero_data

        if selected_hero in selected_heroes:
            await callback_query.message.answer(f"Герой {selected_hero} уже добавлен в команду!")
            return

        if len(selected_heroes) < 5:
            selected_heroes.append(selected_hero)
            total_damage += base_damage
            await state.update_data(selected_heroes=selected_heroes, total_damage=total_damage)

            if total_damage < 100:
                strength = "слабая"
            elif total_damage < 150:
                strength = "средняя"
            else:
                strength = "сильная"

            message_text = f"Герой {selected_hero} добавлен в команду!\n" \
                           f"Текущая команда: {', '.join(selected_heroes)}\n" \
                           f"Общий урон: {total_damage}\n" \
                           f"Сила команды: {strength}"

            if len(selected_heroes) == 5:
                message_text = f"Команда собрана! Вот ваш выбор:\n" \
                               f"{', '.join(selected_heroes)}\n" \
                               f"Общий урон: {total_damage}\n" \
                               f"Сила команды: {strength}"

            await edit_or_send_team_message(callback_query.message, message_text)

        else:
            await callback_query.message.answer("Вы уже собрали команду из 5 героев.")

    elif callback_query.data.startswith("page_"):
        current_page = int(callback_query.data.split("_")[1])
        heroes = get_heroes_from_db()
        total_pages = math.ceil(len(heroes) / HEROES_PER_PAGE)

        await send_team_building_page(callback_query.message.chat.id, heroes, current_page, total_pages, callback_query.message)

    elif callback_query.data.startswith("quiz_"):
        selected_hero = callback_query.data.split("_")[1]
        data = await state.get_data()
        correct_hero = data.get("correct_answer")

        if selected_hero == correct_hero:
            new_text = "Правильно! Поздравляю!"
        else:
            new_text = f"Неверно. Правильный ответ: {correct_hero}"

        menu_button = InlineKeyboardButton(text="Главное меню", callback_data="start_menu")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[menu_button]])

        await bot.edit_message_text(
            text=new_text,
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard
        )

        await state.clear()

    elif callback_query.data == "start_menu":
        keyboard = create_start_keyboard()
        await bot.edit_message_text(
            text="Добро пожаловать! Выберите одну из опций:",
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=keyboard
        )

async def start_quiz(message: types.Message, state: FSMContext):
    heroes = get_heroes_from_db()
    if not heroes:
        await message.answer("Героев не найдено в базе данных.")
        return

    hero = random.choice(heroes)
    hero_name, hero_info, base_damage = hero

    if "—" in hero_info:
        description_without_name = hero_info.split('—', 1)[-1].strip()
    else:
        description_without_name = hero_info

    await state.update_data(correct_answer=hero_name)

    other_heroes = [h[0] for h in heroes if h[0] != hero_name]
    options = random.sample(other_heroes, k=4) + [hero_name]
    random.shuffle(options)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=option, callback_data=f"quiz_{option}")] for option in options
    ])

    quiz_text = f"Описание героя: {description_without_name}\nБазовый урон: {base_damage}\n\nКак зовут этого героя?"
    await bot.edit_message_text(
        text=quiz_text,
        chat_id=message.chat.id,
        message_id=message.message_id,
        reply_markup=keyboard
    )

async def send_team_building_page(chat_id, heroes, current_page, total_pages, message: types.Message):
    start_index = current_page * HEROES_PER_PAGE
    end_index = start_index + HEROES_PER_PAGE
    page_heroes = heroes[start_index:end_index]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=hero[0], callback_data=f"hero_{hero[0]}")] for hero in page_heroes
    ])

    navigation_buttons = []
    if current_page > 0:
        navigation_buttons.append(InlineKeyboardButton(text="◀ Назад", callback_data=f"page_{current_page - 1}"))
    if current_page < total_pages - 1:
        navigation_buttons.append(InlineKeyboardButton(text="Вперед ▶", callback_data=f"page_{current_page + 1}"))

    if navigation_buttons:
        keyboard.inline_keyboard.append(navigation_buttons)

    menu_button = InlineKeyboardButton(text="Главное меню", callback_data="start_menu")
    keyboard.inline_keyboard.append([menu_button])

    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=message.message_id,
        text="Выберите героя для своей команды (до 5 героев):",
        reply_markup=keyboard
    )

async def edit_or_send_team_message(message: types.Message, new_text: str):
    if message.reply_to_message:
        await bot.edit_message_text(
            text=new_text,
            chat_id=message.chat.id,
            message_id=message.message_id
        )
    else:
        await bot.send_message(
            chat_id=message.chat.id,
            text=new_text
        )

if __name__ == "__main__":
    import asyncio

    try:
        logger.info("Бот запускается...")
        asyncio.run(dp.start_polling(bot))
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")
