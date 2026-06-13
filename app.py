from flask import Flask, request

app = Flask(__name__)

VERIFY_TOKEN = "myverify123"

@app.route("/", methods=["GET"])
def home():
    return "Bot is running"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Error", 403

    if request.method == "POST":
        data = request.json
        print(data)
        return "OK", 200

if __name__ == "__main__":
    app.run()
