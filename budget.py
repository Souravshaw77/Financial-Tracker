from db import connect
from datetime import datetime

def set_budget(user_id, category, monthly_limit):
    with connect() as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO budgets (user_id, category, monthly_limit)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, category) DO UPDATE SET monthly_limit=excluded.monthly_limit
        ''', (user_id, category, monthly_limit))
        conn.commit()
        print(f"✅ Budget for '{category}' set to ₹{monthly_limit:.2f}")

def get_budgets(user_id):
    with connect() as conn:
        c = conn.cursor()
        c.execute("SELECT category, monthly_limit FROM budgets WHERE user_id=?", (user_id,))
        return dict(c.fetchall())

def get_spending_vs_budget(user_id):
    with connect() as conn:
        c = conn.cursor()
        # Sum actual expenses
        c.execute('''
            SELECT category, SUM(amount) 
            FROM expenses 
            WHERE user_id=?
            GROUP BY category
        ''', (user_id,))
        actuals = dict(c.fetchall())

        # Get budgets
        budgets = get_budgets(user_id)

        # Compare
        alerts = []
        for cat, monthly_limit in budgets.items():
            spent = actuals.get(cat, 0)
            if spent > monthly_limit:
                alerts.append((cat, spent, monthly_limit))
        return alerts
# budget.py (append this at the end)

def show_budget_progress(user_id):
    with connect() as conn:
        c = conn.cursor()

        # Get total spent per category
        c.execute("""
            SELECT category, SUM(amount)
            FROM expenses
            WHERE user_id=?
            GROUP BY category
        """, (user_id,))
        spent_by_category = dict(c.fetchall())

        # Get budget limits
        budgets = get_budgets(user_id)

        if not budgets:
            print("📭 No budgets set.")
            return

        print("\n📈 Budget Progress:")
        for category, limit in budgets.items():
            spent = spent_by_category.get(category, 0)
            percent = (spent / limit) * 100 if limit else 0
            bar = progress_bar(percent)
            status = "✅ OK" if percent <= 100 else "🚨 Over"
            print(f"{category:15} ₹{spent:.2f} / ₹{limit:.2f} [{bar}] {percent:.1f}% {status}")

def progress_bar(percent, width=20):
    filled = int(width * min(percent, 100) / 100)
    empty = width - filled
    return "█" * filled + "-" * empty

def get_spending_vs_budget(user_id):
    with connect() as conn:
        c = conn.cursor()

        # Get total spent per category this month
        first_day = datetime.today().replace(day=1).strftime('%Y-%m-%d')
        today = datetime.today().strftime('%Y-%m-%d')

        c.execute("""
            SELECT category, SUM(amount) 
            FROM expenses
            WHERE user_id=? AND type='expense' AND date BETWEEN ? AND ?
            GROUP BY category
        """, (user_id, first_day, today))
        spent = dict(c.fetchall())  # {'food': 400, 'rent': 1200, ...}

        # Get budgets
        c.execute("SELECT category, monthly_limit FROM budgets WHERE user_id=?", (user_id,))
        budgets = dict(c.fetchall())  # {'food': 300, 'rent': 1500, ...}

        # Compare and return alerts
        alerts = []
        for category, limit in budgets.items():
            spent_amt = spent.get(category, 0)
            if spent_amt > limit:
                alerts.append(f"⚠️ You spent ₹{spent_amt:.2f} on {category} (limit: ₹{limit})")
        return alerts