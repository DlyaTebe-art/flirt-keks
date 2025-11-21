from aiogram import Router, F, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import os
import sqlite3

# --- Налаштування ---
DB_PATH = os.getenv("DB_PATH", "db.sqlite3")
MODERATOR_ID = int(os.getenv("MODERATOR_CHAT_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

create_ad_router = Router()

# --- FSM ---
class Form(StatesGroup):
    anonymity = State()
    name = State()
    gender = State()
    age = State()
    ad_text = State()
    interested_in = State()
    photo = State()
    username = State()

# --- Клавіатури ---
def reply_keyboard(buttons_list):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=b)] for b in buttons_list] + [[KeyboardButton("/start")]],
        resize_keyboard=True
    )
    return kb

# --- Підключення до БД ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS ads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        anonymity TEXT,
        name TEXT,
        gender TEXT,
        age INTEGER,
        ad_text TEXT,
        interested_in TEXT,
        photo TEXT,
        username TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

def save_ad_to_db(data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO ads (anonymity, name, gender, age, ad_text, interested_in, photo, username)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["anonymity"], data["name"], data["gender"], data["age"],
        data["ad_text"], data["interested_in"], data["photo"], data["username"]
    ))
    conn.commit()
    conn.close()

# --- Старт ---
@create_ad_router.message(Command(commands=["start"]))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    kb = reply_keyboard(["Подати оголошення", "Переглянути оголошення"])
    await message.answer("👋 Вітаю! Оберіть дію:", reply_markup=kb)

# --- Подати оголошення ---
@create_ad_router.message(F.text=="Подати оголошення")
async def choose_anonymity(message: types.Message, state: FSMContext):
    kb = reply_keyboard(["Анонімне", "Публічне"])
    await message.answer("Оберіть тип оголошення:", reply_markup=kb)
    await state.set_state(Form.anonymity)

@create_ad_router.message(F.text.in_({"Анонімне", "Публічне"}))
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(anonymity=message.text)
    await message.answer("👉 Вкажіть ваше ім’я (обов’язково)")
    await state.set_state(Form.name)

@create_ad_router.message(Form.name)
async def get_gender(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    kb = reply_keyboard(["Чоловік", "Жінка"])
    await message.answer("Вкажіть вашу стать:", reply_markup=kb)
    await state.set_state(Form.gender)

@create_ad_router.message(Form.gender)
async def get_age(message: types.Message, state: FSMContext):
    await state.update_data(gender=message.text)
    await message.answer("Вкажіть ваш вік (18-100):")
    await state.set_state(Form.age)

@create_ad_router.message(Form.age)
async def get_ad_text(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or not (18 <= int(message.text) <= 100):
        await message.answer("Вік має бути числом від 18 до 100. Спробуйте ще раз.")
        return
    await state.update_data(age=int(message.text))
    await message.answer("Введіть текст оголошення (мінімум 20 символів):")
    await state.set_state(Form.ad_text)

@create_ad_router.message(Form.ad_text)
async def get_interested_in(message: types.Message, state: FSMContext):
    if len(message.text) < 20:
        await message.answer("Текст оголошення занадто короткий, мінімум 20 символів.")
        return
    await state.update_data(ad_text=message.text)
    kb = reply_keyboard(["Чоловік", "Жінка", "Пара", "Будь-хто"])
    await message.answer("Хто вас цікавить?", reply_markup=kb)
    await state.set_state(Form.interested_in)

@create_ad_router.message(Form.interested_in)
async def get_photo(message: types.Message, state: FSMContext):
    await state.update_data(interested_in=message.text)
    await message.answer("Завантажте фото або натисніть /skip")
    await state.set_state(Form.photo)

@create_ad_router.message(Form.photo)
async def get_username(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.text)
    await message.answer("Вкажіть ваш @username (або /skip для анонімності)")
    await state.set_state(Form.username)

# --- Пропуск фото ---
@create_ad_router.message(F.text=="/skip", state=Form.photo)
async def skip_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo=None)
    await message.answer("Вкажіть ваш @username (або /skip для анонімності)")
    await state.set_state(Form.username)

# --- Пропуск username ---
@create_ad_router.message(F.text=="/skip", state=Form.username)
async def skip_username(message: types.Message, state: FSMContext):
    await state.update_data(username=None)
    data = await state.get_data()
    await finalize_ad(message, data)
    await state.clear()

# --- Введений username ---
@create_ad_router.message(Form.username)
async def finish_ad(message: types.Message, state: FSMContext):
    data = await state.get_data()
    data["username"] = message.text
    await finalize_ad(message, data)
    await state.clear()

# --- Функція фіналізації ---
async def finalize_ad(message: types.Message, data: dict):
    save_ad_to_db(data)
    
    # Формуємо текст оголошення
    username_line = f"\n@{data['username']}" if data.get("username") else "\n(анонім)"
    preview = (
        f"{data['name']}{username_line}\n"
        f"Стать: {data['gender']}\n"
        f"Вік: {data['age']}\n"
        f"Текст: {data['ad_text']}\n"
        f"Цікавить: {data['interested_in']}\n"
        f"Фото: {data['photo'] or 'немає'}"
    )
    
    # Відправка модератору та в канал
    await message.bot.send_message(MODERATOR_ID, f"🔔 Нове оголошення:\n\n{preview}")
    await message.bot.send_message(CHANNEL_ID, f"Нове оголошення:\n\n{preview}")
    
    # Відповідь користувачу
    await message.answer("✅ Ваше оголошення готове! Дякуємо за участь.")
