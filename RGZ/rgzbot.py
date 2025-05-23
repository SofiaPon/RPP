import os
import logging
from dotenv import load_dotenv
import psycopg2
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
from datetime import datetime  

#загрузка переменных окружения
load_dotenv()

#настройка логирования
logging.basicConfig(level=logging.INFO)

#инициализация бота и диспетчера
bot = Bot(token=os.getenv('API_TOKEN'))
dp = Dispatcher()

#словарь для хранения временных данных операций
operation_data = {}

#подключение к базе данных
def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST')
    )

#создание таблиц
def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT UNIQUE,
            username TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS operations (
            id SERIAL PRIMARY KEY,
            date TEXT,
            amount FLOAT,
            chat_id BIGINT,
            operation_type TEXT
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

#проверка регистрации пользователя
def is_user_registered(chat_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE chat_id = %s", (chat_id,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists

#/start
@dp.message(Command('start'))
async def start(message: types.Message):
    await message.answer(
        "Привет! Я бот для учета финансов.\n"
        "Доступные команды:\n"
        "/reg - регистрация\n"
        "/add_operation - добавить операцию\n"
        "/operations - список операций\n"
        "/delete_operation - удалить операцию по ID"
    )

#/reg
@dp.message(Command('reg'))
async def register(message: types.Message):
    if is_user_registered(message.chat.id):
        await message.answer("Вы уже зарегистрированы!")
        return
    
    await message.answer("Введите ваш логин:")

# Обработчик ввода логина (для незарегистрированных пользователей)
@dp.message(lambda message: not message.text.startswith('/') and not is_user_registered(message.chat.id))
async def process_username(message: types.Message):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (chat_id, username) VALUES (%s, %s)", 
                   (message.chat.id, message.text))
        conn.commit()
        await message.answer("Регистрация завершена!")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")
    finally:
        cur.close()
        conn.close()

#/add_operation
@dp.message(Command('add_operation'))
async def add_operation(message: types.Message):
    if not is_user_registered(message.chat.id):
        await message.answer("Сначала зарегистрируйтесь с помощью /reg")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ДОХОД", callback_data="income"),
         InlineKeyboardButton(text="РАСХОД", callback_data="expense")]
    ])
    await message.answer("Выберите тип операции:", reply_markup=keyboard)

#выбор типа операции (колбэк)
@dp.callback_query(lambda c: c.data in ["income", "expense"])
async def process_operation_type(callback: types.CallbackQuery):
    operation_type = "ДОХОД" if callback.data == "income" else "РАСХОД"
    operation_data[callback.message.chat.id] = {"type": operation_type}
    await callback.message.answer("Введите сумму операции в рублях:")
    await callback.answer()

#ввод суммы операции
@dp.message(lambda message: message.text.replace('.', '', 1).isdigit() and message.chat.id in operation_data)
async def process_amount(message: types.Message):
    operation_data[message.chat.id]["amount"] = float(message.text)
    await message.answer("Введите дату операции (формат: ГГГГ-ММ-ДД):")

#ввод даты операции
@dp.message(lambda message: message.chat.id in operation_data and "amount" in operation_data[message.chat.id])
async def process_date(message: types.Message):
    try:
        #проверка корректности даты
        date = datetime.strptime(message.text, "%Y-%m-%d").date()
        chat_id = message.chat.id
        op_type = operation_data[chat_id]["type"]
        amount = operation_data[chat_id]["amount"]
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO operations (date, amount, chat_id, operation_type) VALUES (%s, %s, %s, %s)",
            (date, amount, chat_id, op_type)
        )
        conn.commit()
        
        await message.answer("Операция добавлена!")
        operation_data.pop(chat_id, None)
    except ValueError:
        await message.answer("Некорректный формат даты. Пожалуйста, введите дату в формате ГГГГ-ММ-ДД.")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

#/operations
@dp.message(Command('operations'))
async def list_operations(message: types.Message):
    if not is_user_registered(message.chat.id):
        await message.answer("Сначала зарегистрируйтесь с помощью /reg")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="RUB", callback_data="currency_RUB"),
         InlineKeyboardButton(text="EUR", callback_data="currency_EUR"),
         InlineKeyboardButton(text="USD", callback_data="currency_USD")]
    ])
    await message.answer("Выберите валюту для отображения операций:", reply_markup=keyboard)

#выбор валюты (колбэк)
@dp.callback_query(lambda c: c.data.startswith("currency_"))
async def show_operations(callback: types.CallbackQuery):
    currency = callback.data.split("_")[1]
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        #получение текущего курса валюты с сервера
        import requests
        try:
            response = requests.get(f"http://localhost:5000/rate?currency={currency}")
            if response.status_code != 200:
                raise Exception(f"Не удалось получить курс валюты. Код ошибки: {response.status_code}")
            rate_data = response.json()
            rate = rate_data['rate']
        except Exception as e:
            await callback.message.answer(f"Ошибка при получении курса валюты: {e}")
            await callback.answer()
            return

        cur.execute("SELECT id, date, amount, operation_type FROM operations WHERE chat_id = %s", (callback.message.chat.id,))
        ops = cur.fetchall()
        
        if not ops:
            await callback.message.answer("Операций нет")
            await callback.answer()
            return
            
        response = f"Ваши операции ({currency}):\n"
        for op in ops:
            amount_rub = op[2]
            #конвертация
            converted_amount = round(amount_rub / rate, 2)
            response += f"{op[0]}. {op[3]} {converted_amount} {currency} ({op[1]})\n"
        
        await callback.message.answer(response)
        await callback.answer()
    except Exception as e:
        await callback.message.answer(f"Ошибка: {e}")
        await callback.answer()
    finally:
        cur.close()
        conn.close()

#/delete_operation
@dp.message(Command('delete_operation'))
async def delete_operation(message: types.Message):
    if not is_user_registered(message.chat.id):
        await message.answer("Сначала зарегистрируйтесь с помощью /reg")
        return
    
    #получение списка операций
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, date, amount, operation_type FROM operations WHERE chat_id = %s", (message.chat.id,))
        ops = cur.fetchall()
        
        if not ops:
            await message.answer("У вас нет операций для удаления")
            return
            
        response = "Ваши операции (укажите ID для удаления):\n"
        for op in ops:
            response += f"{op[0]}. {op[3]} {op[2]} RUB ({op[1]})\n"
        
        await message.answer(response + "\nВведите ID операции для удаления:")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")
    finally:
        cur.close()
        conn.close()

#ввод ID операции для удаления
@dp.message(lambda message: message.text.isdigit())
async def process_delete_operation(message: types.Message):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        operation_id = int(message.text)
        chat_id = message.chat.id
        
        #проверка на принадлежность операции пользователю
        cur.execute("SELECT id FROM operations WHERE id = %s AND chat_id = %s", (operation_id, chat_id))
        if not cur.fetchone():
            await message.answer("Операция с таким ID не найдена или не принадлежит вам")
            return
        
        #удаление
        cur.execute("DELETE FROM operations WHERE id = %s AND chat_id = %s", (operation_id, chat_id))
        conn.commit()
        
        if cur.rowcount > 0:
            await message.answer(f"Операция {operation_id} успешно удалена")
        else:
            await message.answer("Не удалось удалить операцию")
    except ValueError:
        await message.answer("Пожалуйста, введите числовой ID операции")
    except Exception as e:
        await message.answer(f"Ошибка при удалении: {e}")
    finally:
        cur.close()
        conn.close()

#запуска бота
async def main():
    create_tables()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())