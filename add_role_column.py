import sqlite3

conn = sqlite3.connect('database.db')
cur = conn.cursor()

# Add 'role' column if not exists
try:
    cur.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'cashier'")
    print("Role column added successfully.")
except sqlite3.OperationalError as e:
    print(f"Error: {e} (probably column already exists)")

conn.commit()
conn.close()
