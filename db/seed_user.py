"""
db/seed_user.py — Create the first (or any additional) login user.
Run: python db/seed_user.py --email you@example.com
"""

import argparse
import getpass
import sqlite3
import uuid
import os
import sys

try:
    import bcrypt
except ImportError:
    print("ERROR: bcrypt not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'etherealcrm.db')
DB_PATH = os.path.abspath(DB_PATH)


def seed_user(email: str):
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        print("Run  python db/migrate.py  first.")
        sys.exit(1)

    password = getpass.getpass(f"Set password for {email}: ")
    if len(password) < 6:
        print("ERROR: Password must be at least 6 characters.")
        sys.exit(1)

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    now = __import__('datetime').datetime.utcnow().isoformat()

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT OR REPLACE INTO users (user_id, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), email, password_hash, now)
        )
        conn.commit()
        print(f"[seed_user] ✓ User '{email}' created / updated successfully.")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create a CRM login user')
    parser.add_argument('--email', required=True, help='Email address for the new user')
    args = parser.parse_args()
    seed_user(args.email)
