import sqlite3
from datetime import datetime, timedelta

con = sqlite3.connect('Database.db')
cursor = con.cursor()

# Первичное создание БД
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Ucheniks(
        id INTEGER PRIMARY KEY,
        uchenik TEXT NOT NULL,
        price_per_hour INTEGER,
        hours INTEGER,
        hours_spend INTEGER,
        date_recorded DATE DEFAULT CURRENT_DATE) 
''')
con.commit()
con.close()

def DB_uch(name): #Вызов имени ученика
    cur = sqlite3.connect('Database.db')
    curr = cur.execute("SELECT uchenik FROM Ucheniks WHERE uchenik=?",(name)).fetchone()
    if curr is None:
        cur.close()
        return None
    else:
        cur.close()
        idt = curr[0]
        return idt

#Сбор учеников для аналитики
def get_all_students():
    con = sqlite3.connect('Database.db')
    cursor = con.cursor()
    cursor.execute("SELECT id, uchenik, price_per_hour, hours FROM Ucheniks")
    students = cursor.fetchall()
    con.close()
    return students  # Возвращает список вида (id, uchenik,price_per_hour,hours)

#Сбор всех учеников в inline-кнопку
def get_students_for_button():
    con = sqlite3.connect('Database.db')
    cursor = con.cursor()
    cursor.execute("SELECT id, uchenik FROM Ucheniks")
    students = cursor.fetchall()
    con.close()
    return students  # Возвращает список вида (id, name)

def update_hours_spend(student_id, hours):
    con = sqlite3.connect('Database.db')
    cursor = con.cursor()
    cursor.execute(
        "UPDATE Ucheniks SET hours_spend = COALESCE(hours_spend,0) + ? WHERE id = ?",
        (hours, student_id))
    con.commit()
    con.close()

def get_weekly_report():
    # Рассчитываем даты начала и конца недели
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    con = sqlite3.connect('Database.db')
    cursor = con.cursor()
    
    # Получаем данные за неделю
    cursor.execute('''
        SELECT 
            uchenik, 
            SUM(hours_spend) as total_hours, 
            price_per_hour,
            SUM(hours_spend * price_per_hour) as total_income
        FROM Ucheniks
        WHERE date(date_recorded) BETWEEN ? AND ?
        GROUP BY uchenik
    ''', (start_of_week.strftime('%Y-%m-%d'), end_of_week.strftime('%Y-%m-%d')))
    
    report_data = cursor.fetchall()
    con.close()
    return report_data, start_of_week, end_of_week

def delete_student(student_id):
    con = sqlite3.connect('Database.db')
    cursor = con.cursor()
    cursor.execute("DELETE FROM Ucheniks WHERE id = ?", (student_id,))
    con.commit()
    con.close()
    return cursor.rowcount  # Вернём количество удалённых строк