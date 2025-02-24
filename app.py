from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage
import os
import io

app = Flask(__name__)

# Load credentials from environment variables
# LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
# LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

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

db = SQLAlchemy(app)

# ===================================
# Database Model
# ===================================
class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)
    user_message = db.Column(db.String(500), nullable=False)
    bot_response = db.Column(db.String(500), nullable=False)

class ImageStorage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)
    image_data = db.Column(db.LargeBinary, nullable=False)  # ✅ Store images in BYTEA format
    filename = db.Column(db.String(255), nullable=False)

# ✅ Ensure database tables are created
with app.app_context():
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

# ===================================
# Handle Text Messages
# ===================================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    user_id = event.source.user_id

    bot_response = f"You said: {user_message}"

    # Save to database
    chat = ChatHistory(user_id=user_id, user_message=user_message, bot_response=bot_response)
    db.session.add(chat)
    db.session.commit()

    # Reply to user
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=bot_response))


# ===================================
# Handle Image Messages
# ===================================
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    user_id = event.source.user_id
    message_id = event.message.id

    # ✅ Get image content from LINE
    image_content = line_bot_api.get_message_content(message_id)
    image_data = image_content.content  # Read binary data

    # ✅ Save image to database
    image = ImageStorage(user_id=user_id, image_data=image_data, filename=f"user_{user_id}.jpg")
    db.session.add(image)
    db.session.commit()

    # Reply with confirmation
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ Image received & saved!"))

# ===================================
# Retrieve Image from Database
# ===================================
@app.route("/get_image/<int:image_id>", methods=["GET"])
def get_image(image_id):
    image = ImageStorage.query.get(image_id)
    if not image:
        return jsonify({"error": "Image not found"}), 404

    return send_file(io.BytesIO(image.image_data), mimetype="image/jpeg")

# ===================================
# Upload Image via API
# ===================================
@app.route("/upload_image", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # ✅ Save image to PostgreSQL
    user_id = request.form.get("user_id", "unknown_user")
    image_data = file.read()
    
    image = ImageStorage(user_id=user_id, image_data=image_data, filename=file.filename)
    db.session.add(image)
    db.session.commit()

    return jsonify({"message": "Image uploaded successfully", "image_id": image.id})

# ===================================
# Get Chat History
# ===================================
@app.route("/history", methods=["GET"])
def get_history():
    try:
        chats = ChatHistory.query.all()
        history = [
            {"id": c.id, "user_id": c.user_id, "user_message": c.user_message, "bot_response": c.bot_response}
            for c in chats
        ]
        return jsonify(history), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
