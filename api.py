from flask import Flask, request, jsonify
import os
import sqlite3

app = Flask(__name__)

def save_ip(key, ip):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE keys SET ip=? WHERE key=?",
        (ip, key)
    )

    conn.commit()
    conn.close()


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

    key = data.get("key")

    if not key:
        return jsonify({
            "status": "error",
            "message": "No key"
        })

    user_ip = request.remote_addr

    save_ip(key, user_ip)

    return jsonify({
        "status": "success",
        "key": key,
        "ip": user_ip
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
