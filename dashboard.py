# dashboard.py
import matplotlib.pyplot as plt
from db import connect

def plot_monthly_expenses(user_id):
    from db import connect
    import matplotlib.pyplot as plt

    with connect() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT strftime('%Y-%m', date) AS month, SUM(amount)
            FROM expenses
            WHERE user_id = ?
            GROUP BY month
        ''', (user_id,))
        rows = c.fetchall()

    # Filter out rows where month is None
    clean_data = [(m, t) for m, t in rows if m is not None]

    if not clean_data:
        print("⚠️ No valid monthly expense data to show.")
        return

    months, totals = zip(*clean_data)

    plt.bar(months, totals, color='skyblue')
    plt.xlabel("Month")
    plt.ylabel("Total Expenses (₹)")
    plt.title("Monthly Expense Summary")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def plot_category_distribution(user_id):
    with connect() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT category, SUM(amount)
            FROM expenses
            WHERE user_id=?
            GROUP BY category
        """, (user_id,))
        data = c.fetchall()

    if not data:
        print("📭 No category data to plot.")
        return

    categories, totals = zip(*data)
    plt.figure(figsize=(6, 6))
    plt.pie(totals, labels=categories, autopct="%1.1f%%", startangle=140)
    plt.title("Spending by Category")
    plt.tight_layout()
    plt.show()
