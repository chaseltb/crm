"""
db/crud.py — All CRUD helpers for EtherealCRM.
Every function opens its own connection so it's safe to call from any Dash callback.
"""

import sqlite3
import uuid
import os
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'etherealcrm.db')
DB_PATH = os.path.abspath(DB_PATH)


# ── Helpers ─────────────────────────────────────────────────────────────────

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _now() -> str:
    return datetime.utcnow().isoformat(timespec='seconds')


def _uid() -> str:
    return str(uuid.uuid4())


def row_to_dict(row) -> Optional[Dict]:
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows) -> List[Dict]:
    return [dict(r) for r in rows]


# ── Auth ─────────────────────────────────────────────────────────────────────

def get_user_by_email(email: str) -> Optional[Dict]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return row_to_dict(row)


def get_user_by_id(user_id: str) -> Optional[Dict]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return row_to_dict(row)


# ── Contacts ─────────────────────────────────────────────────────────────────

def get_contacts(include_deleted: bool = False) -> List[Dict]:
    with get_db() as conn:
        if include_deleted:
            rows = conn.execute("SELECT * FROM contacts ORDER BY created_at DESC").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM contacts WHERE is_deleted = 0 ORDER BY created_at DESC"
            ).fetchall()
        return rows_to_list(rows)


def get_contact(contact_id: str) -> Optional[Dict]:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM contacts WHERE contact_id = ? AND is_deleted = 0",
            (contact_id,)
        ).fetchone()
        return row_to_dict(row)


def create_contact(data: Dict) -> str:
    cid = _uid()
    now = _now()
    with get_db() as conn:
        conn.execute("""
            INSERT INTO contacts
              (contact_id, first_name, last_name, company, email, phone,
               city, state, source, tags, is_deleted, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,0,?,?)
        """, (
            cid,
            data.get('first_name', ''),
            data.get('last_name', ''),
            data.get('company', ''),
            data.get('email', ''),
            data.get('phone', ''),
            data.get('city', ''),
            data.get('state', ''),
            data.get('source', ''),
            data.get('tags', ''),
            now, now
        ))
        conn.commit()
    return cid


def update_contact(contact_id: str, data: Dict) -> None:
    now = _now()
    with get_db() as conn:
        conn.execute("""
            UPDATE contacts SET
              first_name=?, last_name=?, company=?, email=?, phone=?,
              city=?, state=?, source=?, tags=?, updated_at=?
            WHERE contact_id=?
        """, (
            data.get('first_name', ''),
            data.get('last_name', ''),
            data.get('company', ''),
            data.get('email', ''),
            data.get('phone', ''),
            data.get('city', ''),
            data.get('state', ''),
            data.get('source', ''),
            data.get('tags', ''),
            now, contact_id
        ))
        conn.commit()


def soft_delete_contact(contact_id: str) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE contacts SET is_deleted=1, updated_at=? WHERE contact_id=?",
            (_now(), contact_id)
        )
        conn.commit()


def get_contact_count() -> int:
    with get_db() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM contacts WHERE is_deleted=0"
        ).fetchone()
        return row['cnt'] if row else 0


def bulk_create_contacts(rows: List[Dict]) -> int:
    """Insert multiple contacts; returns number successfully inserted."""
    now = _now()
    inserted = 0
    with get_db() as conn:
        for data in rows:
            try:
                conn.execute("""
                    INSERT INTO contacts
                      (contact_id, first_name, last_name, company, email, phone,
                       city, state, source, tags, is_deleted, created_at, updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,0,?,?)
                """, (
                    _uid(),
                    data.get('first_name', ''),
                    data.get('last_name', ''),
                    data.get('company', ''),
                    data.get('email', ''),
                    data.get('phone', ''),
                    data.get('city', ''),
                    data.get('state', ''),
                    data.get('source', ''),
                    data.get('tags', ''),
                    now, now
                ))
                inserted += 1
            except Exception:
                pass
        conn.commit()
    return inserted


