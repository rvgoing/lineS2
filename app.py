from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

app = Flask(__name__)

# Load credentials from environment variables
# LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
# LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

LINE_CHANNEL_ACCESS_TOKEN = "Vx9EqfAePjUC2/AAllYO0LhE3m5l/VkUTfGDlxMvuIC4Mf635WTB8G+Y1aikUj8FLRbdFvEkFRdwR5dYRSvX5gqB64fu3I9akViE7GJmlfoK0+vjbpgReNo0TPAkhGOqr7rFHb91QpkUaeFoQvMz2AdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "6262aa5eb114fbd6916ed6fa7e78d18b"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running!"

@app.route("/webhook", methods=["POST"])  # ✅ Must allow POST requests
def webhook():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)  # Return 400 if signature is invalid

    return "OK", 200  # ✅ Must return status 200


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    reply_text = f"You said: {user_message}"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    app.run(port=5000)
