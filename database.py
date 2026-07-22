import sqlite3

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS keys (
    key TEXT PRIMARY KEY,
    expiry TEXT,
    used INTEGER DEFAULT 0
)
""")

conn.commit()


def save_key(key, expiry):
    cursor.execute(
        "INSERT INTO keys (key, expiry) VALUES (?, ?)",
        (key, expiry)
    )
    conn.commit()


def get_key(key):
    cursor.execute(
        "SELECT key, expiry, used FROM keys WHERE key=?",
        (key,)
    )
    return cursor.fetchone()


def mark_used(key):
    cursor.execute(
        "UPDATE keys SET used=1 WHERE key=?",
        (key,)
    )
    conn.commit()


def reset_key(key):
    cursor.execute(
        "UPDATE keys SET used=0 WHERE key=?",
        (key,)
    )
    conn.commit()