def get_open_deal_count_for_contact(contact_id: str) -> int:
    with get_db() as conn:
        row = conn.execute("""
            SELECT COUNT(*) as cnt FROM deals
            WHERE contact_id=? AND is_deleted=0 AND stage NOT IN ('Won','Lost')
        """, (contact_id,)).fetchone()
        return row['cnt'] if row else 0


# ── Deals ─────────────────────────────────────────────────────────────────────

def get_deals(include_deleted: bool = False, stage: str = None) -> List[Dict]:
    with get_db() as conn:
        query = """
            SELECT d.*, c.first_name, c.last_name, c.company
            FROM deals d
            JOIN contacts c ON d.contact_id = c.contact_id
        """
        conditions = []
        params = []
        if not include_deleted:
            conditions.append("d.is_deleted = 0")
        if stage:
            conditions.append("d.stage = ?")
            params.append(stage)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY d.created_at DESC"
        rows = conn.execute(query, params).fetchall()
        return rows_to_list(rows)


def get_deal(deal_id: str) -> Optional[Dict]:
    with get_db() as conn:
        row = conn.execute("""
            SELECT d.*, c.first_name, c.last_name, c.company, c.email
            FROM deals d
            JOIN contacts c ON d.contact_id = c.contact_id
            WHERE d.deal_id=? AND d.is_deleted=0
        """, (deal_id,)).fetchone()
        return row_to_dict(row)


def get_deals_for_contact(contact_id: str) -> List[Dict]:
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM deals
            WHERE contact_id=? AND is_deleted=0
            ORDER BY created_at DESC
        """, (contact_id,)).fetchall()
        return rows_to_list(rows)


def create_deal(data: Dict, created_by: str = '') -> str:
    did = _uid()
    now = _now()
    initial_stage = data.get('stage', 'New Lead')
    with get_db() as conn:
        conn.execute("""
            INSERT INTO deals
              (deal_id, contact_id, deal_name, service_type, stage, value,
               probability, next_follow_up, assigned_to, close_date,
               is_deleted, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,0,?,?)
        """, (
            did,
            data['contact_id'],
            data.get('deal_name', ''),
            data.get('service_type', ''),
            initial_stage,
            data.get('value'),
            data.get('probability', 50),
            data.get('next_follow_up'),
            data.get('assigned_to', ''),
            data.get('close_date'),
            now, now
        ))
        conn.commit()
    # Log initial stage
    log_stage_change(did, None, initial_stage, created_by)
    return did


def update_deal(deal_id: str, data: Dict, changed_by: str = '') -> None:
    now = _now()
    # Check if stage changed
    old = get_deal(deal_id)
    old_stage = old['stage'] if old else None
    new_stage = data.get('stage', old_stage)

    with get_db() as conn:
        conn.execute("""
            UPDATE deals SET
              deal_name=?, service_type=?, stage=?, value=?, probability=?,
              next_follow_up=?, assigned_to=?, close_date=?, updated_at=?
            WHERE deal_id=?
        """, (
            data.get('deal_name', ''),
            data.get('service_type', ''),
            new_stage,
            data.get('value'),
            data.get('probability', 50),
            data.get('next_follow_up'),
            data.get('assigned_to', ''),
            data.get('close_date'),
            now, deal_id
        ))
        conn.commit()

    if old_stage and new_stage and old_stage != new_stage:
        log_stage_change(deal_id, old_stage, new_stage, changed_by)


def soft_delete_deal(deal_id: str) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE deals SET is_deleted=1, updated_at=? WHERE deal_id=?",
            (_now(), deal_id)
        )
        conn.commit()


def snooze_deal_followup(deal_id: str, days: int) -> None:
    """Push next_follow_up forward by `days` days."""
    deal = get_deal(deal_id)
    if not deal:
        return
    today = date.today()
    if deal['next_follow_up']:
        try:
            base = date.fromisoformat(deal['next_follow_up'])
        except ValueError:
            base = today
    else:
        base = today
    new_date = (base + timedelta(days=days)).isoformat()
    with get_db() as conn:
        conn.execute(
            "UPDATE deals SET next_follow_up=?, updated_at=? WHERE deal_id=?",
            (new_date, _now(), deal_id)
        )
        conn.commit()


# ── Notes ─────────────────────────────────────────────────────────────────────

def get_notes_for_deal(deal_id: str) -> List[Dict]:
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM notes WHERE deal_id=? ORDER BY created_at DESC
        """, (deal_id,)).fetchall()
        return rows_to_list(rows)


