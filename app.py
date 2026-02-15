from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import sqlite3
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

if not os.path.exists('uploads'):
    os.makedirs('uploads')

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Users table (for student + admin)
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')

    # Orders table
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            filename TEXT,
            print_type TEXT,
            pages INTEGER,
            token INTEGER,
            contact TEXT,
            total_price INTEGER,
            status TEXT,
            payment_screenshot TEXT
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# HOME
@app.route('/')
def index():
    return render_template('index.html')

# =========================
# REGISTER
# =========================
@app.route('/register/<role>', methods=['GET','POST'])
def register(role):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        try:
            c.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                      (username,password,role))
            conn.commit()
        except:
            return "Username already exists!"

        conn.close()
        return redirect(url_for('login', role=role))

    return render_template('register.html', role=role)

# =========================
# LOGIN
# =========================
@app.route('/login/<role>', methods=['GET','POST'])
def login(role):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=? AND role=?",
                  (username,password,role))
        user = c.fetchone()
        conn.close()

        if user:
            if role == "student":
                return redirect(url_for('student_dashboard', username=username))
            else:
                return redirect(url_for('admin_dashboard'))
        else:
            return "Invalid Login!"

    return render_template('login.html', role=role)

# =========================
# STUDENT DASHBOARD
# =========================
@app.route('/student-dashboard/<username>', methods=['GET','POST'])
def student_dashboard(username):
    if request.method == 'POST':
        file = request.files['document']
        print_type = request.form['print_type']
        pages = int(request.form['pages'])
        contact = request.form['contact']
        payment = request.files['payment']

        price = 5 if print_type == "bw" else 10
        total = price * pages

        filename = file.filename
        payment_name = payment.filename

        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        payment.save(os.path.join(app.config['UPLOAD_FOLDER'], payment_name))

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute("SELECT MAX(token) FROM orders")
        last_token = c.fetchone()[0]
        token = 1 if last_token is None else last_token + 1

        c.execute('''
            INSERT INTO orders
            (username, filename, print_type, pages, token, contact, total_price, status, payment_screenshot)
            VALUES (?,?,?,?,?,?,?,?,?)
        ''',(username, filename, print_type, pages, token, contact, total, "Pending", payment_name))

        conn.commit()
        conn.close()

        return redirect(url_for('student_status', token=token))

    return render_template('student_dashboard.html', username=username)

# =========================
# STUDENT STATUS
# =========================
@app.route('/student-status/<int:token>')
def student_status(token):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT status FROM orders WHERE token=?", (token,))
    status = c.fetchone()[0]
    conn.close()
    return render_template('student_status.html', token=token, status=status)

# =========================
# ADMIN DASHBOARD
# =========================
@app.route('/admin-dashboard', methods=['GET','POST'])
def admin_dashboard():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    if request.method == 'POST':
        token = request.form['token']
        status = request.form['status']
        c.execute("UPDATE orders SET status=? WHERE token=?", (status, token))
        conn.commit()

    c.execute("SELECT * FROM orders ORDER BY token ASC")
    orders = c.fetchall()
    conn.close()

    return render_template('admin_dashboard.html', orders=orders)

# FILE SERVE
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)