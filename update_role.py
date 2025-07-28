import sqlite3

conn = sqlite3.connect('database.db')
cur = conn.cursor()

username_to_update = 'admin'  # your username
new_role = 'admin'

cur.execute("UPDATE users SET role = ? WHERE username = ?", (new_role, username_to_update))
conn.commit()
conn.close()

print(f"Updated role of user '{username_to_update}' to '{new_role}'")
