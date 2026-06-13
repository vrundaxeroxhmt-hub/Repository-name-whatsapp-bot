from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "TEST 12345"

@app.route("/telegram-test")
def telegram_test():
    return "Telegram Route Working"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
