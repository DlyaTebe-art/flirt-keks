from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_create_ad_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Публічне", callback_data="public"),
        InlineKeyboardButton("Анонімне", callback_data="anonymous")
    )
    return keyboard
