import sqlite3

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS keys (
    key TEXT PRIMARY KEY,
    used INTEGER DEFAULT 0
)
""")

conn.commit()

def save_key(key):
    cursor.execute("INSERT INTO keys (key) VALUES (?)", (key,))
    conn.commit()

def key_exists(key):
    cursor.execute("SELECT * FROM keys WHERE key=?", (key,))
    return cursor.fetchone()

def use_key(key):
    cursor.execute("UPDATE keys SET used=1 WHERE key=?", (key,))
    conn.commit()

def is_used(key):
    cursor.execute("SELECT used FROM keys WHERE key=?", (key,))
    row = cursor.fetchone()
    return row and row[0] == 1

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
