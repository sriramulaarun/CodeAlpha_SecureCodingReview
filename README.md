# 🛡️ CodeAlpha Secure Coding Review: Flask Login System Audit

A professional security audit and secure coding remediation project designed for the **CodeAlpha Cyber Security Internship Task 3**.

This project provides a hands-on demonstration of the difference between insecure and secure software development practices in web applications. It features two standalone Flask login applications: a **`Vulnerable_App`** displaying critical security bugs, and a **`Secure_App`** representing a hardened, patched implementation.

---

## 📂 Project Structure

```text
CodeAlpha_SecureCodingReview/
│
├── Vulnerable_App/             # App demonstrating critical security flaws
│   ├── app.py                  # Vulnerable server code (SQLi, XSS, plain cookies)
│   └── templates/
│       ├── index.html          # Login portal
│       └── dashboard.html      # Note bio editor (renders raw HTML unsafely)
│
├── Secure_App/                 # Fully patched, secure app equivalent
│   ├── app.py                  # Hardened server code (Prepared statements, hashes)
│   └── templates/
│       ├── index.html          # Clean login portal
│       └── dashboard.html      # Secure bio editor (escapes HTML tags)
│
├── Report/
│   └── Secure_Coding_Review_Report.md  # Detailed PDF-ready PDF security audit report
│
├── Findings.md                 # Vulnerability Findings Catalog with code diffs
│
├── linkedin_promotion.md       # Presentation script and social media post
│
├── .gitignore                  # Git tracking exclusion list
│
└── README.md                   # This instruction guide
```

---

## 🔍 Vulnerabilities Identified & Remediated

This project audits and patches **7 key security flaws** corresponding to the **OWASP Top 10**:

1. **SQL Injection (SQLi)**:
   - *Vulnerable*: Raw user inputs are directly concatenated into sqlite3 queries, allowing hackers to bypass the login portal using `' OR '1'='1`.
   - *Secure*: Patched using **parameterized queries** (prepared statements) that treat user inputs strictly as strings, blocking syntax evaluation.
2. **Hardcoded Credentials & Backdoors**:
   - *Vulnerable*: A master developer backdoor account is hardcoded in the source code.
   - *Secure*: Backdoor code removed. All authentication runs dynamically through database checks.
3. **Weak Password Policy & Plaintext Storage**:
   - *Vulnerable*: Registration accepts weak passwords (e.g., `123`) and saves them in plain text.
   - *Secure*: Enforces a strong complexity policy (minimum 8 characters, uppercase, lowercase, numbers, symbols) and hashes credentials using **PBKDF2-SHA256**.
4. **Missing Input Validation**:
   - *Vulnerable*: Registration accepts empty names, long strings, or dangerous characters.
   - *Secure*: Validates usernames using regular expressions (`^[a-zA-Z0-9_]{3,20}$`) and limits input length.
5. **Information Disclosure (Stack Traces)**:
   - *Vulnerable*: Raw database exceptions are displayed on the public browser page during query errors.
   - *Secure*: Exception handling logs details to an internal administrative file (`app.log`) and shows user-friendly, generic error banners.
6. **Insecure Session Management**:
   - *Vulnerable*: Cookies do not use safety flags, and the server secret key is hardcoded.
   - *Secure*: Secret keys are generated using cryptographically secure random bytes (`os.urandom(32)`). Cookies are set with `HttpOnly` and `SameSite='Lax'` flags.
7. **Stored Cross-Site Scripting (XSS)**:
   - *Vulnerable*: Dashboard notes are rendered using Flask's `| safe` template filter, allowing JavaScript injected into the database to execute.
   - *Secure*: The `| safe` filter is removed. Jinja2 automatically escapes HTML tags, rendering script payloads as harmless plain text.

---

## 🛠️ Technologies Used

- **Runtime**: Python 3
- **Framework**: Flask (Python Web Server)
- **Database Engine**: SQLite3
- **Hashing Helpers**: Werkzeug (PBKDF2-SHA256 crypt security)
- **Regex**: Python `re` module for input validation

---

## 🚀 How to Run & Test the Scenarios

### Step 1: Clone the Repository
```bash
git clone https://github.com/sriramulaarun/CodeAlpha_SecureCodingReview.git
cd CodeAlpha_SecureCodingReview
```

### Step 2: Install Dependencies
Ensure you have Flask installed:
```bash
pip install flask
```

### Step 3: Run the Vulnerable Application
```bash
# Start the vulnerable portal on port 5001
python Vulnerable_App/app.py
```
*   **Test SQL Injection**: Open `http://127.0.0.1:5001` in your browser. Type `' OR '1'='1` in the username field, enter any password, and click Log In. You will successfully log in as the admin user.
*   **Test Stored XSS**: Once logged in, type `<script>alert('XSS Exploit!')</script>` into the "Profile Bio" notes text area and submit. The javascript alert pops up immediately.

---

### Step 4: Run the Secure Application
```bash
# Start the secure portal on port 5002
python Secure_App/app.py
```
*   **Test SQL Injection**: Open `http://127.0.0.1:5002` in your browser. Type the same `' OR '1'='1` SQL payload. The application will block the input or display "Invalid credentials", preventing access.
*   **Test Stored XSS**: Log in (Register a secure account first). Paste `<script>alert('XSS!')</script>` into the notes and submit. The script tag will render as harmless plain text on the page rather than executing!

---

## 📷 Recommended Screenshot Documentation

When presenting this project, capture these visual comparisons:
1. **SQL Injection Bypass**: Screenshot of the SQL payload bypass working on the vulnerable port (`5001`), contrasting with the access denied screen on the secure port (`5002`).
2. **XSS Payload Execution**: Screenshot of the browser pop-up box executing on port `5001`, compared to the sanitized text block on port `5002`.
3. **Database File Comparison**: Showing plaintext credentials stored in `vulnerable.db` versus cryptographically hashed strings in `secure.db`.
4. **Local Audit Logs**: Screenshot of the generated `app.log` file showing internal traceback logs.

---

## 🎓 Learning Outcomes
- Understanding standard OWASP Top 10 vulnerabilities at a code level.
- Applying secure design patterns (Prepared statements, salted password hashing, output sanitization).
- Implementing defense-in-depth security architectures using HTTP headers.
- Establishing formal risk assessment scoring methodologies.
