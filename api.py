from flask import Flask, request, jsonify
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


@app.route("/activate", methods=["POST"])
def activate():

    data = request.json

    if not data:
        return jsonify({
            "status": "error",
            "message": "No data"
        })

    key = data.get("key")

    if not key:
        return jsonify({
            "status": "error",
            "message": "No key"
        })

    user_ip = request.remote_addr

    return jsonify({
        "status": "success",
        "key": key,
        "ip": user_ip
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
