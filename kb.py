from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from Database import get_students_for_button

kb_main = types.ReplyKeyboardMarkup(keyboard=[
    [types.KeyboardButton(text="Записать")],
    [types.KeyboardButton(text="Ученики"), types.KeyboardButton(text="Список учеников")],
    [types.KeyboardButton(text="Недельный отчёт")]
], resize_keyboard=True)

kb_uch = types.ReplyKeyboardMarkup(keyboard=[
    [types.KeyboardButton(text="Добавить ученика"), types.KeyboardButton(text="Удалить ученика"), types.KeyboardButton(text="Назад")]
], resize_keyboard=True)

kb_red_urok = types.ReplyKeyboardMarkup(keyboard=[
    [types.KeyboardButton(text="Назад")]
], resize_keyboard=True)

async def generate_students_keyboard(user_id: int, prefix: str = "student"):
    students = get_students_for_button(user_id)
    buttons = []
    for student in students:
        student_id, student_name = student
        buttons.append([
            InlineKeyboardButton(
                text=student_name,
                callback_data=f"{prefix}_{student_id}"
            )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirmation_keyboard(student_id: int):
    buttons = [[
        InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_{student_id}"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_delete")
    ]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


kb_admin_menu = types.ReplyKeyboardMarkup(keyboard=[
    [types.KeyboardButton(text="👥 Список пользователей")],
    [types.KeyboardButton(text="🔙 В главное меню")]
], resize_keyboard=True)

async def generate_admin_users_keyboard():
    from Database import get_all_users_summary
    users = get_all_users_summary()
    buttons = []
    for user_id, count, hours, income in users:
        buttons.append([
            InlineKeyboardButton(
                text=f"🆔 {user_id} | 👤 {count} уч.",
                callback_data=f"admin_detail_{user_id}"
            )
        ])
    if not buttons:
        buttons.append([InlineKeyboardButton(text="Пользователей нет", callback_data="admin_noop")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)