from aiogram import F, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from kb import kb_main, kb_red_urok, kb_uch, generate_students_keyboard, get_confirmation_keyboard, kb_admin_menu, generate_admin_users_keyboard
from Database import (
    get_all_students, get_weekly_report, update_hours_spend,
    delete_student, add_student, get_student_name
)
from datetime import datetime

msg = Dispatcher()

ADMIN_ID = #Сюда ID

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

class StudentState(StatesGroup):
    waiting_hours = State()
    waiting_add_data = State()
    waiting_delete_selection = State()
    waiting_delete_confirmation = State()

def get_user_id(update: types.Message | types.CallbackQuery) -> int:
    return update.from_user.id

@msg.callback_query(F.data.startswith("student_"))
async def student_selected(callback: types.CallbackQuery, state: FSMContext):
    user_id = get_user_id(callback)
    student_id = callback.data.split("_")[1]
    await state.update_data(student_id=student_id, user_id=user_id)
    await state.set_state(StudentState.waiting_hours)
    await callback.message.answer("Введите количество часов:", reply_markup=kb_red_urok)
    await callback.answer()

@msg.message(StudentState.waiting_hours)
async def process_hours(message: types.Message, state: FSMContext):
    try:
        hours = float(message.text)
        data = await state.get_data()
        student_id = data["student_id"]
        user_id = data["user_id"]

        update_hours_spend(user_id, student_id, hours)
        await message.answer("✅ Часы добавлены!", reply_markup=kb_main)
    except ValueError:
        await message.answer("❌ Ошибка! Введите число:")
    finally:
        await state.clear()

@msg.message(Command('start'))
async def start_command(message: types.Message) -> None:
    await message.answer('Ведомость твоих занятий', reply_markup=kb_main)

@msg.message(F.text == 'Список учеников')
async def uchenik_handler(message: types.Message) -> None:
    user_id = get_user_id(message)
    students = get_all_students(user_id)
    if not students:
        await message.answer("Список учеников пуст", reply_markup=kb_main)
        return

    students_list = "\n".join([
        f"{num}. {name} | Цена: {price}/час | Часов: {hours} | Сумма: {price*hours:.2f}"
        for num, (id, name, price, hours) in enumerate(students, 1)
    ])
    await message.answer(f"📚 Список учеников:\n{students_list}", reply_markup=kb_main)

@msg.message(F.text == 'Записать')
async def reg_handler(message: types.Message) -> None:
    user_id = get_user_id(message)
    keyboard = await generate_students_keyboard(user_id)
    await message.answer('Выберите кого отметить:', reply_markup=keyboard)

@msg.message(F.text == 'Назад')
async def back_handler(message: types.Message) -> None:
    await message.answer('Главное меню:', reply_markup=kb_main)

@msg.message(F.text == 'Ученики')
async def students_menu_handler(message: types.Message) -> None:
    await message.answer('Редакция учеников:', reply_markup=kb_uch)

@msg.message(F.text == 'Добавить ученика')
async def add_handler(message: types.Message, state: FSMContext) -> None:
    await message.answer('Введите данные в формате:\n`Имя Цена_в_час`\nНапример: `Иван 1500`', parse_mode="Markdown", reply_markup=kb_red_urok)
    await state.set_state(StudentState.waiting_add_data)

@msg.message(StudentState.waiting_add_data)
async def write_handler(message: types.Message, state: FSMContext):
    parts = message.text.split()
    if len(parts) >= 2:
        name = parts[0]
        try:
            price = float(parts[1])
            user_id = get_user_id(message)
            add_student(user_id, name, price)
            await message.answer('✅ Ученик добавлен!', reply_markup=kb_main)
        except ValueError:
            await message.answer('❌ Цена должна быть числом. Попробуйте снова.')
            return
    else:
        await message.answer('❌ Неверный формат. Используйте: Имя Цена')
        return
    await state.clear()

@msg.message(F.text == 'Недельный отчёт')
async def weekly_report_handler(message: types.Message):
    user_id = get_user_id(message)
    report_data, start_date, end_date = get_weekly_report(user_id)

    if not report_data:
        await message.answer("❌ За эту неделю занятий не было", reply_markup=kb_main)
        return

    total_income = 0.0
    total_hours = 0.0
    report_text = f"📊 Отчёт за неделю:\n{start_date.strftime('%d.%m')}-{end_date.strftime('%d.%m.%Y')}\n\n"

    for student in report_data:
        name, hours, price, income = student
        report_text += f"👤 {name}:\n"
        report_text += f"   ⏱ Часов: {hours:.1f}\n"
        report_text += f"   💰 Сумма: {income:.2f} руб.\n"
        report_text += f"   📊 Цена часа: {price} руб./час\n\n"
        total_income += income
        total_hours += hours

    avg_price = total_income / total_hours if total_hours > 0 else 0
    report_text += "══════════════════\n"
    report_text += f"Итого:\n"
    report_text += f"⏱ Всего часов: {total_hours:.1f}\n"
    report_text += f"💰 Общий доход: {total_income:.2f} руб.\n"
    report_text += f"📊 Средняя цена часа: {avg_price:.2f} руб./час"

    await message.answer(report_text, reply_markup=kb_main)

