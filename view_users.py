import sqlite3
import os

db_path = 'database.db'
print("🗂️  Checking DB at:", os.path.abspath(db_path))

conn = sqlite3.connect(db_path)
cur = conn.cursor()

try:
    cur.execute("SELECT id, username FROM users")
    rows = cur.fetchall()

    if rows:
        for row in rows:
            print(f"✅ ID: {row[0]}, Username: {row[1]}")
    else:
        print("⚠️ No users found in the 'users' table.")
except sqlite3.OperationalError as e:
    print("❌ Error:", e)

conn.close()
