from flask import Flask, request, abort, send_from_directory
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageMessage, ImageSendMessage
)
import os

app = Flask(__name__)

# Load credentials from environment variables
# LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
# LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

LINE_CHANNEL_ACCESS_TOKEN = "Vx9EqfAePjUC2/AAllYO0LhE3m5l/VkUTfGDlxMvuIC4Mf635WTB8G+Y1aikUj8FLRbdFvEkFRdwR5dYRSvX5gqB64fu3I9akViE7GJmlfoK0+vjbpgReNo0TPAkhGOqr7rFHb91QpkUaeFoQvMz2AdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "6262aa5eb114fbd6916ed6fa7e78d18b"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


# ✅ Ensure "static" folder exists
STATIC_FOLDER = "static"
os.makedirs(STATIC_FOLDER, exist_ok=True)

@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running!", 200  # Ensure it returns 200

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    if not signature:
        abort(400)

    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK", 200

# ✅ Serve images from the "static" folder
@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory(STATIC_FOLDER, filename)

# ✅ Handle Text Messages
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_message = event.message.text
    reply_text = f"You said: {user_message}"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

# ✅ Handle Image Messages
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    message_id = event.message.id

    # 🔹 Get image from LINE's server
    message_content = line_bot_api.get_message_content(message_id)

    # 🔹 Save the image in the "static/" directory
    image_path = os.path.join(STATIC_FOLDER, f"{message_id}.jpg")
    with open(image_path, "wb") as img_file:
        for chunk in message_content.iter_content():
            img_file.write(chunk)

    # 🔹 Generate a public URL for the image
    render_app_url = "https://your-app-name.onrender.com"  # Change to your Render URL
    image_url = f"{render_app_url}/static/{message_id}.jpg"

    # 🔹 Debug: Print URL in logs
    print("Sending image:", image_url)

    # 🔹 Send the image back
    line_bot_api.reply_message(
        event.reply_token,
        ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
