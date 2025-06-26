import sqlite3

conn = sqlite3.connect('finance.db')
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(expenses)")
columns = cursor.fetchall()

for column in columns:
    print(column)

conn.close()
