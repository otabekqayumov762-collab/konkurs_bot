from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_contact_keyboard() -> ReplyKeyboardMarkup:
    """Returns a reply keyboard to request user contact."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Kontaktni yuborish", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

def get_yes_no_keyboard() -> ReplyKeyboardMarkup:
    """Returns a reply keyboard with To'lov qilaman/To'lov qilmayman buttons."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="To'lov qilaman"), KeyboardButton(text="To'lov qilmayman")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard


