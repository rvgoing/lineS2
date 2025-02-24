import os
from flask import Flask, request, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from werkzeug.utils import secure_filename

app = Flask(__name__)

# LINE Bot Configuration
LINE_CHANNEL_ACCESS_TOKEN = "Vx9EqfAePjUC2/AAllYO0LhE3m5l/VkUTfGDlxMvuIC4Mf635WTB8G+Y1aikUj8FLRbdFvEkFRdwR5dYRSvX5gqB64fu3I9akViE7GJmlfoK0+vjbpgReNo0TPAkhGOqr7rFHb91QpkUaeFoQvMz2AdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "6262aa5eb114fbd6916ed6fa7e78d18b"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ===================================
# PostgreSQL process
# ===================================

# Configure PostgreSQL (Replace with your Render database URL)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "postgresql://linebots1_user:x5XSGS3mtdDq2urm52I2kwHksHdhsVYM@dpg-cusib1vnoe9s738vfsl0-a/linebots1")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



# Define ChatHistory Model
class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)
    user_message = db.Column(db.String(500), nullable=True)
    bot_response = db.Column(db.String(500), nullable=True)
    image_data = db.Column(db.LargeBinary, nullable=True)  # Store image binary data
    image_type = db.Column(db.String(50), nullable=True)  # Store file type

# with app.app_context():
    db.create_all()


# ===================================
# main Linbot Test process
# ===================================
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

# # Handle LINE Bot Messages
# @app.route("/callback", methods=["POST"])
# def callback():
#     signature = request.headers['X-Line-Signature']
#     body = request.get_data(as_text=True)
#     handler.handle(body, signature)
#     return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    user_id = event.source.user_id

    chat = ChatHistory(user_id=user_id, user_message=user_message, bot_response="Received")
    db.session.add(chat)
    db.session.commit()

    bot_response = f"You said: {user_message}"  # Simple Echo Response
    chat.bot_response = bot_response
    db.session.commit()

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=bot_response))

# Upload Image to PostgreSQL
@app.route("/upload_image", methods=["POST"])
def upload_image():
    if "image" not in request.files:
        return jsonify({"error": "No image file found"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    new_chat = ChatHistory(
        user_id="test_user",
        image_data=file.read(),
        image_type=file.content_type
    )
    db.session.add(new_chat)
    db.session.commit()

    return jsonify({"message": "Image uploaded successfully!", "chat_id": new_chat.id}), 201

# Retrieve Image from PostgreSQL
@app.route("/get_image/<int:chat_id>", methods=["GET"])
def get_image(chat_id):
    chat = ChatHistory.query.get(chat_id)
    if chat and chat.image_data:
        return Response(chat.image_data, mimetype=chat.image_type)
    return jsonify({"error": "Image not found"}), 404

# Get Chat History
@app.route("/history", methods=["GET"])
def get_history():
    try:
        chats = ChatHistory.query.all()
        history = [{
            "id": chat.id,
            "user_id": chat.user_id,
            "user_message": chat.user_message,
            "bot_response": chat.bot_response
        } for chat in chats]
        return jsonify(history), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
