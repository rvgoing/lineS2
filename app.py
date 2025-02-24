import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from werkzeug.utils import secure_filename



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

# Define ChatHistory Model
class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)
    user_message = db.Column(db.String(500), nullable=True)
    bot_response = db.Column(db.String(500), nullable=True)
    image_data = db.Column(db.LargeBinary, nullable=True)  # Store image binary data
    image_type = db.Column(db.String(50), nullable=True)  # Store file type

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
# Handle process
# ===================================
# ✅ Handle Text Messages
# Handle text messages from users
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    user_id = event.source.user_id

    # Simple bot response logic
    bot_response = f"You said: {user_message}"

    # Save to database
    chat = ChatHistory(user_id=user_id, user_message=user_message, bot_response=bot_response)
    db.session.add(chat)
    db.session.commit()

    # Reply to user
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

# Route to get chat history
@app.route("/history", methods=["GET"])
def get_history():
    try:
        # Query all chat history from PostgreSQL
        chats = ChatHistory.query.all()
        
        # Convert the chat records into a JSON response
        history = [
            {
                "id": chat.id,
                "user_id": chat.user_id,
                "user_message": chat.user_message,
                "bot_response": chat.bot_response
            }
            for chat in chats
        ]

        return jsonify(history), 200  # Return JSON response with HTTP 200 (OK)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Return error message if something goes wrong

if __name__ == "__main__":
    app.run(debug=True)
