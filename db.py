
import sqlite3
import hashlib

DB_PATH = "instance/expenses.db"

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user_table():
    with connect() as conn:
        c = conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )''')
        conn.commit()

def create_expense_table():
    with connect() as conn:
        cursor = conn.cursor()

        # Create the table if it doesn't exist (with 'type' column included)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                date TEXT,
                type TEXT DEFAULT 'expense',  -- ✅ Add this
                category TEXT,
                amount REAL,
                note TEXT
            )
        ''')

        # Check if 'type' column exists
        cursor.execute("PRAGMA table_info(expenses)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'type' not in columns:
            try:
                cursor.execute("ALTER TABLE expenses ADD COLUMN type TEXT DEFAULT 'expense'")
                print("✅ Added 'type' column to existing 'expenses' table.")
            except sqlite3.OperationalError as e:
                print("⚠️ Could not add 'type' column:", e)

        conn.commit()
def create_budget_table():
    with connect() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")  # enable foreign key support
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                monthly_limit REAL,
                UNIQUE(user_id, category),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        conn.commit()

def get_monthly_total(user_id):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        SELECT SUM(amount)
        FROM expenses
        WHERE user_id = ? AND amount > 0 AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
    """, (user_id,))
    result = c.fetchone()
    return result[0] if result and result[0] else 0



def get_category_summary(user_id):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        SELECT category, SUM(amount)
        FROM expenses
        WHERE user_id = ? AND amount > 0 AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
        GROUP BY category
    """, (user_id,))
    return c.fetchall()



def initialize_db():
    create_user_table()
    create_expense_table()
    create_budget_table()
    print("✅ Database initialized.")
