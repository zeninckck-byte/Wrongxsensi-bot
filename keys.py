import secrets
from datetime import datetime, timedelta

def generate_key(days):
    key = "WRONG-" + secrets.token_hex(4).upper()
    expiry = datetime.now() + timedelta(days=days)
    return key, expiry.strftime("%Y-%m-%d %H:%M:%S")
