@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Error", 403

    if request.method == "POST":
        data = request.json

        try:
            value = data["entry"][0]["changes"][0]["value"]

            # 🔥 SAFE CHECK (IMPORTANT)
            if "messages" not in value:
                return "No message", 200

            msg = value["messages"][0]
            sender = msg["from"]

            # ONLY PDF
            if msg["type"] == "document":
                media_id = msg["document"]["id"]

                pages = get_pdf_pages(media_id)

                reply = f"📄 PDF Received\nPages: {pages}"

                send_message(sender, reply)

        except Exception as e:
            print("ERROR:", e)

        return "OK", 200
