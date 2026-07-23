from flask import Flask, request
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "API Running"

@app.route("/ip")
def get_ip():
    return {
        "ip": request.remote_addr
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
