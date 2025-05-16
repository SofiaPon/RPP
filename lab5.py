import asyncio
import os
import logging
import psycopg2
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from dotenv import load_dotenv

#загрузка переменных окружения
load_dotenv()

#настройка логирования
logging.basicConfig(level=logging.INFO)

#токена бота
API_TOKEN = os.getenv('API_TOKEN')

#подключение к postgresql
DB_NAME = os.getenv('DB_NAME', 'currency_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

#инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

#состояния для FSM
class CurrencyStates(StatesGroup):
    name = State()
    rate = State()
    delete = State()
    update = State()
    new_rate = State()
    convert_currency = State()
    convert_amount = State()

#кнопки для управления валютами
def currency_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Добавить валюту"),
                KeyboardButton(text="Удалить валюту"),
                KeyboardButton(text="Изменить курс валюты"),
            ]
        ],
        resize_keyboard=True
    )
    return keyboard

#функция подключения к базе данных
def db_connection():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        logging.error(f"Ошибка подключения к базе данных: {e}")
        return None

#функция для инициализации базы данных
def init_db():
    conn = None
    try:
        conn = db_connection()
        if conn:
            with conn.cursor() as cur:
                #создание таблицы currencies
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS currencies (
                        id SERIAL PRIMARY KEY,
                        currency_name VARCHAR(50) UNIQUE NOT NULL,
                        rate NUMERIC(10, 2) NOT NULL
                    )
                """)
                
                #создание таблицы admins
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS admins (
                        id SERIAL PRIMARY KEY,
                        chat_id VARCHAR(50) UNIQUE NOT NULL
                    )
                """)
                
                conn.commit()
            logging.info("База данных успешно инициализирована")
        else:
            logging.error("Не удалось подключиться к базе данных для инициализации")
    except Exception as e:
        logging.error(f"Ошибка при инициализации базы данных: {e}")
    finally:
        if conn:
            conn.close()

#проверка на администратора
async def is_admin(chat_id):
    conn = None
    try:
        conn = db_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM admins WHERE chat_id = %s", (str(chat_id),))
                return bool(cur.fetchone())
        return False
    except Exception as e:
        logging.error(f"Ошибка при проверке администратора: {e}")
        return False
    finally:
        if conn:
            conn.close()

#/start
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    if await is_admin(message.chat.id):
        await message.answer(
            "Привет, администратор!\n"
            "Доступные команды:\n"
            "/manage_currency - управление валютами\n"
            "/get_currencies - список всех валют\n"
            "/convert - конвертация валюты",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await message.answer(
            "Привет!\n"
            "Доступные команды:\n"
            "/get_currencies - список всех валют\n"
            "/convert - конвертация валюты",
            reply_markup=ReplyKeyboardRemove()
        )

#/manage_currency (только для администраторов)
@dp.message(Command("manage_currency"))
async def cmd_manage_currency(message: types.Message):
    if not await is_admin(message.chat.id):
        await message.answer("Нет доступа к команде", reply_markup=ReplyKeyboardRemove())
        return
    
    await message.answer(
        "Выберите действие:",
        reply_markup=currency_keyboard()
    )

#кнопка "Добавить валюту"
@dp.message(F.text == "Добавить валюту")
async def add_currency_start(message: types.Message, state: FSMContext):
    if not await is_admin(message.chat.id):
        await message.answer("Нет доступа", reply_markup=ReplyKeyboardRemove())
        return
    
    await state.set_state(CurrencyStates.name)
    await message.answer(
        "Введите название валюты:",
        reply_markup=ReplyKeyboardRemove()
    )

#получение названия валюты
@dp.message(CurrencyStates.name)
async def add_currency_name(message: types.Message, state: FSMContext):
    currency_name = message.text.upper()
    
    try:
        conn = db_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM currencies WHERE currency_name = %s", (currency_name,))
                if cur.fetchone():
                    await message.answer("Данная валюта уже существует")
                    await state.clear()
                    return
                await state.update_data(currency_name=currency_name)
                await state.set_state(CurrencyStates.rate)
                await message.answer("Введите курс к рублю:")
    except Exception as e:
        logging.error(f"Ошибка при проверке валюты: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")
        await state.clear()
    finally:
        if conn:
            conn.close()

#получение курса валюты для добавления
@dp.message(CurrencyStates.rate)
async def add_currency_rate(message: types.Message, state: FSMContext):
    try:
        rate = float(message.text.replace(',', '.'))
        if rate <= 0:
            await message.answer("Курс должен быть положительным числом.")
            return
        data = await state.get_data()
        currency_name = data["currency_name"]
        
        conn = db_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO currencies (currency_name, rate) VALUES (%s, %s)",
                    (currency_name, rate)
                )
                conn.commit()
                await message.answer(f"Валюта: {currency_name} успешно добавлена")
    except ValueError:
        await message.answer("Неверный формат курса. Введите число (например: 75.43 или 75,43).")
        return
    except Exception as e:
        logging.error(f"Ошибка при добавлении валюты: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")
    finally:
        await state.clear()
        if conn:
            conn.close()

