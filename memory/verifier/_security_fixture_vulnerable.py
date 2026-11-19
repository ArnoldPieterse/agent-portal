# ── CLEAN SNIPPET (should produce 0 findings) ──────────────────────────────
def safe_query(user_id):
    conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))

import os
api_key_env = os.environ.get('API_KEY')  # from env, not hardcoded

# ── DELIBERATELY VULNERABLE FIXTURE — for security_scan.py self-test only ──
# DO NOT USE IN PRODUCTION CODE.

import sqlite3

# (a) Hardcoded secrets — scanner should flag these
api_key = "sk_live_abc123def456ghi789"
db_password = "SuperSecret123!"
auth_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.faketokenvalue"
aws_access_key_id = "AKIAIOSFODNN7EXAMPLE"

# (b) SQL injection vectors — scanner should flag these
def get_user_bad(name):
    conn = sqlite3.connect("test.db")
    # f-string in SQL query
    query = f"SELECT * FROM users WHERE username = '{name}'"
    return conn.execute(query).fetchall()

def search_bad(term):
    conn = sqlite3.connect("test.db")
    # string concatenation in SQL
    q = "SELECT id, title FROM posts WHERE title LIKE '%" + term + "%'"
    return conn.execute(q).fetchall()

def update_bad(uid, status):
    conn = sqlite3.connect("test.db")
    # .format() in SQL
    sql = "UPDATE users SET status = '{}' WHERE id = {}".format(status, uid)
    conn.execute(sql)