@msg.message(F.text == 'Удалить ученика')
async def delete_student_handler(message: types.Message, state: FSMContext):
    user_id = get_user_id(message)
    keyboard = await generate_students_keyboard(user_id, prefix="delete")
    await message.answer('Выберите ученика для удаления:', reply_markup=keyboard)
    await state.update_data(user_id=user_id)
    await state.set_state(StudentState.waiting_delete_selection)

@msg.callback_query(F.data.startswith("delete_"), StudentState.waiting_delete_selection)
async def student_selected_for_deletion(callback: types.CallbackQuery, state: FSMContext):
    user_id = get_user_id(callback)
    student_id = callback.data.split("_")[1]
    await state.update_data(student_id=student_id)

    student_name = get_student_name(user_id, student_id)
    keyboard = get_confirmation_keyboard(student_id)
    await callback.message.answer(f"Вы уверены, что хотите удалить ученика {student_name}?", reply_markup=keyboard)
    await callback.answer()
    await state.set_state(StudentState.waiting_delete_confirmation)

@msg.callback_query(F.data.startswith("confirm_delete_"), StudentState.waiting_delete_confirmation)
async def confirm_deletion(callback: types.CallbackQuery, state: FSMContext):
    user_id = get_user_id(callback)
    student_id = callback.data.split("_")[2]
    deleted_count = delete_student(user_id, student_id)

    if deleted_count > 0:
        await callback.message.answer("✅ Ученик успешно удалён!", reply_markup=kb_main)
    else:
        await callback.message.answer("❌ Не удалось удалить ученика", reply_markup=kb_main)

    await callback.answer()
    await state.clear()

@msg.callback_query(F.data == "cancel_delete")
async def cancel_deletion(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("❌ Удаление отменено", reply_markup=kb_main)
    await callback.answer()
    await state.clear()

@msg.message(Command('admin'))
async def admin_command(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ к админ-панели запрещён.")
        return
    await message.answer("🛠 Админ-панель:", reply_markup=kb_admin_menu)

@msg.message(F.text == "👥 Список пользователей")
async def admin_users_list(message: types.Message):
    if not is_admin(message.from_user.id): return
    keyboard = await generate_admin_users_keyboard()
    await message.answer("Выберите пользователя для просмотра статистики:", reply_markup=keyboard)

@msg.callback_query(F.data.startswith("admin_detail_"))
async def admin_user_detail(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    user_id = int(callback.data.split("_")[2])
    from Database import get_user_detailed_stats
    
    summary, students = get_user_detailed_stats(user_id)
    if not summary or summary[0] == 0:
        await callback.answer("Нет данных")
        return

    total_students, total_hours, total_income = summary
    text = f"👤 <b>Статистика пользователя {user_id}</b>:\n"
    text += f"📚 Учеников: <b>{total_students}</b>\n"
    text += f"⏱ Всего часов: <b>{total_hours:.1f}</b>\n"
    text += f"💰 Общий доход: <b>{total_income:.2f} ₽</b>\n\n"
    text += "📋 <b>Детализация по ученикам:</b>\n"

    for s_id, name, price, hours, income in students:
        text += f"• <i>{name}</i> | {hours:.1f}ч | {income:.2f}₽\n"

    kb_back = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔙 Назад к списку", callback_data="admin_back_to_list")
    ]])

    await callback.message.answer(text, reply_markup=kb_back, parse_mode="HTML")
    await callback.answer()

@msg.callback_query(F.data == "admin_back_to_list")
async def admin_back_to_list(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    keyboard = await generate_admin_users_keyboard()
    await callback.message.edit_text("Выберите пользователя:", reply_markup=keyboard)
    await callback.answer()

@msg.message(F.text == "🔙 В главное меню")
async def admin_back_to_main(message: types.Message):
    if not is_admin(message.from_user.id): return
    await message.answer("Главное меню:", reply_markup=kb_main)