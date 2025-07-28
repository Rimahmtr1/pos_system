import sqlite3

conn = sqlite3.connect('database.db')
cur = conn.cursor()
cur.execute("SELECT id, username, role FROM users")
users = cur.fetchall()
conn.close()

for u in users:
    print(f"ID: {u[0]}, Username: {u[1]}, Role: {u[2]}")
