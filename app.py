import time
from flask import Flask, request
import requests
import os
import PyPDF2
import tempfile
app = Flask(__name__)

TELEGRAM_BOT_TOKEN = "8901318810:AAFszegHbEY2mw6sERa-khj1ghrRqBDmdkI"
TELEGRAM_CHAT_ID = "264634921"
def send_telegram(text):

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text
        }
    )

    print("Telegram:", response.text)


@app.route("/telegram-test")
def telegram_test():

    send_telegram("✅ Telegram Test Success")

    return "Telegram Sent"
# =========================
# CONFIG
# =========================
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "myverify123")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "")

PDF_RATE = 2      # ₹ per PDF page
PHOTO_RATE = 3    # ₹ per Photo

UPI_ID = "yourupi@upi"

# User Orders Storage
orders = {}

# =========================
# HOME
# =========================
@app.route("/")
def home():

    try:
        send_telegram("HOME TEST FROM RENDER")
        return "TELEGRAM SENT"

    except Exception as e:
        return str(e)

# =========================
# WEBHOOK
# =========================
@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    # Meta Verification
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Verification Failed", 403

    # Incoming Messages
    data = request.json

    try:
        value = data["entry"][0]["changes"][0]["value"]

        if "messages" not in value:
            return "OK", 200

        msg = value["messages"][0]
        sender = msg["from"]

        # Create User Record
        if sender not in orders:
            orders[sender] = {
                "pdf_pages": 0,
                "photos": 0
            }

        # =====================
        # TEXT COMMANDS
        # =====================
        if msg["type"] == "text":

            text = msg["text"]["body"].strip().upper()

            # STATUS
            if text == "STATUS":

                pdf_pages = orders[sender]["pdf_pages"]
                photos = orders[sender]["photos"]

                total = (
                    pdf_pages * PDF_RATE
                    + photos * PHOTO_RATE
                )

                reply = f"""📋 CURRENT ORDER

📄 PDF Pages: {pdf_pages}
🖼 Photos: {photos}

💰 Current Total: ₹{total}
"""

                send_message(sender, reply)
                return "OK", 200
        # =====================
        # DONE
        # =====================

elif text == "DONE":

    pdf_pages = orders[sender]["pdf_pages"]
    photos = orders[sender]["photos"]

    pdf_cost = pdf_pages * PDF_RATE
    photo_cost = photos * PHOTO_RATE

    total = pdf_cost + photo_cost

    telegram_msg = f"""NEW ORDER

Customer: {sender}

PDF Pages: {pdf_pages}
Photos: {photos}

Total: Rs.{total}
"""

    send_telegram(telegram_msg)

    bill = f"""FINAL BILL

PDF Pages: {pdf_pages}
Photos: {photos}

PDF Cost: Rs.{pdf_cost}
Photo Cost: Rs.{photo_cost}

--------------------
TOTAL: Rs.{total}
--------------------

UPI:
{UPI_ID}

Payment kari screenshot moklo.
"""

    send_message(sender, bill)

    return "OK", 200
        # =====================
        # PDF
        # =====================
        elif msg["type"] == "document":

            media_id = msg["document"]["id"]

            pages = get_pdf_pages(media_id)

            orders[sender]["pdf_pages"] += pages

            send_message(
                sender,
                f"""📄 PDF Added

Pages Added: {pages}

Type STATUS to view order.
Type DONE when finished."""
            )

            return "OK", 200

        # =====================
        # PHOTO
        # =====================
        elif msg["type"] == "image":

            orders[sender]["photos"] += 1

            total_photos = orders[sender]["photos"]

            send_message(
                sender,
                f"""🖼 Photo Added

Total Photos: {total_photos}

Type STATUS to view order.
Type DONE when finished."""
            )

            return "OK", 200

    except Exception as e:
        print("ERROR:", e)

    return "OK", 200


# =========================
# PDF PAGE COUNT
# =========================
def get_pdf_pages(media_id):

    url = f"https://graph.facebook.com/v23.0/{media_id}"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}"
    }

    r = requests.get(url, headers=headers)
    data = r.json()

    if "url" not in data:
        print("MEDIA ERROR:", data)
        return 0

    media_url = data["url"]

    pdf_response = requests.get(
        media_url,
        headers=headers
    )

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    ) as f:

        f.write(pdf_response.content)
        file_path = f.name

    reader = PyPDF2.PdfReader(file_path)

    return len(reader.pages)


# =========================
# SEND WHATSAPP MESSAGE
# =========================
def send_message(to, text):

    url = (
        f"https://graph.facebook.com/v23.0/"
        f"{PHONE_NUMBER_ID}/messages"
    )

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "body": text
        }
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload
    )

    print(response.text)


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
