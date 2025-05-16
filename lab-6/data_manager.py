import os
import psycopg2
from flask import Flask, request, jsonify
from dotenv import load_dotenv

#загрузка переменных окружения
load_dotenv()

app = Flask(__name__)

#настройки базы данных
DB_NAME = os.getenv('DB_NAME', 'currency_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

def get_db_connection():
    """Установка соединения с базой данных"""
    try:
        return psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
    except Exception as e:
        app.logger.error(f"Ошибка подключения к базе данных: {e}")
        return None

@app.route('/convert', methods=['GET'])
def convert_currency():
    """Конвертация валюты"""
    currency_name = request.args.get('currency')
    amount = request.args.get('amount')

    if not currency_name or not amount:
        return jsonify({'error': 'Не указана валюта или сумма'}), 400

    try:
        #проверка что сумма является числом
        amount = float(amount)
        if amount <= 0:
            return jsonify({'error': 'Сумма должна быть положительным числом'}), 400
    except ValueError:
        return jsonify({'error': 'Неверный формат суммы. Должно быть число'}), 400

    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Не удалось подключиться к базе данных'}), 500

        with conn.cursor() as cur:
            #получение курса валюты
            cur.execute(
                "SELECT rate FROM currencies WHERE currency_name = %s",
                (currency_name.upper(),)
            )
            result = cur.fetchone()
            
            if not result:
                return jsonify({'error': 'Валюта не найдена'}), 404

            rate = result[0]
            converted_amount = amount * rate
            return jsonify({
                'currency': currency_name.upper(),
                'original_amount': amount,
                'converted_amount': round(converted_amount, 2),
                'rate': rate
            }), 200

    except Exception as e:
        app.logger.error(f"Ошибка при конвертации валюты: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/currencies', methods=['GET'])
def get_all_currencies():
    """Получение списка всех валют"""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Не удалось подключиться к базе данных'}), 500

        with conn.cursor() as cur:
            cur.execute("SELECT currency_name, rate FROM currencies ORDER BY currency_name")
            currencies = cur.fetchall()
            
            result = [{
                'currency_name': currency[0],
                'rate': float(currency[1])
            } for currency in currencies]
            
            return jsonify({'currencies': result}), 200

    except Exception as e:
        app.logger.error(f"Ошибка при получении списка валют: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(port=5002)