#кнопка "Удалить валюту"
@dp.message(F.text == "Удалить валюту")
async def delete_currency_start(message: types.Message, state: FSMContext):
    if not await is_admin(message.chat.id):
        await message.answer("Нет доступа", reply_markup=ReplyKeyboardRemove())
        return
    
    await state.set_state(CurrencyStates.delete)
    await message.answer(
        "Введите название валюты для удаления:",
        reply_markup=ReplyKeyboardRemove()
    )

#удаление
@dp.message(CurrencyStates.delete)
async def delete_currency(message: types.Message, state: FSMContext):
    currency_name = message.text.upper()
    
    try:
        conn = db_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM currencies WHERE currency_name = %s RETURNING currency_name",
                    (currency_name,)
                )
                deleted = cur.fetchone()
                conn.commit()
                if deleted:
                    await message.answer(f"Валюта {currency_name} успешно удалена")
                else:
                    await message.answer(f"Валюта {currency_name} не найдена")
    except Exception as e:
        logging.error(f"Ошибка при удалении валюты: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")
    finally:
        await state.clear()
        if conn:
            conn.close()

#кнопка "Изменить курс валюты"
@dp.message(F.text == "Изменить курс валюты")
async def update_currency_start(message: types.Message, state: FSMContext):
    if not await is_admin(message.chat.id):
        await message.answer("Нет доступа", reply_markup=ReplyKeyboardRemove())
        return
    
    await state.set_state(CurrencyStates.update)
    await message.answer(
        "Введите название валюты для изменения курса:",
        reply_markup=ReplyKeyboardRemove()
    )

#получение названия валюты для изменения курса
@dp.message(CurrencyStates.update)
async def update_currency_name(message: types.Message, state: FSMContext):
    currency_name = message.text.upper()
    try:
        conn = db_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM currencies WHERE currency_name = %s", (currency_name,))
                if not cur.fetchone():
                    await message.answer(f"Валюта {currency_name} не найдена")
                    await state.clear()
                    return
                await state.update_data(currency_name=currency_name)
                await state.set_state(CurrencyStates.new_rate)
                await message.answer("Введите новый курс к рублю:")
    except Exception as e:
        logging.error(f"Ошибка при проверке валюты: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")
        await state.clear()
    finally:
        if conn:
            conn.close()

#обновление курса валюты
@dp.message(CurrencyStates.new_rate)
async def update_currency_rate(message: types.Message, state: FSMContext):
    try:
        new_rate = float(message.text.replace(',', '.'))
        if new_rate <= 0:
            await message.answer("Курс должен быть положительным числом.")
            return
        data = await state.get_data()
        currency_name = data["currency_name"]
        conn = db_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE currencies SET rate = %s WHERE currency_name = %s",
                    (new_rate, currency_name)
                )
                conn.commit()
                await message.answer(f"Курс валюты {currency_name} успешно изменен на {new_rate}")
    except ValueError:
        await message.answer("Неверный формат курса. Введите число (например: 75.43 или 75,43).")
        return
    except Exception as e:
        logging.error(f"Ошибка при обновлении курса: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")
    finally:
        await state.clear()
        if conn:
            conn.close()

#/get_currencies
@dp.message(Command("get_currencies"))
async def cmd_get_currencies(message: types.Message):
    try:
        conn = db_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute("SELECT currency_name, rate FROM currencies ORDER BY currency_name")
                currencies = cur.fetchall()
                if currencies:
                    response = "Список валют и их курсов к рублю:\n"
                    for currency in currencies:
                        response += f"{currency[0]}: {currency[1]}\n"
                    await message.answer(response)
                else:
                    await message.answer("В базе данных нет сохраненных валют")
    except Exception as e:
        logging.error(f"Ошибка при получении списка валют: {e}")
        await message.answer("Произошла ошибка при получении списка валют")
    finally:
        if conn:
            conn.close()

#/convert 
@dp.message(Command("convert"))
async def cmd_convert(message: types.Message, state: FSMContext):
    await state.set_state(CurrencyStates.convert_currency)
    await message.answer("Введите название валюты:")

#получение названия валюты 
@dp.message(CurrencyStates.convert_currency)
async def convert_currency_name(message: types.Message, state: FSMContext):
    currency_name = message.text.upper()
    
    try:
        conn = db_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute("SELECT rate FROM currencies WHERE currency_name = %s", (currency_name,))
                rate = cur.fetchone()
                
                if not rate:
                    await message.answer(f"Валюта {currency_name} не найдена")
                    await state.clear()
                    return
                
                await state.update_data(currency_name=currency_name, rate=rate[0])
                await state.set_state(CurrencyStates.convert_amount)
                await message.answer("Введите сумму для конвертации:")
    except Exception as e:
        logging.error(f"Ошибка при поиске валюты: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")
        await state.clear()
    finally:
        if conn:
            conn.close()

#конвертация валюты
@dp.message(CurrencyStates.convert_amount)
async def convert_currency_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            await message.answer("Сумма должна быть положительной")
            return
        
        data = await state.get_data()
        currency_name = data["currency_name"]
        rate = float(data["rate"])  
        
        result = amount * rate
        await message.answer(f"{amount} {currency_name} = {result:.2f} руб.")
    except ValueError:
        await message.answer("Неверный формат суммы. Введите число (например: 100 или 100,50).")
        return
    except Exception as e:
        logging.error(f"Ошибка при конвертации: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")
    finally:
        await state.clear()

#запуск бота
async def main():
    init_db()
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())

    