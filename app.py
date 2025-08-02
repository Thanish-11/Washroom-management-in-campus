from flask import Flask, render_template, request, redirect, session, flash, url_for
import sqlite3
import os
from datetime import datetime
from dataset import create_dataset
from recognition import FaceRecognition

app = Flask(__name__)
app.secret_key = "your_sescret_key"
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        password TEXT NOT NULL
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        password TEXT NOT NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS maintainance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS feedbacks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_path TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    image_path TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.commit()
conn.close()

# Home route (renders both forms)
@app.route('/')
def index():
    return render_template('index.html')

# Home route (renders both forms)
@app.route('/mentain')
def mentain():
    return render_template('mentain.html')

# Home route (renders both forms)
@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/signup', methods=['POST'])
def signup():
    name = request.form['name']
    password = request.form['password']
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (name, password) VALUES (?, ?)", (name, password))
    conn.commit()
    conn.close()
    return render_template('index.html', msg="Registration successfull")

@app.route('/signin', methods=['POST'])
def signin():
    name = request.form['name']
    password = request.form['password']
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE name = ? AND password = ?", (name, password))
    user = cursor.fetchone()
    conn.close()
    if user:
        return render_template('studentlog.html')
    else:
        return render_template('index.html', msg="Entered wrong credantials")

@app.route('/adminsignup', methods=['POST'])
def adminsignup():
    name = request.form['name']
    password = request.form['password']
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO admin (name, password) VALUES (?, ?)", (name, password))
    conn.commit()
    conn.close()
    return render_template('admin.html', msg="Registration successfull")

@app.route('/feedbacks')
def feedbacks():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT image_path, message, timestamp FROM feedbacks ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    return render_template('adminlog.html', feedbacks=rows)

@app.route('/maintainanceupdates')
def maintainanceupdates():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, image_path, timestamp FROM updates ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    return render_template('maintainanceupdates.html', feedbacks=rows)

@app.route('/adminsignin', methods=['POST'])
def adminsignin():
    name = request.form['name']
    password = request.form['password']
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admin WHERE name = ? AND password = ?", (name, password))
    user = cursor.fetchone()
    conn.close()
    if user:
        return redirect(url_for('feedbacks'))
    else:
        return render_template('admin.html', msg="Entered wrong credantials")

@app.route('/maintainsignup', methods=['POST'])
def maintainsignup():
    try:
        name = request.form['name']
        password = request.form['password']
        try:
            create_dataset(name)
        except Exception as e:
            print(e)
            return render_template('mentain.html', msg="Something went wrong")
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO maintainance (name, password) VALUES (?, ?)", (name, password))
        conn.commit()
        conn.close()
        return render_template('mentain.html', msg="Registration successfull")
    except:
        return render_template('mentain.html', msg="Username already exists. Try again")

@app.route('/maintainsignin', methods=['POST'])
def maintainsignin():
    name = request.form['name']
    password = request.form['password']
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM maintainance WHERE name = ? AND password = ?", (name, password))
    user = cursor.fetchone()
    conn.close()
    if user:
        res = FaceRecognition()
        if res != 'unknown':
            session['maintainance'] = res
            return render_template('maintainancelog.html')
        else:
            return render_template('mentain.html', msg="Unknown person")
    else:
        return render_template('mentain.html', msg="Entered wrong credantials")

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    feedback = request.form.get('feedback', '').strip()
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    filepath = filepath.replace('\\', '/')
    file.save(filepath)

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO feedbacks (image_path, message, timestamp) VALUES (?, ?, ?)",
        (filepath, feedback, datetime.now())
    )
    conn.commit()
    conn.close()

    return render_template('studentlog.html', msg="Uploaded successfully")


@app.route('/updates', methods=['POST'])
def updates():
    name = session['maintainance']
    file = request.files['file']
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    filepath = filepath.replace('\\', '/')
    file.save(filepath)

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO updates (name, image_path, timestamp) VALUES (?, ?, ?)",
        (name, filepath, datetime.now())
    )
    conn.commit()
    conn.close()

    return render_template('maintainancelog.html', msg="Uploaded successfully")

@app.route('/logout')
def logout():
    return render_template('index.html')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)