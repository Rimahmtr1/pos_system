from werkzeug.security import generate_password_hash
import sqlite3

conn = sqlite3.connect('database.db')
cur = conn.cursor()

username = 'admin'
password = 'admin123'
role = 'admin'
hashed_pw = generate_password_hash(password)

cur.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, hashed_pw, role))

conn.commit()
conn.close()
print("Admin user created.")
