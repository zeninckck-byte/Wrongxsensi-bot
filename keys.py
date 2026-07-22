import secrets

def generate_key():
    return "WRONG-" + secrets.token_hex(4).upper()
