from db import connect

def get_monthly_summary(user_id):
    with connect() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT strftime('%Y-%m', date) as month, 
                   SUM(amount) as total 
            FROM expenses 
            WHERE user_id = ? 
            GROUP BY month 
            ORDER BY month DESC
        ''', (user_id,))
        return c.fetchall()

def get_category_summary(user_id):
    with connect() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT category, SUM(amount) as total 
            FROM expenses 
            WHERE user_id = ? 
            GROUP BY category 
            ORDER BY total DESC
        ''', (user_id,))
        return c.fetchall()
