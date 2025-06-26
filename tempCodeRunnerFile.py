from flask import Flask, render_template, request, redirect, url_for, session, flash
from db import connect, initialize_db
from auth import register_user, validate_user
from expenses import insert_expense, fetch_expenses, delete_expense_by_id,fetch_monthly_summary
from analytics import get_monthly_summary, get_category_summary
from budget import set_budget, get_spending_vs_budget
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Replace with environment variable in production

initialize_db()

def get_db():
    return sqlite3.connect('finance.db')

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if register_user(username, password):
            flash("Registered successfully! Please log in.", "success")
            return redirect(url_for('login'))
        else:
            flash("Username already exists.", "danger")
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if validate_user(username, password):
            with connect() as conn:
                c = conn.cursor()
                c.execute("SELECT id FROM users WHERE username=?", (username,))
                user_id = c.fetchone()[0]
            session['username'] = username
            session['user_id'] = user_id
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials.", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    expenses = fetch_expenses(user_id)
    return render_template('dashboard.html', expenses=expenses, username=session['username'])

@app.route('/add', methods=['GET', 'POST'])
def add_expense():
    if 'username' not in session:
        return redirect(url_for('login'))

    user_id = session.get('user_id')

    if request.method == 'POST':
        date = request.form['date']
        trans_type = request.form['type']  # 'income' or 'expense'
        category = request.form['category']
        amount = float(request.form['amount'])
        note = request.form.get('note', '')

        # Convert expense to negative
        if trans_type == 'expense' and amount > 0:
            amount *= -1

        insert_expense(user_id, date, category, amount, note)
        flash("Transaction added!", "success")
        return redirect(url_for('dashboard'))

    return render_template('add_expense.html')

@app.route('/delete/<int:expense_id>')
def delete_expense(expense_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    delete_expense_by_id(expense_id, user_id)
    flash("Expense deleted!", "info")
    return redirect(url_for('dashboard'))

@app.route('/summary')
def summary():
    if 'username' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = sqlite3.connect('finance.db')
    c = conn.cursor()

    # Total income
    c.execute("SELECT SUM(amount) FROM expenses WHERE user_id=? AND amount > 0", (user_id,))
    income = c.fetchone()[0] or 0

    # Total expenses
    c.execute("SELECT SUM(amount) FROM expenses WHERE user_id=? AND amount < 0", (user_id,))
    total_expense = abs(c.fetchone()[0] or 0)

    # Group by category
    c.execute("""
        SELECT category, ABS(SUM(amount)) 
        FROM expenses 
        WHERE user_id=? AND amount < 0 
        GROUP BY category
    """, (user_id,))
    category_data = c.fetchall()
    conn.close()

    # Prepare labels and values for Chart.js
    chart_labels = [row[0] for row in category_data]
    chart_values = [row[1] for row in category_data]

    return render_template(
        "summary.html",
        income=income,
        total_expense=total_expense,
        chart_labels=chart_labels,
        chart_values=chart_values
    )


@app.route('/budget', methods=['GET', 'POST'])
def budget():
    if 'username' not in session:
        return redirect(url_for('login'))

    user_id = session.get('user_id')

    if request.method == 'POST':
        category = request.form['category']
        limit = float(request.form['limit'])
        set_budget(user_id, category, limit)
        flash("Budget set!", "success")

    alerts = get_spending_vs_budget(user_id)
    return render_template('budget.html', alerts=alerts)

if __name__ == '__main__':
    app.run(debug=True)
