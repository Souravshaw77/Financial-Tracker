from flask import Flask, render_template, request, redirect, url_for, session, flash,send_file
from db import connect, initialize_db
from auth import register_user, validate_user
from expenses import insert_expense, fetch_expenses, delete_expense_by_id,fetch_monthly_summary
from analytics import get_monthly_summary, get_category_summary
from budget import set_budget, get_spending_vs_budget
import sqlite3
from datetime import datetime
from flask_mail import Mail, Message
from budget import get_spending_vs_budget
import smtplib
from email.mime.text import MIMEText
import io
import matplotlib  # ✅ First import matplotlib
matplotlib.use('Agg')  # ✅ Then set the non-GUI backend
from matplotlib import pyplot as plt 
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Replace with environment variable in production

initialize_db()

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'msdseven45@gmail.com'  # 🔒 use env variable in prod
app.config['MAIL_PASSWORD'] = '1234'     # 🔒 not your Gmail password
app.config['MAIL_DEFAULT_SENDER'] = 'youremail@gmail.com'

mail = Mail(app)



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
        email = request.form['email']  

       
        if register_user(username, password, email):
            flash("✅ Registered successfully! Please log in.", "success")
            return redirect(url_for('login'))
        else:
            flash("❌ Username already exists.", "danger")

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


@app.route('/delete/<int:expense_id>', methods=['POST'])
def delete_expense_by_id(expense_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    with connect() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM expenses WHERE id=? AND user_id=?", (expense_id, session['user_id']))
        conn.commit()
        flash('🗑️ Expense deleted successfully.')
    return redirect(url_for('dashboard'))


@app.route('/edit/<int:expense_id>', methods=['GET', 'POST'])
def edit_expense(expense_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    with connect() as conn:
        c = conn.cursor()
        if request.method == 'POST':
            # Update the expense
            date = request.form['date']
            category = request.form['category']
            amount = float(request.form['amount'])
            note = request.form['note']

            c.execute("""
                UPDATE expenses
                SET date=?, category=?, amount=?, note=?
                WHERE id=? AND user_id=?
            """, (date, category, amount, note, expense_id, session['user_id']))
            conn.commit()
            flash('✅ Expense updated successfully.')
            return redirect(url_for('dashboard'))

        # GET: Show the form with existing data
        c.execute("SELECT * FROM expenses WHERE id=? AND user_id=?", (expense_id, session['user_id']))
        expense = c.fetchone()
        if expense:
            expense_dict = {
                'id': expense[0],
                'date': expense[1],
                'category': expense[2],
                'amount': expense[3],
                'note': expense[4]
            }
            return render_template('edit_expense.html', expense=expense_dict)
        else:
            flash("❌ Expense not found.")
            return redirect(url_for('dashboard'))


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
    print("Fetched expenses for user:", expenses)
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


        insert_expense(user_id, date, trans_type, category, amount, note)

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
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')

    summary = get_category_summary(user_id)
    print("DEBUG Summary from DB:", summary)  # 👈 Add this line

    chart_labels = [item[0] for item in summary]
    chart_values = [item[1] for item in summary]

    total_expense = sum(chart_values)

    return render_template('summary.html',
                           total_expense=total_expense,
                           chart_labels=chart_labels,
                           chart_values=chart_values)


@app.route('/budget', methods=['GET', 'POST'])
def budget():
    if 'username' not in session:
        return redirect(url_for('login'))

    user_id = session.get('user_id')

    if request.method == 'POST':
        category = request.form['category']
        limit = float(request.form['limit'])

        # Save or update budget
        set_budget(user_id, category, limit)
        flash(f"✅ Budget for '{category}' set to ₹{limit}", "success")
        return redirect(url_for('budget'))
    
    alerts = get_spending_vs_budget(user_id)
    # Fetch current budgets
    with connect() as conn:
        c = conn.cursor()
        c.execute("SELECT category, monthly_limit FROM budgets WHERE user_id=?", (user_id,))
        budgets = [{'category': row[0], 'limit': row[1]} for row in c.fetchall()]

    # Check current alerts
    alerts = get_spending_vs_budget(user_id)

    # ✅ Optional: Email alerts only if they exist
    if alerts:
        user_email = 'youremail@gmail.com'  # Replace with actual user email if stored in DB
        body = "\n".join(alerts)
        try:
            send_alert_email(user_email, "⚠️ Budget Alert: Limit Exceeded", body)
        except Exception as e:
            print("📧 Email send failed:", e)

    return render_template('budget.html', budgets=budgets, alerts=alerts)


@app.route("/budget-alert")
def budget_alert():
    if 'username' not in session:
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    alerts = get_spending_vs_budget(user_id)
    return render_template("budget_alert.html", alerts=alerts)


def send_alert_email(to_email, subject, body):
    sender_email = "sourav.shaw9122003@gmail.com"
    sender_password = "nveg fjvm very yovk"  # Use an App Password from Gmail settings

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print("📧 Email sent successfully!")
    except Exception as e:
        print("📧 Email send failed:", e)

@app.route('/export/pdf')
def export_pdf():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    print("Current logged in user ID:", user_id)
    expenses = fetch_expenses(user_id)  # 👈 Your function that fetches all expenses
    print("DEBUG - fetched expenses:", expenses)
    # ✅ Step: Filter only type='expense'
    expense_items = [e for e in expenses if e.get("type") == "expense"]
   
    # ✅ Step: Aggregate totals by category
    category_totals = {}
    for exp in expense_items:
        cat = exp["category"]
        amt = abs(exp["amount"])  # Ensures values are positive
        category_totals[cat] = category_totals.get(cat, 0) + amt

    if not category_totals:
        return "No expense data available for export."
    fig, ax = plt.subplots()
    ax.pie(category_totals.values(), labels=category_totals.keys(), autopct='%1.1f%%')
    ax.set_title("Spending by Category")
    chart_io = io.BytesIO()
    plt.savefig(chart_io, format='PNG')
    plt.close(fig)
    chart_io.seek(0)

    # ✅ Step: Generate PDF with pie chart and text
    pdf_buffer = io.BytesIO()
    p = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter
    p.setFont("Helvetica-Bold", 14)
    p.drawString(180, height - 50, "Monthly Expense Report")
    p.drawImage(ImageReader(chart_io), 130, height - 350, width=300, preserveAspectRatio=True)

    y = height - 380
    p.setFont("Helvetica", 10)
    for cat, amt in category_totals.items():
        y -= 15
        p.drawString(50, y, f"{cat}: ₹{amt:.2f}")

    p.showPage()
    p.save()
    pdf_buffer.seek(0)

    return send_file(pdf_buffer, download_name="monthly_report.pdf", as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
