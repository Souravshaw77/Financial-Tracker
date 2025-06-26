import sqlite3

conn = sqlite3.connect('finance.db')
cursor = conn.cursor()

# Create the expenses table
cursor.execute('''
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    date TEXT NOT NULL,
    category TEXT NOT NULL,
    amount REAL NOT NULL,
    note TEXT
)
''')

conn.commit()
conn.close()

print("✅ Table 'expenses' created successfully.")
