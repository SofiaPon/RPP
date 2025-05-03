import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from dotenv import load_dotenv


#загрузка переменных окружения из файла .env
load_dotenv()

#получение токена бота из переменной окружения
bot_token= os.getenv('API_TOKEN')

#включаем логирование
logging.basicConfig(level=logging.INFO)

#инициализация бота
bot = Bot(token=bot_token)
dp = Dispatcher()

#словарь для хранения курсов валют
currency = {}

#сохранение валюты
class SaveCurrency(StatesGroup):
    name = State()
    rate = State()

#конвертация валюты
class ConvertCurrency(StatesGroup):
    index = State()
    amount = State()


#/start
@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(f"Привет!\nЯ бот для сохранения и конвертации валют.\nИспользуйте /save_currency для сохранения курса валюты и /convert для конвертации.")

#/save_currency
@dp.message(Command("save_currency"))
async def save_currency(message: Message, state: FSMContext):

    await state.set_state(SaveCurrency.name)
    await message.answer("Пожалуйста, введите название валюты:")

#получение названия валюты
@dp.message(SaveCurrency.name)
async def save_currency_name(message: Message, state: FSMContext):

    await state.update_data(currency_name=message.text.upper())  #верхний регистр
    await state.set_state(SaveCurrency.rate) 
    await message.answer("Пожалуйста, введите курс валюты к рублю:")

#сохранение курса валюты
@dp.message(SaveCurrency.rate)
async def save_currency_rate(message: Message, state: FSMContext):
    try:
        rate = float(message.text.replace(',', '.'))
        data = await state.get_data()
        currency_name = data["currency_name"]
        
        #генерируем новый индекс
        new_index = len(currency) + 1
        currency[new_index] = {"name": currency_name, "rate": rate}
        
        await state.clear()
        await message.answer(f"Курс {currency_name} ({rate}) сохранен под индексом {new_index}.")
        
    except ValueError:
        await message.answer("Неверный формат. Введите число (например: 75.43 или 75,43).")
    except Exception as e:
        logging.error(f"Ошибка сохранения: {e}")
        await message.answer("Ошибка. Попробуйте снова.")
    finally:
        await state.clear()


#вывод сохраненных курсов валют
@dp.message(Command("list"))
async def list_currency(message: Message):
    if currency:
        text = "Сохраненные курсы:\n"
        for index, curr_data in currency.items():
            text += f"{index}: {curr_data['name']} - {curr_data['rate']}\n"
        await message.answer(text)
    else:
        await message.answer("Курсы не сохранены. Используйте /save_currency.")


#/convert
@dp.message(Command("convert"))
async def convert_currency(message: Message, state: FSMContext):
    if not currency:
        await message.answer("Сначала добавьте курсы с помощью /save_currency.")
        return
    await state.set_state(ConvertCurrency.index)
    await message.answer("Введите индекс валюты или /list:")

#конвертация
@dp.message(ConvertCurrency.index)
async def convert_currency_index(message: Message, state: FSMContext):
    if message.text.lower() == "/list":
        await list_currency(message)
        return

    try:
        index = int(message.text)
        if index in currency:  #проверяем существование индекса
            await state.update_data(currency_index=index)
            await state.set_state(ConvertCurrency.amount)
            await message.answer("Введите сумму для конвертации:")
        else:
            await message.answer(f"Валюта с индексом {index} не найдена. Введите существующий индекс или /list")
    
    except ValueError:
        await message.answer("Неверный формат. Введите число (индекс валюты) или /list")
    except Exception as e:
        logging.error(f"Ошибка при выборе валюты: {e}")
        await message.answer("Произошла ошибка. Попробуйте снова.")

#вывод суммы
@dp.message(ConvertCurrency.amount, F.text)
async def convert_currency_amount(message: Message, state: FSMContext):  
    try:
        amount = float(message.text.replace(',', '.'))
        data = await state.get_data()
        index = data["currency_index"]
        
        #используем глобальную переменную currency
        curr = currency.get(index)
        if not curr:
            await message.answer("Ошибка: валюта не найдена.")
            return
            
        result = amount * curr["rate"]
        await message.answer(f"{amount} {curr['name']} = {result:.2f} руб.")
        logging.info(f"Конвертация {amount} {curr['name']} в рубли")
        
    except ValueError:
        await message.answer("Неверный формат суммы. Введите число (например: 100 или 100,50).")
    except Exception as e:
        logging.error(f"Ошибка конвертации: {e}")
        await message.answer("Ошибка. Попробуйте снова.")
    finally:
        await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())