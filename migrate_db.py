import sqlite3

conn = sqlite3.connect('database.db')
cur = conn.cursor()

# Add currency column if it doesn't exist
try:
    cur.execute("ALTER TABLE products ADD COLUMN currency TEXT DEFAULT 'LBP'")
except sqlite3.OperationalError:
    pass  # Column probably exists

# Add unit_type column if it doesn't exist
try:
    cur.execute("ALTER TABLE products ADD COLUMN unit_type TEXT DEFAULT 'piece'")
except sqlite3.OperationalError:
    pass  # Column probably exists

conn.commit()
conn.close()

print("Database migration completed.")
