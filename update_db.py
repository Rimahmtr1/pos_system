import sqlite3

conn = sqlite3.connect('database.db')
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE products ADD COLUMN image_url TEXT DEFAULT ''")
    print("Added column image_url")
except sqlite3.OperationalError:
    print("Column image_url already exists")

try:
    cur.execute("ALTER TABLE products ADD COLUMN currency TEXT DEFAULT 'LBP'")
    print("Added column currency")
except sqlite3.OperationalError:
    print("Column currency already exists")

conn.commit()
conn.close()
