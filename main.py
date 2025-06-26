# main.py

from auth import register_user, validate_user
from expenses import insert_expense, fetch_expenses, delete_expense_by_id
from analytics import get_monthly_summary, get_category_summary
from export import export_expenses_to_csv
from budget import set_budget, get_spending_vs_budget, show_budget_progress
from db import initialize_db, connect
from dashboard import plot_monthly_expenses, plot_category_distribution

import getpass
import os

def delete_expense_by_id_cli(user_id):
    try:
        expense_id = int(input("Enter expense ID to delete: "))
        delete_expense_by_id(user_id, expense_id)
    except ValueError:
        print("❌ Invalid ID. Please enter a number.")

def main():
    print("\U0001F4B0 Welcome to Finance Tracker")
    initialize_db()

    # Login/Register loop
    while True:
        print("\n1. Register")
        print("2. Login")
        print("3. Exit")
        choice = input("Choose an option: ")

        if choice == '1':
            username = input("Enter new username: ")
            password = getpass.getpass("Enter password: ")
            if register_user(username, password):
                print("✅ Registered successfully. Please login.")
            else:
                print("❌ Username already exists.")
        
        elif choice == '2':
            username = input("Enter username: ")
            password = getpass.getpass("Enter password: ")
            if validate_user(username, password):
                print(f"✅ Welcome, {username}!")
                break
            else:
                print("❌ Invalid credentials.")

        elif choice == '3':
            print("👋 Exiting Finance Tracker.")
            return

        else:
            print("❌ Invalid option. Try again.")

    # Get user ID safely
    with connect() as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username=?", (username,))
        row = c.fetchone()
        if row:
            user_id = row[0]
        else:
            print("❌ Unexpected error: user not found in DB.")
            return

    # Main menu loop
    while True:
        print("\n\U0001F4CB Main Menu")
        print("1. Add Expense")
        print("2. View Expenses")
        print("3. Delete Expense")
        print("4. Monthly Summary")
        print("5. Category Summary")
        print("6. Export to CSV")
        print("7. Set Category Budget")
        print("8. View Budget Alerts")
        print("9. View Monthly Chart")
        print("10. View Category Chart")
        print("11. View Budget Progress")
        print("12. Logout")
        print("13. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            date = input("Enter date (YYYY-MM-DD): ")
            category = input("Enter category: ")
            try:
                amount = abs(float(input("Enter amount: ")))
            except ValueError:
                print("❌ Invalid amount. Please enter a number.")
                continue
            note = input("Enter note (optional): ")
            insert_expense(user_id, date, category, amount, note)
            print("✅ Expense added.")
            input("Press Enter to return to menu...")

        elif choice == '2':
            expenses = fetch_expenses(user_id)
            if not expenses:
                print("ℹ️ No expenses found.")
            else:
                print("\n📄 Your Expenses:")
                for e in expenses:
                    print(f"{e[0]} | {e[1]} | ₹{e[2]:.2f} | {e[3]} | ID: {e[4]}")
            input("Press Enter to return to menu...")

        elif choice == '3':
            delete_expense_by_id_cli(user_id)
            input("Press Enter to return to menu...")

        elif choice == '4':
            summary = get_monthly_summary(user_id)
            if not summary:
                print("ℹ️ No expense data available for summary.")
            else:
                print("\n📅 Monthly Summary:")
                for month, total in summary:
                    print(f"{month}: ₹{total:.2f}")
            input("Press Enter to return to menu...")

        elif choice == '5':
            summary = get_category_summary(user_id)
            if not summary:
                print("ℹ️ No category summary available.")
            else:
                print("\n📊 Category Summary:")
                for category, total in summary:
                    print(f"{category}: ₹{total:.2f}")
            input("Press Enter to return to menu...")

        elif choice == '6':
            filename = input("Enter filename (default: my_expenses_export.csv): ").strip()
            if filename == "":
                filename = "my_expenses_export.csv"
            os.makedirs("exports", exist_ok=True)
            export_expenses_to_csv(user_id, f"exports/{filename}")
            print(f"✅ Exported to exports/{filename}")
            input("Press Enter to return to menu...")

        elif choice == '7':
            cat = input("Enter category: ")
            try:
                limit = float(input("Enter monthly limit (₹): "))
                set_budget(user_id, cat, limit)
                print("✅ Budget set successfully.")
            except ValueError:
                print("❌ Invalid amount. Please enter a number.")
            input("Press Enter to return to menu...")

        elif choice == '8':
            alerts = get_spending_vs_budget(user_id)
            if alerts:
                print("\n🚨 Budget Alerts:")
                for cat, spent, limit in alerts:
                    print(f"Category: {cat} | Spent: ₹{spent:.2f} | Limit: ₹{limit:.2f}")
            else:
                print("✅ All spending is within budget.")
            input("Press Enter to return to menu...")

        elif choice == '9':
            plot_monthly_expenses(user_id)
            input("Press Enter to return to menu...")

        elif choice == '10':
            plot_category_distribution(user_id)
            input("Press Enter to return to menu...")

        elif choice == '11':
            show_budget_progress(user_id)
            input("Press Enter to return to menu...")

        elif choice == '12':
            print("🔐 Logged out.")
            return main()

        elif choice == '13':
            print("👋 Goodbye!")
            break

        else:
            print("❌ Invalid choice. Try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Exiting gracefully.")
