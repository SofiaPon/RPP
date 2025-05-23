from flask import Flask, jsonify, request

app = Flask(__name__)

#курсы валют
RATES = {
    "USD": 90.0,
    "EUR": 100.0,
    "RUB": 1.0
}

@app.route('/rate', methods=['GET'])
def get_rate():
    currency = request.args.get('currency')
    
    if currency not in RATES:
        return jsonify({"message": "UNKNOWN CURRENCY"}), 400
    
    try:
        return jsonify({"rate": RATES[currency]}), 200
    except Exception as e:
        return jsonify({"message": "UNEXPECTED ERROR"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)