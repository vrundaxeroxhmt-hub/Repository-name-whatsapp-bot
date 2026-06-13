from flask import Flask

app = Flask(**name**)

@app.route("/")
def home():
return "WhatsApp Print Bot Running"

@app.route("/telegram-test")
def telegram_test():
return "Telegram Route Working"

if **name** == "**main**":
app.run(host="0.0.0.0", port=5000)
