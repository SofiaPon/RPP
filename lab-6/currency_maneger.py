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

@app.route('/load', methods=['POST'])
def load_currency():
    """Добавление новой валюты"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Необходимо передать данные в формате JSON'}), 400

    currency_name = data.get('currency_name')
    rate = data.get('rate')

    if not currency_name or not rate:
        return jsonify({'error': 'Не указано название валюты или курс'}), 400

    try:
        #проверка что курс является числом
        rate = float(rate)
        if rate <= 0:
            return jsonify({'error': 'Курс должен быть положительным числом'}), 400
    except ValueError:
        return jsonify({'error': 'Неверный формат курса. Должно быть число'}), 400

    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Не удалось подключиться к базе данных'}), 500

        with conn.cursor() as cur:
            #проверка существования валюты
            cur.execute("SELECT 1 FROM currencies WHERE currency_name = %s", (currency_name.upper(),))
            if cur.fetchone():
                return jsonify({'error': 'Валюта уже существует'}), 400

            #добавление валюты
            cur.execute(
                "INSERT INTO currencies (currency_name, rate) VALUES (%s, %s)",
                (currency_name.upper(), rate)
            )
            conn.commit()
            return jsonify({'message': f'Валюта {currency_name} успешно добавлена'}), 200

    except Exception as e:
        app.logger.error(f"Ошибка при добавлении валюты: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/update_currency', methods=['POST'])
def update_currency():
    """Обновление курса валюты"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Необходимо передать данные в формате JSON'}), 400

    currency_name = data.get('currency_name')
    new_rate = data.get('rate')

    if not currency_name or not new_rate:
        return jsonify({'error': 'Не указано название валюты или курс'}), 400

    try:
        #проверка что курс является числом
        new_rate = float(new_rate)
        if new_rate <= 0:
            return jsonify({'error': 'Курс должен быть положительным числом'}), 400
    except ValueError:
        return jsonify({'error': 'Неверный формат курса. Должно быть число'}), 400

    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Не удалось подключиться к базе данных'}), 500

        with conn.cursor() as cur:
            #проверка существования валюты
            cur.execute("SELECT 1 FROM currencies WHERE currency_name = %s", (currency_name.upper(),))
            if not cur.fetchone():
                return jsonify({'error': 'Валюта не найдена'}), 404

            #обновление курса
            cur.execute(
                "UPDATE currencies SET rate = %s WHERE currency_name = %s",
                (new_rate, currency_name.upper())
            )
            conn.commit()
            return jsonify({'message': f'Курс валюты {currency_name} обновлен до {new_rate}'}), 200

    except Exception as e:
        app.logger.error(f"Ошибка при обновлении валюты: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/delete', methods=['POST'])
def delete_currency():
    """Удаление валюты"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Необходимо передать данные в формате JSON'}), 400

    currency_name = data.get('currency_name')
    if not currency_name:
        return jsonify({'error': 'Не указано название валюты'}), 400

    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Не удалось подключиться к базе данных'}), 500

        with conn.cursor() as cur:
            #проверка существования валюты
            cur.execute("SELECT 1 FROM currencies WHERE currency_name = %s", (currency_name.upper(),))
            if not cur.fetchone():
                return jsonify({'error': 'Валюта не найдена'}), 404

            #удаление валюты
            cur.execute("DELETE FROM currencies WHERE currency_name = %s", (currency_name.upper(),))
            conn.commit()
            return jsonify({'message': f'Валюта {currency_name} успешно удалена'}), 200

    except Exception as e:
        app.logger.error(f"Ошибка при удалении валюты: {e}")
        return jsonify({'error': 'Внутренняя ошибка сервера'}), 500
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    app.run(port=5001)