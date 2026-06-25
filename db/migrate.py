"""
db/migrate.py — EtherealCRM schema migration.
Safe to re-run; uses CREATE TABLE IF NOT EXISTS.
Run: python db/migrate.py
"""

import sqlite3
import os
import sys

# Allow running from project root or from db/
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'etherealcrm.db')
DB_PATH = os.path.abspath(DB_PATH)


def run_migration():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    print(f"[migrate] Using database at: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.executescript("""
        PRAGMA journal_mode=WAL;
        PRAGMA foreign_keys=ON;

        -- ── Users (auth) ────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS users (
            user_id     TEXT PRIMARY KEY,
            email       TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at  TEXT NOT NULL
        );

        -- ── Contacts ────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS contacts (
            contact_id  TEXT PRIMARY KEY,
            first_name  TEXT NOT NULL,
            last_name   TEXT NOT NULL,
            company     TEXT,
            email       TEXT,
            phone       TEXT,
            city        TEXT,
            state       TEXT,
            source      TEXT,
            tags        TEXT,
            is_deleted  INTEGER NOT NULL DEFAULT 0,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );

        -- ── Deals ───────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS deals (
            deal_id         TEXT PRIMARY KEY,
            contact_id      TEXT NOT NULL REFERENCES contacts(contact_id),
            deal_name       TEXT NOT NULL,
            service_type    TEXT,
            stage           TEXT NOT NULL DEFAULT 'New Lead',
            value           REAL,
            probability     INTEGER DEFAULT 50,
            next_follow_up  TEXT,
            assigned_to     TEXT,
            close_date      TEXT,
            is_deleted      INTEGER NOT NULL DEFAULT 0,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        );

        -- ── Notes ───────────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS notes (
            note_id     TEXT PRIMARY KEY,
            deal_id     TEXT REFERENCES deals(deal_id),
            contact_id  TEXT REFERENCES contacts(contact_id),
            note_type   TEXT NOT NULL DEFAULT 'Internal',
            body        TEXT,
            doc_link    TEXT,
            created_by  TEXT,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );

        -- ── Stage History ────────────────────────────────────────────
        CREATE TABLE IF NOT EXISTS stage_history (
            history_id  TEXT PRIMARY KEY,
            deal_id     TEXT NOT NULL REFERENCES deals(deal_id),
            from_stage  TEXT,
            to_stage    TEXT NOT NULL,
            changed_by  TEXT,
            changed_at  TEXT NOT NULL
        );

        -- ── Indexes ─────────────────────────────────────────────────
        CREATE INDEX IF NOT EXISTS idx_deals_contact ON deals(contact_id);
        CREATE INDEX IF NOT EXISTS idx_deals_stage   ON deals(stage);
        CREATE INDEX IF NOT EXISTS idx_notes_deal    ON notes(deal_id);
        CREATE INDEX IF NOT EXISTS idx_notes_contact ON notes(contact_id);
        CREATE INDEX IF NOT EXISTS idx_history_deal  ON stage_history(deal_id);
    """)

    conn.commit()
    conn.close()
    print("[migrate] [OK] All tables created / verified successfully.")


if __name__ == '__main__':
    run_migration()
