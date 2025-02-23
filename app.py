import os
import base64
from flask import Flask, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  # Import Flask-Migrate
from io import BytesIO
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

# ===================================
# PostgreSQL process
# ===================================

# PostgreSQL Database Config (Render)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://linebots1_user:x5XSGS3mtdDq2urm52I2kwHksHdhsVYM@dpg-cusib1vnoe9s738vfsl0-a/linebots1")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Initialize Flask-Migrate

# Database Model for Images
class LineImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.String(50), unique=True, nullable=False)
    image_data = db.Column(db.LargeBinary, nullable=False)  # Store image as binary

    def __init__(self, message_id, image_data):
        self.message_id = message_id
        self.image_data = image_data
        
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
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_message = event.message.text
    reply_text = f"You said: {user_message}"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

# Handle image messages
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    message_id = event.message.id

    # Get image from Line API
    image_content = line_bot_api.get_message_content(message_id)
    image_binary = b"".join(chunk for chunk in image_content.iter_content())

    # Save image in PostgreSQL
    new_image = LineImage(message_id=message_id, image_data=image_binary)
    db.session.add(new_image)
    db.session.commit()

    # Generate image URL
    image_url = f"{request.host_url}get_image/{message_id}"

    # Reply with the stored image
    line_bot_api.reply_message(event.reply_token, ImageSendMessage(
        original_content_url=image_url,
        preview_image_url=image_url
    ))

# Route to serve images from PostgreSQL
@app.route("/get_image/<message_id>")
def get_image(message_id):
    image_record = LineImage.query.filter_by(message_id=message_id).first()

    if image_record:
        return send_file(
            BytesIO(image_record.image_data),
            mimetype="image/jpeg",
            as_attachment=False
        )
    else:
        return "Image not found", 404

# Run Flask App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
