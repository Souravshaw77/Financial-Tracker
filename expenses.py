import sqlite3
from db import connect

def insert_expense(user_id, date, trans_type, category, amount, note=""):
    with connect() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO expenses (user_id, date, type, category, amount, note)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, date, trans_type, category, amount, note))
        conn.commit()
        print("✅ Expense added.")



def fetch_expenses(user_id):
    with connect() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT id, date, category, amount, note, type
            FROM expenses
            WHERE user_id = ?
            ORDER BY date DESC
        """, (user_id,))
        rows = c.fetchall()
        
        expenses = [
            {
                "id": row[0],
                "date": row[1],
                "category": row[2],
                "amount": row[3],
                "note": row[4],
                "type": row[5]
            }
            for row in rows
        ]
        return expenses


def delete_expense_by_id(expense_id, user_id):
    with connect() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM expenses WHERE id=? AND user_id=?", (expense_id, user_id))
        conn.commit()

def fetch_monthly_summary(user_id):
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT category, SUM(amount) 
        FROM expenses
        WHERE user_id = ? 
          AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')  -- current month
        GROUP BY category
    ''', (user_id,))
    summary = cursor.fetchall()
    conn.close()
    return summary
