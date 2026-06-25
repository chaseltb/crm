import bcrypt
import sqlite3
import uuid
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'etherealcrm.db')
DB_PATH = os.path.abspath(DB_PATH)

def seed():
    email = "etherealabsco@gmail.com"
    password = "ethereal123"
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    now = __import__('datetime').datetime.utcnow().isoformat()

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO users (user_id, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
        (str(uuid.uuid4()), email, password_hash, now)
    )
    conn.commit()
    conn.close()
    print("Seeded user etherealabsco@gmail.com with password: ethereal123")

if __name__ == '__main__':
    seed()
