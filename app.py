from flask import Flask, request
import json

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("Received:", json.dumps(data, indent=2))
    return "OK"

if __name__ == "__main__":
    app.run(port=5000)
