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

# ---------------- HOME ----------------
@app.route("/")
def home():
    return "WhatsApp PDF Bot Running 🚀"


# ---------------- WEBHOOK ----------------
@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    # VERIFY META
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Error", 403

    # RECEIVE MESSAGE
    if request.method == "POST":
        data = request.json

        try:
            value = data["entry"][0]["changes"][0]["value"]

            # SAFE CHECK (IMPORTANT)
            if "messages" not in value:
                return "No message", 200

            msg = value["messages"][0]
            sender = msg["from"]

            # ONLY PDF
            if msg["type"] == "document":
                media_id = msg["document"]["id"]

                pages = get_pdf_pages(media_id)

                reply = f"""📄 PDF Received

Pages: {pages}"""

                send_message(sender, reply)

        except Exception as e:
            print("ERROR:", e)

        return "OK", 200


# ---------------- GET PDF PAGE COUNT ----------------
def get_pdf_pages(media_id):

    url = f"https://graph.facebook.com/v20.0/{media_id}"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}

    r = requests.get(url, headers=headers)
    data = r.json()

    # SAFE CHECK (IMPORTANT FIX)
    if "url" not in data:
        print("MEDIA ERROR:", data)
        return 0

    media_url = data["url"]

    pdf_data = requests.get(media_url, headers=headers)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
        f.write(pdf_data.content)
        file_path = f.name

    reader = PyPDF2.PdfReader(file_path)
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


# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
