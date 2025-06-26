import csv
from db import connect

def export_expenses_to_csv(user_id, filename="my_expenses_export.csv"):
    with connect() as conn:
        c = conn.cursor()
        c.execute("SELECT date, category, amount, note FROM expenses WHERE user_id=? ORDER BY date DESC", 
                  (user_id,))
        rows = c.fetchall()

    if not rows:
        print("⚠️ No expenses to export.")
        return

    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Category', 'Amount', 'Note'])
        writer.writerows(rows)
        print(f"✅ Exported {len(rows)} expenses to {filename}")
