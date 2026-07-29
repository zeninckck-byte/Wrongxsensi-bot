from flask import Flask, request, jsonify
import os

app = Flask(__name__)

def get_client_ip():
    # Railway passes the real user IP through X-Forwarded-For
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # The first IP in the comma-separated list is the original client
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr

@app.route("/")
def home():
    return "API Running"


@app.route("/ip")
def get_ip():
    return {
        "ip": get_client_ip()
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

    user_ip = get_client_ip()

    return jsonify({
        "status": "success",
        "key": key,
        "ip": user_ip
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8081))
    app.run(host="0.0.0.0", port=port)
