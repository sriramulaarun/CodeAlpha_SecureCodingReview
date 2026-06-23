import sqlite3
from flask import Flask, request, render_template, redirect, session, make_response

app = Flask(__name__)

# VULNERABILITY: Insecure Session Management - Hardcoded Secret Key
# Easily guessable/retrievable by reverse engineering or code leaks
app.secret_key = "super_secret_debug_key_do_not_change"

def init_db():
    conn = sqlite3.connect('vulnerable.db')
    cursor = conn.cursor()
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            notes TEXT
        )
    ''')
    # Pre-populate some vulnerable users
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        # VULNERABILITY: Weak Password Policy / Hardcoded Credentials (stored in plaintext)
        cursor.execute("INSERT INTO users (username, password, notes) VALUES ('admin', 'admin123', 'System administrative notes.')")
        cursor.execute("INSERT INTO users (username, password, notes) VALUES ('alice', 'password', 'Welcome to my profile! <script>console.log(\"XSS Triggered!\");</script>')")
    conn.commit()
    conn.close()

# Initialize vulnerable database
init_db()

@app.route('/')
def home():
    if 'username' in session:
        return redirect('/dashboard')
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')

    # VULNERABILITY: Hardcoded Admin Credential Check
    if username == "backdoor_admin" and password == "DeveloperSecret2026!":
        session['username'] = "backdoor_admin"
        return redirect('/dashboard')

    # VULNERABILITY: SQL Injection (Raw concatenation of user input into SQLite query)
    # A user can bypass login by entering: ' OR '1'='1
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    print(f"[DEBUG] Executing Query: {query}")

    try:
        conn = sqlite3.connect('vulnerable.db')
        cursor = conn.cursor()
        cursor.execute(query)
        user = cursor.fetchone()
        conn.close()
        
        if user:
            # Set session cookie
            session['username'] = user[1]
            resp = make_response(redirect('/dashboard'))
            # VULNERABILITY: Insecure Session Management - Missing Secure/HttpOnly flags
            # Stolen session cookies can be extracted by scripts in XSS
            resp.set_cookie('user_session_id', user[1]) 
            return resp
        else:
            return render_template('index.html', error="Invalid credentials")
            
    except Exception as e:
        # VULNERABILITY: Information Disclosure (Returning raw DB errors/tracebacks to client)
        return f"<h3>Database Error!</h3><p>Query: {query}</p><p>Exception: {e}</p>", 500

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    
    # VULNERABILITY: Missing Input Validation & Weak Password Policy
    # Accepts blank names, passwords of length 1, no complexity checking
    if not username or not password:
        return "Username and Password cannot be empty!", 400

    try:
        conn = sqlite3.connect('vulnerable.db')
        cursor = conn.cursor()
        
        # Check if username exists
        cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
        if cursor.fetchone():
            conn.close()
            return "User already exists!", 400
            
        # VULNERABILITY: Weak Password Policy - Storing password in plaintext
        cursor.execute(f"INSERT INTO users (username, password, notes) VALUES ('{username}', '{password}', 'User bio notes.')")
        conn.commit()
        conn.close()
        return redirect('/')
    except Exception as e:
        return f"Registration database error: {e}", 500

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/')
    
    username = session['username']
    try:
        conn = sqlite3.connect('vulnerable.db')
        cursor = conn.cursor()
        cursor.execute(f"SELECT notes FROM users WHERE username = '{username}'")
        row = cursor.fetchone()
        conn.close()
        
        notes = row[0] if row else ""
        return render_template('dashboard.html', username=username, notes=notes)
    except Exception as e:
        return f"Dashboard retrieval error: {e}", 500

@app.route('/update_notes', methods=['POST'])
def update_notes():
    if 'username' not in session:
        return redirect('/')
        
    username = session['username']
    new_notes = request.form.get('notes', '')
    
    # VULNERABILITY: Cross-Site Scripting (XSS) due to saving unsanitized inputs 
    # and rendering them raw in HTML via the templates.
    try:
        conn = sqlite3.connect('vulnerable.db')
        cursor = conn.cursor()
        cursor.execute(f"UPDATE users SET notes = '{new_notes}' WHERE username = '{username}'")
        conn.commit()
        conn.close()
        return redirect('/dashboard')
    except Exception as e:
        return f"Update notes database error: {e}", 500

@app.route('/logout')
def logout():
    session.pop('username', None)
    resp = make_response(redirect('/'))
    resp.delete_cookie('user_session_id')
    return resp

if __name__ == '__main__':
    # Runs on standard port 5001 for local comparison
    app.run(host='127.0.0.1', port=5002, debug=True)
