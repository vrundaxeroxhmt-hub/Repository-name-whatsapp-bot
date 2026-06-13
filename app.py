from flask import Flask, request, render_template_string
import requests
import os
import PyPDF2
import tempfile

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "myverify123")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "")

PRICE_PER_PAGE = 2

# 📊 SIMPLE MEMORY STORAGE (for demo)
orders = []


# ---------------- HOME ----------------
@app.route("/")
def home():
    return "WhatsApp PDF Bot + Admin Panel Running 🚀"


# ---------------- ADMIN PANEL ----------------
@app.route("/admin")
def admin():

    total_orders = len(orders)
    total_earnings = sum(o["price"] for o in orders)

    html = """
    <h1>📊 Admin Panel</h1>
    <h3>Total Orders: {{total_orders}}</h3>
    <h3>Total Earnings: ₹{{total_earnings}}</h3>

    <hr>
    <h2>Orders List</h2>
    {% for o in orders %}
        <p>
        📱 {{o['user']}} <br>
        📄 Pages: {{o['pages']}} <br>
        💰 Price: ₹{{o['price']}}
        </p>
        <hr>
    {% endfor %}
    """

    return render_template_string(html,
                                  orders=orders,
                                  total_orders=total_orders,
                                  total_earnings=total_earnings)


# ---------------- WEBHOOK ----------------
@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Error", 403

    if request.method == "POST":
        data = request.json

        try:
            msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
            sender = msg["from"]

            if msg["type"] == "document":
                media_id = msg["document"]["id"]

                pages = process_pdf(media_id)
                price = pages * PRICE_PER_PAGE

                # Save order in admin panel
                orders.append({
                    "user": sender,
                    "pages": pages,
                    "price": price
                })

                reply = f"""📄 PDF Received

Pages: {pages}
Price: ₹{price}

Thank you 👍"""

                send_message(sender, reply)

        except Exception as e:
            print("Error:", e)

        return "OK", 200


# ---------------- PDF PROCESS ----------------
def process_pdf(media_id):

    url = f"https://graph.facebook.com/v20.0/{media_id}"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}

    r = requests.get(url, headers=headers)
    media_url = r.json()["url"]

    pdf_data = requests.get(media_url, headers=headers)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
        f.write(pdf_data.content)
        path = f.name

    reader = PyPDF2.PdfReader(path)
    return len(reader.pages)


# ---------------- SEND MESSAGE ----------------
def send_message(to, text):

    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }

    requests.post(url, headers=headers, json=payload)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
