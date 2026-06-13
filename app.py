from flask import Flask, request
import requests
import os
import PyPDF2
import tempfile

app = Flask(__name__)

# 🔐 ENV VARIABLES (Render ma set karva)
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "myverify123")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "")

# 💰 PRICE SETTINGS
PRICE_PER_PAGE_BW = 2
PRICE_PER_PAGE_COLOR = 5


# -------------------------
# HOME ROUTE
# -------------------------
@app.route("/", methods=["GET"])
def home():
    return "WhatsApp PDF Bot is Running 🚀"


# -------------------------
# WEBHOOK VERIFY + RECEIVE
# -------------------------
@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    # VERIFY (Meta setup time)
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Verification failed", 403

    # RECEIVE MESSAGE
    if request.method == "POST":
        data = request.json

        try:
            entry = data["entry"][0]
            changes = entry["changes"][0]
            value = changes["value"]

            messages = value.get("messages", [])

            if messages:
                msg = messages[0]
                sender = msg["from"]

                # If document (PDF)
                if msg["type"] == "document":
                    media_id = msg["document"]["id"]

                    # Process PDF
                    pages = process_pdf(media_id)

                    # Calculate price
                    price = pages * PRICE_PER_PAGE_BW

                    reply_text = f"""📄 PDF Received

Pages: {pages}
Rate: ₹{PRICE_PER_PAGE_BW}/page

💰 Total Price: ₹{price}

Thank you for your order 👍"""

                    send_message(sender, reply_text)

        except Exception as e:
            print("Error:", e)

        return "OK", 200


# -------------------------
# DOWNLOAD + COUNT PDF PAGES
# -------------------------
def process_pdf(media_id):
    url = f"https://graph.facebook.com/v20.0/{media_id}"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}"
    }

    r = requests.get(url, headers=headers)
    media_url = r.json()["url"]

    pdf_data = requests.get(media_url, headers=headers)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
        f.write(pdf_data.content)
        file_path = f.name

    reader = PyPDF2.PdfReader(file_path)
    return len(reader.pages)


# -------------------------
# SEND MESSAGE
# -------------------------
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


# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
