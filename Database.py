import sqlite3
from datetime import datetime, timedelta

DB_NAME = 'Database.db'

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    """Инициализация БД. Вызывается один раз при старте."""
    con = get_connection()
    cursor = con.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Ucheniks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        uchenik TEXT NOT NULL,
        price_per_hour REAL,
        hours REAL DEFAULT 0,
        hours_spend REAL DEFAULT 0,
        date_recorded DATE DEFAULT CURRENT_DATE
    )
    ''')
    # Индекс ускоряет поиск учеников конкретного пользователя в сотни раз
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON Ucheniks(user_id)')
    con.commit()
    con.close()

# Запускаем инициализацию при импорте модуля
init_db()

def get_all_students(user_id: int):
    con = get_connection()
    cursor = con.cursor()
    cursor.execute("SELECT id, uchenik, price_per_hour, hours_spend FROM Ucheniks WHERE user_id = ?", (user_id,))
    students = cursor.fetchall()
    con.close()
    return students

def get_students_for_button(user_id: int):
    con = get_connection()
    cursor = con.cursor()
    cursor.execute("SELECT id, uchenik FROM Ucheniks WHERE user_id = ?", (user_id,))
    students = cursor.fetchall()
    con.close()
    return students

def get_student_name(user_id: int, student_id: int):
    con = get_connection()
    cursor = con.cursor()
    cursor.execute("SELECT uchenik FROM Ucheniks WHERE id = ? AND user_id = ?", (student_id, user_id))
    result = cursor.fetchone()
    con.close()
    return result[0] if result else "Неизвестный"

def update_hours_spend(user_id: int, student_id: int, hours: float):
    con = get_connection()
    cursor = con.cursor()
    cursor.execute(
        "UPDATE Ucheniks SET hours_spend = COALESCE(hours_spend,0) + ?, date_recorded = ? WHERE id = ? AND user_id = ?",
        (hours, datetime.now().strftime("%Y-%m-%d"), student_id, user_id))
    con.commit()
    con.close()

def get_weekly_report(user_id: int):
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    con = get_connection()
    cursor = con.cursor()
    cursor.execute('''
        SELECT uchenik, SUM(hours_spend) as total_hours, price_per_hour, SUM(hours_spend * price_per_hour) as total_income
        FROM Ucheniks
        WHERE user_id = ? AND date(date_recorded) BETWEEN ? AND ?
        GROUP BY uchenik
    ''', (user_id, start_of_week.strftime('%Y-%m-%d'), end_of_week.strftime('%Y-%m-%d')))
    report_data = cursor.fetchall()
    con.close()
    return report_data, start_of_week, end_of_week

def delete_student(user_id: int, student_id: int):
    con = get_connection()
    cursor = con.cursor()
    cursor.execute("DELETE FROM Ucheniks WHERE id = ? AND user_id = ?", (student_id, user_id))
    con.commit()
    rowcount = cursor.rowcount
    con.close()
    return rowcount

def add_student(user_id: int, name: str, price: float, hours: float = 0):
    con = get_connection()
    cursor = con.cursor()
    cursor.execute("INSERT INTO Ucheniks(user_id, uchenik, price_per_hour, hours) VALUES(?,?,?,?)",
                   (user_id, name, price, hours))
    con.commit()
    con.close()


def get_all_users_summary():
    """Возвращает список всех пользователей с общей статистикой."""
    con = get_connection()
    cursor = con.cursor()
    cursor.execute('''
        SELECT user_id,
               COUNT(id) as student_count,
               COALESCE(SUM(hours_spend), 0) as total_hours,
               COALESCE(SUM(hours_spend * price_per_hour), 0) as total_income
        FROM Ucheniks
        GROUP BY user_id
        ORDER BY total_income DESC
    ''')
    users = cursor.fetchall()
    con.close()
    return users

def get_user_detailed_stats(user_id: int):
    """Возвращает подробную статистику по конкретному пользователю."""
    con = get_connection()
    cursor = con.cursor()
    # Общая сводка
    cursor.execute('''
        SELECT COUNT(id) as student_count,
               COALESCE(SUM(hours_spend), 0) as total_hours,
               COALESCE(SUM(hours_spend * price_per_hour), 0) as total_income
        FROM Ucheniks WHERE user_id = ?
    ''', (user_id,))
    summary = cursor.fetchone()

    # Детализация по ученикам
    cursor.execute('''
        SELECT id, uchenik, price_per_hour, hours_spend, (hours_spend * price_per_hour) as income
        FROM Ucheniks WHERE user_id = ?
        ORDER BY hours_spend DESC
    ''', (user_id,))
    students = cursor.fetchall()
    con.close()
    return summary, students