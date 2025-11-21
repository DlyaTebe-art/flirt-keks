# handlers/create_ad.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import os
from database import SessionLocal, Ad

create_ad_router = Router()

MODERATOR_ID = int(os.getenv("MODERATOR_CHAT_ID"))

# Стани FSM
class Form(StatesGroup):
    ad_type = State()           # Анонімне / Публічне
    name = State()              # Імʼя
    gender = State()            # Стать
    age = State()               # Вік
    text = State()              # Текст оголошення
    interested_in = State()     # Хто цікавить
    photo = State()             # Фото
    username = State()          # Telegram нік

# Кнопка "Спочатку"
start_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="/start")]],
    resize_keyboard=True,
    one_time_keyboard=True
)

# --- Старт ---
@create_ad_router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Подати оголошення"), KeyboardButton(text="Переглянути оголошення")]
        ],
        resize_keyboard=True
    )
    await message.answer("Виберіть дію:", reply_markup=kb)

# --- Вибір дії ---
@create_ad_router.message(F.text == "Подати оголошення")
async def choose_ad_type(message: Message, state: FSMContext):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Анонімне"), KeyboardButton(text="Публічне")],
            [KeyboardButton(text="/start")]
        ],
        resize_keyboard=True
    )
    await message.answer("Виберіть тип оголошення:", reply_markup=kb)
    await state.set_state(Form.ad_type)

@create_ad_router.message(Form.ad_type)
async def process_ad_type(message: Message, state: FSMContext):
    await state.update_data(ad_type=message.text)
    await message.answer("Вкажіть ваше ім’я:", reply_markup=start_kb)
    await state.set_state(Form.name)

# --- Імʼя ---
@create_ad_router.message(Form.name)
async def process_name(message: Message, state: FSMContext):
    if not message.text.isalpha():
        await message.answer("Імʼя має містити тільки літери.")
        return
    await state.update_data(name=message.text)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Чоловік"), KeyboardButton(text="Жінка")],
            [KeyboardButton(text="/start")]
        ],
        resize_keyboard=True
    )
    await message.answer("Вкажіть вашу стать:", reply_markup=kb)
    await state.set_state(Form.gender)

# --- Стать ---
@create_ad_router.message(Form.gender)
async def process_gender(message: Message, state: FSMContext):
    await state.update_data(gender=message.text)
    await message.answer("Вкажіть ваш вік від 18 до 100:", reply_markup=start_kb)
    await state.set_state(Form.age)

# --- Вік ---
@create_ad_router.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    if not message.text.isdigit() or not (18 <= int(message.text) <= 100):
        await message.answer("Вік повинен бути числом від 18 до 100.")
        return
    await state.update_data(age=int(message.text))
    await message.answer("Текст оголошення (мінімум 20 символів):", reply_markup=start_kb)
    await state.set_state(Form.text)

# --- Текст оголошення ---
@create_ad_router.message(Form.text)
async def process_text(message: Message, state: FSMContext):
    if len(message.text) < 20:
        await message.answer("Текст має бути мінімум 20 символів.")
        return
    await state.update_data(text=message.text)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Чоловік"), KeyboardButton(text="Жінка")],
            [KeyboardButton(text="Пара"), KeyboardButton(text="Будь хто")],
            [KeyboardButton(text="/start")]
        ],
        resize_keyboard=True
    )
    await message.answer("Хто цікавить?", reply_markup=kb)
    await state.set_state(Form.interested_in)

# --- Хто цікавить ---
@create_ad_router.message(Form.interested_in)
async def process_interested(message: Message, state: FSMContext):
    await state.update_data(interested_in=message.text)
    await message.answer("Завантажте фото або натисніть /skip", reply_markup=start_kb)
    await state.set_state(Form.photo)

# --- Фото ---
@create_ad_router.message(Form.photo, F.content_type.in_({"photo", "text"}))
async def process_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photo_id = None
    if message.photo:
        photo_id = message.photo[-1].file_id
    elif message.text != "/skip":
        await message.answer("Будь ласка, надішліть фото або натисніть /skip")
        return
    await state.update_data(photo_id=photo_id)
    await message.answer("Вкажіть ваш @username, якщо бажаєте опублікувати анонімно натисніть /skip", reply_markup=start_kb)
    await state.set_state(Form.username)

# --- Telegram нік ---
@create_ad_router.message(Form.username)
async def process_username(message: Message, state: FSMContext):
    data = await state.get_data()
    username = message.text if message.text != "/skip" else None

    # Збереження оголошення
    async with SessionLocal() as session:
        ad = Ad(
            user_id=message.from_user.id,
            name=data["name"],
            age=data["age"],
            gender=data["gender"],
            interested_in=data["interested_in"],
            about=data["text"],
            photo_id=data.get("photo_id"),
            tg_username=username,
            ad_type=data["ad_type"],
            status="pending"
        )
        session.add(ad)
        await session.commit()
        await session.refresh(ad)

    await state.clear()
    await message.answer("Ваше оголошення надіслано на модерацію ✅", reply_markup=start_kb)

    # Модератор повідомлення
    await create_ad_router.bot.send_message(
        MODERATOR_ID,
        f"Нове оголошення #{ad.id}\n"
        f"Імʼя: {ad.name}\n"
        f"Вік: {ad.age}\n"
        f"Стать: {ad.gender}\nХто цікавить: {ad.interested_in}\nТекст: {ad.about}\nTelegram: @{username if username else 'анонім'}"
    )
    if photo_id:
        await create_ad_router.bot.send_photo(MODERATOR_ID, photo_id)
