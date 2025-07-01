from aiogram import F, Dispatcher, types
from aiogram.filters import Command
import sqlite3 as sq
from datetime import datetime, timedelta
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup

from kb import kb_main, kb_red_urok,kb_uch, generate_students_keyboard
from Database import get_all_students,get_weekly_report

msg = Dispatcher()  # Задаем диспатч на сообщения

class StudentState(StatesGroup):
    waiting_hours = State()

class DeleteState(StatesGroup):
    waiting_selection = State()
    waiting_confirmation = State()

@msg.callback_query(F.data.startswith("student_"))
async def student_selected(callback: types.CallbackQuery, state: FSMContext):
    student_id = callback.data.split("_")[1]
    await state.update_data(student_id=student_id)
    await state.set_state(StudentState.waiting_hours)
    await callback.message.answer(f"Введите количество часов:")
    await callback.answer()

# Обработчик ввода часов
@msg.message(StudentState.waiting_hours)
async def process_hours(message: types.Message, state: FSMContext):
    try:
        hours = float(message.text)
        data = await state.get_data()
        student_id = data["student_id"]
        
        con = sq.connect('Database.db')
        cursor = con.cursor()
        cursor.execute(
            "UPDATE Ucheniks SET hours_spend = COALESCE(hours_spend,0) + ? WHERE id = ?",
            (hours, student_id))
        con.commit()
        con.close()
        
        await message.answer(f"✅ Часы добавлены!", reply_markup=kb_main)
    except ValueError:
        await message.answer("❌ Ошибка! Введите число:")
    finally:
        await state.clear()   

@msg.message(Command('start'))  # оператор старта бота
async def start_command(message: types.Message) -> None:
    await message.answer('Ведомость твоих занятий', reply_markup=kb_main)
    
@msg.message(F.text == 'Список учеников')
async def uchenik_handler(message: types.Message) -> None:
    students = get_all_students()
    # Формируем читаемый список учеников
    if not students:
        await message.answer("Список учеников пуст", reply_markup=kb_main)
        return
    # Создаем текст сообщения
    students_list = "\n".join([f"{num}. {name} (ID: {id}) Цена в час: {price_per_hour} Часы: {hours} Суммарно: {price_per_hour*hours}" for num, (id, name, price_per_hour,hours) in enumerate(students, 1)])
    await message.answer(f"📚 Список учеников:\n{students_list}",reply_markup=kb_main)
  
@msg.message(F.text == 'Записать')
async def reg_handler(message: types.Message) -> None:
    keyboard = await generate_students_keyboard() 
    await message.answer('Выберите кого отметить:', reply_markup=keyboard)

@msg.message(F.text == 'Назад')
async def back_handler(message: types.Message) -> None:
    await message.answer('Главное меню:', reply_markup=kb_main)
    
@msg.message(F.text == 'Ученики')
async def reg_handler(message: types.Message) -> None:
    await message.answer('Редакция учеников:', reply_markup=kb_uch)

'''
Пофиксить мрак с дабл-хендлером
'''
@msg.message(F.text == 'Добавить ученика')
async def add_handler(message: types.Message) -> None:
    await message.answer('Имя ученика|Цена в час|Кол-во часов:')
    @msg.message()
    async def write_handler(message: types.Message) -> None:
        input = message.text.split()
        if input[1].isdigit() and input[2].isdigit():    
            get = [str(input[0]),int(input[1]),int(input[2])]
            con = sq.connect('Database.db')
            con.execute("INSERT OR REPLACE INTO Ucheniks(uchenik, price_per_hour, hours) VALUES(?,?,?)",get)
            con.commit()
            con.close()
            await message.answer('Запись сделана!',reply_markup=kb_main)
        else:
            await message.answer('В Цене или часах содержится символ, перепишите')

@msg.message(StudentState.waiting_hours)
async def process_hours(message: types.Message, state: FSMContext):
    try:
        hours = float(message.text)
        data = await state.get_data()
        student_id = data["student_id"]
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        con = sq.connect('Database.db')
        cursor = con.cursor()
        cursor.execute(
            "UPDATE Ucheniks SET hours_spend = COALESCE(hours_spend,0) + ?, date_recorded = ? WHERE id = ?",
            (hours, current_date, student_id))
        con.commit()
        con.close()
        
        await message.answer(f"✅ Часы добавлены!", reply_markup=kb_main)
    except ValueError:
        await message.answer("❌ Ошибка! Введите число:")
    finally:
        await state.clear()

@msg.message(F.text == 'Недельный отчёт')
async def weekly_report_handler(message: types.Message):
    from Database import get_weekly_report  # Импорт внутри функции чтобы избежать циклических зависимостей
    
    report_data, start_date, end_date = get_weekly_report()
    
    if not report_data:
        await message.answer("❌ За эту неделю занятий не было")
        return
    
    total_income = 0
    total_hours = 0
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

# Обработчик кнопки "Удалить ученика"
@msg.message(F.text == 'Удалить ученика')
async def delete_student_handler(message: types.Message, state: FSMContext):
    from kb import generate_students_keyboard
    
    keyboard = await generate_students_keyboard(prefix="delete")
    await message.answer('Выберите ученика для удаления:', reply_markup=keyboard)
    await state.set_state(DeleteState.waiting_selection)

# Обработчик выбора ученика для удаления
@msg.callback_query(F.data.startswith("delete_"), DeleteState.waiting_selection)
async def student_selected_for_deletion(callback: types.CallbackQuery, state: FSMContext):
    student_id = callback.data.split("_")[1]
    
    # Сохраняем ID ученика в состоянии
    await state.update_data(student_id=student_id)
    
    # Получаем имя ученика для сообщения
    con = sq.connect('Database.db')
    cursor = con.cursor()
    cursor.execute("SELECT uchenik FROM Ucheniks WHERE id = ?", (student_id,))
    student_name = cursor.fetchone()[0]
    con.close()
    
    # Запрашиваем подтверждение
    from kb import get_confirmation_keyboard
    keyboard = get_confirmation_keyboard(student_id)
    await callback.message.answer(
        f"Вы уверены, что хотите удалить ученика {student_name}?",
        reply_markup=keyboard
    )
    await callback.answer()
    await state.set_state(DeleteState.waiting_confirmation)

# Обработчик подтверждения удаления
@msg.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_deletion(callback: types.CallbackQuery, state: FSMContext):
    student_id = callback.data.split("_")[2]
    
    # Удаляем ученика из базы
    from Database import delete_student
    deleted_count = delete_student(student_id)
    
    if deleted_count > 0:
        await callback.message.answer("✅ Ученик успешно удалён!", reply_markup=kb_main)
    else:
        await callback.message.answer("❌ Не удалось удалить ученика", reply_markup=kb_main)
    
    await callback.answer()
    await state.clear()

# Обработчик отмены удаления
@msg.callback_query(F.data == "cancel_delete")
async def cancel_deletion(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("❌ Удаление отменено", reply_markup=kb_main)
    await callback.answer()
    await state.clear()