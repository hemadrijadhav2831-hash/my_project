import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect("app.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 username TEXT UNIQUE,
 password TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS reports(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER,
 symptoms TEXT,
 diagnosis TEXT,
 prescription TEXT,
 serious INTEGER,
 created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

try:
    cur.execute("INSERT INTO users (username,password) VALUES (?,?)",
                ("admin", generate_password_hash("admin123")))
except:
    pass

conn.commit()
conn.close()

print("Database initialized.")
