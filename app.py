from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = '0000'

# Database setup
def init_db():
    conn = sqlite3.connect('todo.db')
    c = conn.cursor()
        "/home/malak/.vscode/extensions/algoritmika.algopython-20251111.203400.0/temp/to-do list/.venv/bin/python" app.py
    # Create todos table
    c.execute('''
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            completed BOOLEAN NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('todo.db')
    conn.row_factory = sqlite3.Row
    return conn

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    todos = conn.execute(
        'SELECT * FROM todos WHERE user_id = ? ORDER BY created_at DESC',
        (session['user_id'],)
    ).fetchall()
    conn.close()
    return render_template('index.html', todos=todos, username=session.get('username'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please fill in all fields.', 'error')
            return render_template('login.html')
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([username, email, password, confirm_password]):
            flash('Please fill in all fields.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('register.html')
        
        conn = get_db_connection()
        
        # Check if username or email already exists
        existing_user = conn.execute(
            'SELECT * FROM users WHERE username = ? OR email = ?', 
            (username, email)
        ).fetchone()
        
        if existing_user:
            flash('Username or email already exists.', 'error')
            conn.close()
            return render_template('register.html')
        
        # Create new user
        password_hash = generate_password_hash(password)
        conn.execute(
            'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
            (username, email, password_hash)
        )
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/add', methods=['POST'])
@login_required
def add_task():
    task = request.form.get('task')
    if task:
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO todos (task, user_id) VALUES (?, ?)',
            (task, session['user_id'])
        )
        conn.commit()
        conn.close()
        flash('Task added successfully!', 'success')
    else:
        flash('Please enter a task!', 'error')
    return redirect(url_for('index'))

@app.route('/complete/<int:todo_id>')
@login_required
def complete_todo(todo_id):
    conn = get_db_connection()
    todo = conn.execute(
        'SELECT * FROM todos WHERE id = ? AND user_id = ?', 
        (todo_id, session['user_id'])
    ).fetchone()
    
    if todo:
        new_status = not todo['completed']
        conn.execute(
            'UPDATE todos SET completed = ? WHERE id = ? AND user_id = ?',
            (new_status, todo_id, session['user_id'])
        )
        conn.commit()
        flash('Task updated!', 'success')
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:todo_id>')
@login_required
def delete_todo(todo_id):
    conn = get_db_connection()
    conn.execute(
        'DELETE FROM todos WHERE id = ? AND user_id = ?', 
        (todo_id, session['user_id'])
    )
    conn.commit()
    conn.close()
    flash('Task deleted!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)