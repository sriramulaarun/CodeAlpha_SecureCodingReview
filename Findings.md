# Security Audit Findings: Vulnerability Catalog

This catalog documents the **7 core security vulnerabilities** identified during the security review of the Flask Login System, along with side-by-side code comparisons and remediation steps.

---

## 1. SQL Injection (SQLi)

- **Vulnerability ID**: SEC-01
- **Risk Level**: 🔴 **CRITICAL / HIGH**
- **Impact**: Allows attackers to bypass login screens, retrieve user accounts, modify or destroy database records, and potentially execute administrative database commands.

### Code Comparison

#### ❌ Vulnerable Implementation (`Vulnerable_App/app.py`)
```python
username = request.form.get('username', '')
password = request.form.get('password', '')

# User input is concatenated directly into the query string
query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
cursor.execute(query)
```

####  Secure Implementation (`Secure_App/app.py`)
```python
username = request.form.get('username', '')
password = request.form.get('password', '')

# Parameterized Query placeholder "?" blocks SQL syntax interpretation
cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
```

### Remediation
Always separate the SQL structure from the data input. Utilize parameterized queries (prepared statements) or an Object-Relational Mapper (ORM) like SQLAlchemy. In SQLite, use the `?` placeholder and pass data as a tuple.

---

## 2. Hardcoded Credentials

- **Vulnerability ID**: SEC-02
- **Risk Level**: 🔴 **HIGH**
- **Impact**: Provides backdoor access to system databases and services. If code leaks (via public GitHub repos or server intrusions), attackers gain administrative credentials.

### Code Comparison

#### ❌ Vulnerable Implementation (`Vulnerable_App/app.py`)
```python
# Hardcoded credentials comparison inside the code
if username == "backdoor_admin" and password == "DeveloperSecret2026!":
    session['username'] = "backdoor_admin"
    return redirect('/dashboard')
```

####  Secure Implementation (`Secure_App/app.py`)
```python
# Backdoor comparison block removed entirely. 
# All credentials are mathematically verified using secure hash matching from DB
if user and check_password_hash(user['password'], password):
    session['username'] = user['username']
```

### Remediation
Remove all hardcoded credentials and backdoors from the source code. Save admin configurations in a secure database with hashed passwords, or load keys dynamically through encrypted environment variables.

---

## 3. Weak Password Policy & Plaintext Storage

- **Vulnerability ID**: SEC-03
- **Risk Level**: 🔴 **HIGH**
- **Impact**: If the user database is compromised or leaked, all accounts are compromised instantly. Bypassing complexity allows simple, easily brute-forced passwords (like `password123` or `1234`).

### Code Comparison

#### ❌ Vulnerable Implementation (`Vulnerable_App/app.py`)
```python
# Storing credentials in plaintext (no hashing)
cursor.execute(f"INSERT INTO users (username, password, notes) VALUES ('{username}', '{password}', 'User bio notes.')")
```

####  Secure Implementation (`Secure_App/app.py`)
```python
# Passwords are cryptographically salted and hashed using PBKDF2 with SHA-256
hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
cursor.execute("INSERT INTO users (username, password, notes) VALUES (?, ?, ?)", 
               (username, hashed_password, 'User bio notes.'))
```

### Remediation
1. Never store plain passwords. Use robust salted hashing algorithms (like Argon2, bcrypt, or PBKDF2-SHA256).
2. Enforce complexity constraints on registration (minimum length, mixed case, numbers, and special symbols).

---

## 4. Missing Input Validation

- **Vulnerability ID**: SEC-04
- **Risk Level**: 🟡 **MEDIUM**
- **Impact**: Promotes injection, buffer overflows, and database corruption. Allows malicious inputs to bypass business logic.

### Code Comparison

#### ❌ Vulnerable Implementation (`Vulnerable_App/app.py`)
```python
username = request.form.get('username', '')
# No checks on length or character boundaries. Blank strings are inserted.
```

####  Secure Implementation (`Secure_App/app.py`)
```python
# Username validation matching strict regex (3-20 chars, alphanumeric)
if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
    return "Username must be alphanumeric, between 3 to 20 characters.", 400
```

### Remediation
Validate all user inputs using a whitelist approach (accepting only known-good patterns) via regular expressions or validation libraries. Restrict inputs based on maximum length and format boundaries.

---

## 5. Information Disclosure (Stack Traces)

- **Vulnerability ID**: SEC-05
- **Risk Level**: 🟡 **MEDIUM**
- **Impact**: Exposes structural details (database paths, database versions, SQL schemas, and variable names), helping attackers customize target exploits.

### Code Comparison

#### ❌ Vulnerable Implementation (`Vulnerable_App/app.py`)
```python
except Exception as e:
    # Raw database engine stack traces returned to browser client
    return f"<h3>Database Error!</h3><p>Query: {query}</p><p>Exception: {e}</p>", 500
```

####  Secure Implementation (`Secure_App/app.py`)
```python
except Exception as e:
    # Error logged securely internally on server, client receives generic warning
    app.logger.error(f"Login database connection failure: {e}")
    return "An internal system error occurred. Please contact administrators.", 500
```

### Remediation
1. Configure global try-except blocks.
2. Log detailed stack traces to files on the server (`app.log`) accessible only to admin.
3. Return user-friendly, generic responses ("An internal error occurred") to public users.

---

## 6. Insecure Session Management

- **Vulnerability ID**: SEC-06
- **Risk Level**: 🟡 **MEDIUM**
- **Impact**: Hardcoded keys allow attackers to forge session cookies. Missing cookie flags (like `HttpOnly` or `SameSite`) allow malicious scripts to read session cookies during XSS attacks, leading to session hijacking.

### Code Comparison

#### ❌ Vulnerable Implementation (`Vulnerable_App/app.py`)
```python
app.secret_key = "super_secret_debug_key_do_not_change"
# Cookies are set without HttpOnly or SameSite protections
resp.set_cookie('user_session_id', user[1]) 
```

####  Secure Implementation (`Secure_App/app.py`)
```python
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(32))

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,   # Blocks Javascript cookie theft
    SESSION_COOKIE_SAMESITE='Lax',  # Protects against CSRF
    SESSION_COOKIE_SECURE=False     # Change to True on HTTPS production
)
```

### Remediation
Load session keys dynamically from environment variables. Set `HttpOnly=True` to block script reading, and `SameSite='Lax'` to prevent CSRF.

---

## 7. Cross-Site Scripting (XSS)

- **Vulnerability ID**: SEC-07
- **Risk Level**: 🔴 **HIGH**
- **Impact**: Allows attackers to inject malicious JavaScript into database fields that execute when other users view the page. Leads to cookie theft, session hijacking, phishing overlays, or malware redirect loops.

### Code Comparison

#### ❌ Vulnerable Implementation (`Vulnerable_App/templates/dashboard.html`)
```html
<!-- Bypassing Jinja2 HTML escaping engine using the 'safe' filter -->
<p>{{ notes | safe }}</p>
```

####  Secure Implementation (`Secure_App/templates/dashboard.html`)
```html
<!-- Notes are processed naturally, escaping all HTML tags automatically -->
<p>{{ notes }}</p>
```

### Remediation
Ensure automatic HTML escaping is enabled. Never use Flask's `safe` filter or mark content as safe unless it has been explicitly sanitized using a library like `bleach`. Additionally, deploy a Content Security Policy (CSP) header.