def get_notes_for_contact(contact_id: str) -> List[Dict]:
    with get_db() as conn:
        rows = conn.execute("""
            SELECT n.*, d.deal_name FROM notes n
            LEFT JOIN deals d ON n.deal_id = d.deal_id
            WHERE n.contact_id=?
            ORDER BY n.created_at DESC
        """, (contact_id,)).fetchall()
        return rows_to_list(rows)


def get_recent_notes(limit: int = 10) -> List[Dict]:
    with get_db() as conn:
        rows = conn.execute("""
            SELECT n.*, d.deal_name,
                   c.first_name || ' ' || c.last_name AS contact_name
            FROM notes n
            LEFT JOIN deals d ON n.deal_id = d.deal_id
            LEFT JOIN contacts c ON n.contact_id = c.contact_id
            ORDER BY n.created_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return rows_to_list(rows)


def get_note(note_id: str) -> Optional[Dict]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM notes WHERE note_id=?", (note_id,)).fetchone()
        return row_to_dict(row)


def create_note(data: Dict) -> str:
    nid = _uid()
    now = _now()
    with get_db() as conn:
        conn.execute("""
            INSERT INTO notes
              (note_id, deal_id, contact_id, note_type, body, doc_link,
               created_by, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            nid,
            data.get('deal_id'),
            data.get('contact_id'),
            data.get('note_type', 'Internal'),
            data.get('body', ''),
            data.get('doc_link', ''),
            data.get('created_by', ''),
            now, now
        ))
        conn.commit()
    return nid


def update_note(note_id: str, data: Dict) -> None:
    now = _now()
    with get_db() as conn:
        conn.execute("""
            UPDATE notes SET note_type=?, body=?, doc_link=?, updated_at=?
            WHERE note_id=?
        """, (
            data.get('note_type', 'Internal'),
            data.get('body', ''),
            data.get('doc_link', ''),
            now, note_id
        ))
        conn.commit()


def delete_note(note_id: str) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM notes WHERE note_id=?", (note_id,))
        conn.commit()


# ── Stage History ─────────────────────────────────────────────────────────────

def log_stage_change(deal_id: str, from_stage: Optional[str],
                     to_stage: str, changed_by: str = '') -> None:
    with get_db() as conn:
        conn.execute("""
            INSERT INTO stage_history (history_id, deal_id, from_stage, to_stage, changed_by, changed_at)
            VALUES (?,?,?,?,?,?)
        """, (_uid(), deal_id, from_stage, to_stage, changed_by, _now()))
        conn.commit()


