import sqlite3
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

username = "Sourav"
new_password = "your_new_password"

with sqlite3.connect("expenses.db") as conn:
    c = conn.cursor()
    hashed = hash_password(new_password)
    c.execute("UPDATE users SET password=? WHERE username=?", (hashed, username))
    conn.commit()
    print("✅ Password reset for", username)
