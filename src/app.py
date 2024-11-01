from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "supersecretkey"


# Database connection function
def get_db_connection():
    conn = sqlite3.connect('blood_bank.db')
    conn.row_factory = sqlite3.Row
    return conn


# Initialize the database tables
def init_db():
    conn = get_db_connection()

    # Drop tables if they exist (only for development)
    conn.execute("DROP TABLE IF EXISTS blood_inventory")
    conn.execute("DROP TABLE IF EXISTS donations")
    conn.execute("DROP TABLE IF EXISTS requests")

    # Create tables with the necessary columns
    conn.execute('''
        CREATE TABLE IF NOT EXISTS blood_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            blood_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            donor_name TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            phone TEXT NOT NULL,
            blood_type TEXT NOT NULL,
            quantity INTEGER NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            phone TEXT NOT NULL,
            blood_type TEXT NOT NULL,
            quantity INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


# Initialize the database when the application starts
init_db()


# Route for the main page
@app.route('/')
def index():
    conn = get_db_connection()
    blood_data = conn.execute("SELECT blood_type, quantity, donor_name FROM blood_inventory").fetchall()
    conn.close()
    return render_template('index.html', blood_data=blood_data)


# Route for handling blood donations
@app.route('/donate', methods=['POST'])
def donate():
    name = request.form['name']
    age = int(request.form['age'])
    phone = request.form['phone']
    blood_type = request.form['blood_type']
    quantity = int(request.form['quantity'])

    conn = get_db_connection()
    conn.execute("INSERT INTO donations (name, age, phone, blood_type, quantity) VALUES (?, ?, ?, ?, ?)",
                 (name, age, phone, blood_type, quantity))

    # Update or insert blood inventory
    existing = conn.execute("SELECT * FROM blood_inventory WHERE blood_type = ?", (blood_type,)).fetchone()
    if existing:
        conn.execute("UPDATE blood_inventory SET quantity = quantity + ?, donor_name = ? WHERE blood_type = ?",
                     (quantity, name, blood_type))
    else:
        conn.execute("INSERT INTO blood_inventory (blood_type, quantity, donor_name) VALUES (?, ?, ?)",
                     (blood_type, quantity, name))

    conn.commit()
    conn.close()
    flash("Thank you for your donation!")
    return redirect(url_for('index'))


# Route for handling blood requests
@app.route('/request_blood', methods=['POST'])
def request_blood():
    name = request.form['name']
    age = int(request.form['age'])
    phone = request.form['phone']
    blood_type = request.form['blood_type']
    quantity = int(request.form['quantity'])

    conn = get_db_connection()
    inventory = conn.execute("SELECT * FROM blood_inventory WHERE blood_type = ?", (blood_type,)).fetchone()

    if inventory and inventory['quantity'] >= quantity:
        # Update inventory and record request
        conn.execute("UPDATE blood_inventory SET quantity = quantity - ? WHERE blood_type = ?", (quantity, blood_type))
        conn.execute("INSERT INTO requests (name, age, phone, blood_type, quantity) VALUES (?, ?, ?, ?, ?)",
                     (name, age, phone, blood_type, quantity))
        conn.commit()
        flash("Blood request successful!")
    else:
        flash("Not available currently.")

    conn.close()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
