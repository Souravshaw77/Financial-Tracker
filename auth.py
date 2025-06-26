from db import connect, hash_password

def register_user(username, password, email):
    with connect() as conn:
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                      (username, hash_password(password), email))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def validate_user(username, password):
    with connect() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", 
                  (username, hash_password(password)))
        return c.fetchone() is not None
