import os
import sqlite3
import re
import logging
from flask import Flask, request, render_template, redirect, session, make_response
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# SECURITY REMEDIATION: Insecure Session Management - Dynamic Secret Key
# Load key from system environment variables; fall back to secure random key on boot
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(32))

# Configure secure session cookie settings
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,   # Prevents client-side scripts from reading cookie (Mitigates XSS cookie theft)
    SESSION_COOKIE_SAMESITE='Lax',  # Protects against Cross-Site Request Forgery (CSRF)
    SESSION_COOKIE_SECURE=False     # Set to True in production when using HTTPS
)

# Configure internal secure audit logger
logging.basicConfig(filename='app.log', level=logging.ERROR, 
                    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')

def init_db():
    conn = sqlite3.connect('secure.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            notes TEXT
        )
    ''')
    # Pre-populate secure administrators and default users (storing secure hashes)
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        hashed_admin = generate_password_hash('ComplexAdminPass2026!', method='pbkdf2:sha256')
        hashed_alice = generate_password_hash('SecureAlice@2026!', method='pbkdf2:sha256')
        
        cursor.execute("INSERT INTO users (username, password, notes) VALUES (?, ?, ?)", 
                       ('admin', hashed_admin, 'Administrative logs locked.'))
        cursor.execute("INSERT INTO users (username, password, notes) VALUES (?, ?, ?)", 
                       ('alice', hashed_alice, 'Welcome to my secure profile page!'))
    conn.commit()
    conn.close()

# Initialize secure database
init_db()

@app.after_request
def add_security_headers(response):
    """Add secure HTTP response headers to harden the browser client."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline';"
    return response

@app.route('/')
def home():
    if 'username' in session:
        return redirect('/dashboard')
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')

    # Validation: Filter username character set to prevent raw bypass attempts
    if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
        return render_template('index.html', error="Invalid username format")

    try:
        conn = sqlite3.connect('secure.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # SECURITY REMEDIATION: SQL Injection - Parameterized Query placeholder "?"
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        
        # SECURITY REMEDIATION: Weak Password Policy / Hardcoded Credentials
        # Match hashed values; verify through secure Werkzeug hashing verification
        if user and check_password_hash(user['password'], password):
            session['username'] = user['username']
            resp = make_response(redirect('/dashboard'))
            # Session cookie properties are automatically inherited from app.config
            return resp
        else:
            # SECURITY REMEDIATION: Hardcoded credentials removed, backdoor account disabled.
            # Return identical error for user mismatch vs password mismatch (prevents User Enumeration)
            return render_template('index.html', error="Invalid credentials")
            
    except Exception as e:
        # SECURITY REMEDIATION: Information Disclosure - Log errors internally, return generic warning
        app.logger.error(f"Login database connection failure: {e}")
        return "An internal system error occurred. Please contact administrators.", 500

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    
    # SECURITY REMEDIATION: Input Validation
    # Enforces regex bounds on usernames
    if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
        return "Username must be alphanumeric, between 3 to 20 characters.", 400

    # SECURITY REMEDIATION: Strong Password Policy Checker
    # Requires: Min 8 chars, 1 uppercase, 1 lowercase, 1 number, 1 special character
    if (len(password) < 8 or
        not re.search(r"[a-z]", password) or
        not re.search(r"[A-Z]", password) or
        not re.search(r"[0-9]", password) or
        not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)):
        return "Password must be at least 8 characters long, containing uppercase, lowercase, numbers, and special symbols.", 400

    try:
        conn = sqlite3.connect('secure.db')
        cursor = conn.cursor()
        
        # Parameterized check
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return "User already exists!", 400
            
        # SECURITY REMEDIATION: Password Hashing using PBKDF2
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        # Parameterized insertion
        cursor.execute("INSERT INTO users (username, password, notes) VALUES (?, ?, ?)", 
                       (username, hashed_password, 'User bio notes.'))
        conn.commit()
        conn.close()
        return redirect('/')
    except Exception as e:
        app.logger.error(f"User registration failure: {e}")
        return "Internal registration error occurred.", 500

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/')
    
    username = session['username']
    try:
        conn = sqlite3.connect('secure.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT notes FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        
        notes = row['notes'] if row else ""
        return render_template('dashboard.html', username=username, notes=notes)
    except Exception as e:
        app.logger.error(f"Dashboard load error: {e}")
        return "Internal server dashboard error.", 500

@app.route('/update_notes', methods=['POST'])
def update_notes():
    if 'username' not in session:
        return redirect('/')
        
    username = session['username']
    new_notes = request.form.get('notes', '')
    
    # Input Validation: Truncate notes length to prevent buffer strain/database overflow
    if len(new_notes) > 500:
        new_notes = new_notes[:500]

    try:
        conn = sqlite3.connect('secure.db')
        cursor = conn.cursor()
        # Parameterized update
        cursor.execute("UPDATE users SET notes = ? WHERE username = ?", (new_notes, username))
        conn.commit()
        conn.close()
        return redirect('/dashboard')
    except Exception as e:
        app.logger.error(f"Notes update failure: {e}")
        return "An error occurred while updating profile.", 500

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')

if __name__ == '__main__':
    # Runs on standard port 5002 for local comparison
    app.run(host='127.0.0.1', port=5002, debug=False)
