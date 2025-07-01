from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from Database import get_students_for_button
kb_main = [
    [
        types.KeyboardButton(text="Записать")
    ],
    [
        types.KeyboardButton(text="Ученики"),
        types.KeyboardButton(text="Список учеников")
    ],
    [
        types.KeyboardButton(text="Недельный отчёт") 
    ]
]

kb_uch = [
    [
        types.KeyboardButton(text="Добавить ученика"),
        types.KeyboardButton(text="Удалить ученика"),
        types.KeyboardButton(text="Назад")
    ]
]

kb_red_urok = [
    [
        types.KeyboardButton(text="Назад")
    ]
]

kb_main = types.ReplyKeyboardMarkup(keyboard=kb_main, resize_keyboard=True)
kb_uch = types.ReplyKeyboardMarkup(keyboard=kb_uch, resize_keyboard=True)
kb_red_urok = types.ReplyKeyboardMarkup(keyboard=kb_red_urok, resize_keyboard=True)

async def generate_students_keyboard(prefix="student"):
    students = get_students_for_button()
    buttons = []
    for student in students:
        student_id, student_name = student
        buttons.append([
            InlineKeyboardButton(
                text=student_name,
                callback_data=f"{prefix}_{student_id}"
            )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirmation_keyboard(student_id):
    buttons = [
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_{student_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_delete")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)