def get_stage_history(deal_id: str) -> List[Dict]:
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM stage_history WHERE deal_id=? ORDER BY changed_at DESC
        """, (deal_id,)).fetchall()
        return rows_to_list(rows)


# ── Dashboard Stats ───────────────────────────────────────────────────────────

def get_pipeline_stats() -> Dict:
    """Returns aggregate stats for the dashboard."""
    with get_db() as conn:
        # Open deals (not Won/Lost)
        open_row = conn.execute("""
            SELECT COUNT(*) as cnt, COALESCE(SUM(value),0) as total_value
            FROM deals WHERE is_deleted=0 AND stage NOT IN ('Won','Lost')
        """).fetchone()

        # Win rate
        won = conn.execute(
            "SELECT COUNT(*) as cnt FROM deals WHERE is_deleted=0 AND stage='Won'"
        ).fetchone()['cnt']
        lost = conn.execute(
            "SELECT COUNT(*) as cnt FROM deals WHERE is_deleted=0 AND stage='Lost'"
        ).fetchone()['cnt']

        # Deals by stage
        stage_rows = conn.execute("""
            SELECT stage, COUNT(*) as cnt, COALESCE(SUM(value),0) as total_value
            FROM deals WHERE is_deleted=0
            GROUP BY stage
        """).fetchall()

        # Follow-up overdue
        today_str = date.today().isoformat()
        followup_count = conn.execute("""
            SELECT COUNT(*) as cnt FROM deals
            WHERE is_deleted=0 AND next_follow_up <= ? AND stage NOT IN ('Won','Lost')
        """, (today_str,)).fetchone()['cnt']

    return {
        'open_deals': open_row['cnt'],
        'pipeline_value': open_row['total_value'],
        'won': won,
        'lost': lost,
        'win_rate': round(won / (won + lost) * 100) if (won + lost) > 0 else 0,
        'by_stage': rows_to_list(stage_rows),
        'overdue_followups': followup_count,
    }


def get_won_revenue_by_month(months: int = 6) -> List[Dict]:
    """
    Closed revenue per calendar month for the last `months` months.
    Uses stage_history so the timestamp reflects when a deal was actually won,
    not just the deal's updated_at. Fills missing months with 0s.
    """
    from datetime import date as _date
    # Build the expected month labels (YYYY-MM) so gaps are filled with zeros
    labels = []
    today = _date.today()
    for i in range(months - 1, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        labels.append(f"{y:04d}-{m:02d}")

    cutoff = labels[0] + '-01'  # first day of the earliest month

    with get_db() as conn:
        rows = conn.execute("""
            SELECT strftime('%Y-%m', sh.changed_at) AS month,
                   COUNT(DISTINCT sh.deal_id)        AS deals_closed,
                   COALESCE(SUM(d.value), 0)         AS revenue
            FROM stage_history sh
            JOIN deals d ON sh.deal_id = d.deal_id
            WHERE sh.to_stage = 'Won'
              AND d.is_deleted = 0
              AND sh.changed_at >= ?
            GROUP BY month
            ORDER BY month
        """, (cutoff,)).fetchall()

    by_month = {r['month']: dict(r) for r in rows}
    result = []
    for lbl in labels:
        if lbl in by_month:
            result.append(by_month[lbl])
        else:
            result.append({'month': lbl, 'deals_closed': 0, 'revenue': 0.0})
    return result


def get_pipeline_by_source() -> List[Dict]:
    """
    Total pipeline value and won revenue per lead source, sorted by total pipeline desc.
    Only includes non-deleted deals.
    """
    with get_db() as conn:
        rows = conn.execute("""
            SELECT
                COALESCE(NULLIF(TRIM(c.source), ''), 'Unknown') AS source,
                COUNT(d.deal_id)                                  AS deal_count,
                COALESCE(SUM(d.value), 0)                         AS total_pipeline,
                COALESCE(SUM(CASE WHEN d.stage = 'Won' THEN d.value ELSE 0 END), 0) AS won_value
            FROM contacts c
            JOIN deals d ON c.contact_id = d.contact_id
            WHERE d.is_deleted = 0
            GROUP BY source
            ORDER BY total_pipeline DESC
            LIMIT 8
        """).fetchall()
    return rows_to_list(rows)


def get_followup_deals(warning_days: int = 3) -> List[Dict]:
    """Deals where next_follow_up <= today + warning_days, not Won/Lost."""
    cutoff = (date.today() + timedelta(days=warning_days)).isoformat()
    today_str = date.today().isoformat()
    with get_db() as conn:
        rows = conn.execute("""
            SELECT d.*, c.first_name, c.last_name, c.company
            FROM deals d
            JOIN contacts c ON d.contact_id = c.contact_id
            WHERE d.is_deleted=0
              AND d.next_follow_up IS NOT NULL
              AND d.next_follow_up <= ?
              AND d.stage NOT IN ('Won','Lost')
            ORDER BY d.next_follow_up ASC
        """, (cutoff,)).fetchall()
        result = rows_to_list(rows)
        for r in result:
            fu = r.get('next_follow_up', '')
            if fu < today_str:
                r['urgency'] = 'overdue'
            elif fu == today_str:
                r['urgency'] = 'due-today'
            else:
                r['urgency'] = 'due-soon'
        return result
