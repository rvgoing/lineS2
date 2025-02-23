import os
from flask import Flask, request, send_from_directory
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage, ImageSendMessage

app = Flask(__name__)

# Load credentials from environment variables
# LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
# LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

LINE_CHANNEL_ACCESS_TOKEN = "Vx9EqfAePjUC2/AAllYO0LhE3m5l/VkUTfGDlxMvuIC4Mf635WTB8G+Y1aikUj8FLRbdFvEkFRdwR5dYRSvX5gqB64fu3I9akViE7GJmlfoK0+vjbpgReNo0TPAkhGOqr7rFHb91QpkUaeFoQvMz2AdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "6262aa5eb114fbd6916ed6fa7e78d18b"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


# Folder for saving images
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


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

# ✅ Handle Text Messages
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_message = event.message.text
    reply_text = f"You said: {user_message}"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

# Handle image messages (Save & Reply with the Image)
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    message_id = event.message.id

    # Get image from Line API
    image_content = line_bot_api.get_message_content(message_id)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{message_id}.jpg")

    # Save image to static/uploads/
    with open(file_path, "wb") as f:
        for chunk in image_content.iter_content():
            f.write(chunk)

    # Generate Image URL
    image_url = f"{request.host_url}uploads/{message_id}.jpg"

    # Reply with the uploaded image
    line_bot_api.reply_message(event.reply_token, ImageSendMessage(
        original_content_url=image_url,
        preview_image_url=image_url
    ))

# Route to serve images
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
