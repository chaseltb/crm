"""
db/seed_demo.py — Seed a demo database with a login user and realistic sample data.

Usage:
    python db/seed_demo.py --demo heritage
    python db/seed_demo.py --demo neuroink

Each demo gets its own database under data/<demo>/etherealcrm.db
"""

import argparse
import os
import sys
import sqlite3
import uuid
import json
from datetime import datetime, date, timedelta

try:
    import bcrypt
except ImportError:
    print("ERROR: bcrypt not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


DEMOS = {
    "heritage": {
        "email": "demo@heritagelandscaping.com",
        "password": "heritage2024",
        "db": os.path.join(ROOT, "data", "heritage", "etherealcrm.db"),
        "config": os.path.join(ROOT, "config.heritage.yaml"),
    },
    "neuroink": {
        "email": "demo@neuroink.io",
        "password": "neuroink2024",
        "db": os.path.join(ROOT, "data", "neuroink", "etherealcrm.db"),
        "config": os.path.join(ROOT, "config.neuroink.yaml"),
    },
}

# ── Sample data definitions ───────────────────────────────────────────────────

HERITAGE_CONTACTS = [
    {"first_name": "Carol", "last_name": "Whitfield", "company": "Whitfield Property Mgmt", "email": "carol@whitfieldpm.com", "phone": "555-210-4481", "city": "Naperville", "state": "IL", "source": "Referral", "tags": "commercial,priority"},
    {"first_name": "Mark", "last_name": "Denton", "company": "", "email": "mdenton@gmail.com", "phone": "555-382-9014", "city": "Wheaton", "state": "IL", "source": "Nextdoor", "tags": "residential"},
    {"first_name": "Sandra", "last_name": "Okafor", "company": "Okafor & Sons Realty", "email": "sandra@okafor-realty.com", "phone": "555-640-7722", "city": "Aurora", "state": "IL", "source": "Google Search", "tags": "commercial"},
    {"first_name": "Tom", "last_name": "Briggs", "company": "", "email": "tom.briggs@hotmail.com", "phone": "555-118-3305", "city": "Downers Grove", "state": "IL", "source": "Yard Sign", "tags": "residential"},
    {"first_name": "Heather", "last_name": "Nguyen", "company": "Lakeview HOA", "email": "heather.nguyen@lakeviewhoa.org", "phone": "555-774-8830", "city": "Lisle", "state": "IL", "source": "Direct Mail", "tags": "hoa,commercial,priority"},
    {"first_name": "James", "last_name": "Albright", "company": "", "email": "jalbright@comcast.net", "phone": "555-502-1190", "city": "Glen Ellyn", "state": "IL", "source": "Referral", "tags": "residential"},
    {"first_name": "Priya", "last_name": "Sharma", "company": "Sharma Commercial Realty", "email": "priya@sharmacommercial.com", "phone": "555-831-4467", "city": "Naperville", "state": "IL", "source": "Google Search", "tags": "commercial"},
    {"first_name": "Kevin", "last_name": "Maloney", "company": "", "email": "kmaloney@yahoo.com", "phone": "555-295-6643", "city": "Warrenville", "state": "IL", "source": "Repeat Customer", "tags": "residential,repeat"},
]

HERITAGE_DEALS = [
    # (contact_idx, deal_name, service_type, stage, value, days_until_followup)
    (0, "Whitfield Portfolio — 8 Properties Maintenance", "Weekly Maintenance", "Proposal Signed", 18400, 2),
    (0, "Whitfield — Spring Irrigations", "Irrigation Install", "Estimate Sent", 6200, 5),
    (1, "Denton Residence Full Cleanup", "Spring Cleanup", "Won", 950, None),
    (2, "Okafor Strip Mall Grounds", "Weekly Maintenance", "New Lead", 4800, 3),
    (3, "Briggs Backyard Hardscape", "Hardscape Design", "Estimate Sent", 12500, 1),
    (4, "Lakeview HOA Seasonal Contract", "Weekly Maintenance", "Proposal Signed", 34000, 4),
    (4, "Lakeview HOA — Fall Overseeding", "Sod & Seeding", "Won", 2800, None),
    (5, "Albright Tree Removal & Trim", "Tree & Shrub Service", "Completed", 1400, None),
    (6, "Sharma Office Park Renovation", "Hardscape Design", "New Lead", 22000, 7),
    (7, "Maloney Annual Maintenance Renewal", "Weekly Maintenance", "Proposal Signed", 3200, 2),
]

HERITAGE_NOTES = [
    # (deal_idx, note_type, body)
    (0, "Call", "Spoke with Carol. She confirmed all 8 properties need service by May 1. She wants bi-weekly visits on 4 of them. Sending revised proposal by EOD."),
    (0, "Email", "Sent detailed 3-tier proposal covering weekly, bi-weekly, and one-time cleanup options. Waiting on sign-off from her board."),
    (1, "Email", "Followed up on the irrigation quote. Carol mentioned the property manager at Riverwalk location needs to approve separately."),
    (2, "Meeting", "Met Mark at his property. Walked the back yard, front beds, and side yard. He wants a full spring cleanup + mulch. Showed photos of past jobs."),
    (4, "Call", "Tom called to say he wants to move forward. Checking on permit for the retaining wall portion before we schedule."),
    (5, "Meeting", "Met Heather and the HOA board. They love the full seasonal proposal. Voting on it at next Thursday's board meeting. Very positive reception."),
    (7, "Call", "Quick call with James. Tree removal went perfectly. He's asking about spring shrub trimming. Added it as upsell note."),
    (9, "Email", "Kevin confirmed renewal for another year. Slight rate increase accepted without issue. Sending updated contract."),
]

NEUROINK_CONTACTS = [
    {"first_name": "Dr. Aisha", "last_name": "Patel", "company": "MIT Lincoln Lab", "email": "a.patel@ll.mit.edu", "phone": "617-555-0184", "city": "Lexington", "state": "MA", "source": "Conference", "tags": "research,priority"},
    {"first_name": "Marcus", "last_name": "Chen", "company": "Northgate Biomedical", "email": "mchen@northgate-bio.com", "phone": "858-555-0237", "city": "San Diego", "state": "CA", "source": "Website RFQ", "tags": "biomedical,commercial"},
    {"first_name": "Ingrid", "last_name": "Holloway", "company": "UC San Diego ECE Dept", "email": "iholloway@ucsd.edu", "phone": "858-555-0991", "city": "La Jolla", "state": "CA", "source": "Partner Referral", "tags": "university,education"},
    {"first_name": "David", "last_name": "Osei", "company": "Osei Defense Systems", "email": "d.osei@oseidefense.com", "phone": "703-555-0448", "city": "Reston", "state": "VA", "source": "Cold Outreach", "tags": "defense,priority"},
    {"first_name": "Rachel", "last_name": "Kimura", "company": "Vanta Photonics", "email": "rkimura@vantaphotonics.com", "phone": "503-555-0772", "city": "Portland", "state": "OR", "source": "LinkedIn", "tags": "startup,commercial"},
    {"first_name": "Thomas", "last_name": "Whitmore", "company": "Georgia Tech Research", "email": "t.whitmore@gatech.edu", "phone": "404-555-0315", "city": "Atlanta", "state": "GA", "source": "Conference", "tags": "university,research"},
    {"first_name": "Sophia", "last_name": "Laurent", "company": "Laurent MedTech", "email": "slaurent@laurentmed.com", "phone": "617-555-0629", "city": "Boston", "state": "MA", "source": "Existing Account", "tags": "medtech,repeat,priority"},
    {"first_name": "Carlos", "last_name": "Reyes", "company": "SentinelRF Inc.", "email": "creyes@sentinelrf.com", "phone": "512-555-0840", "city": "Austin", "state": "TX", "source": "LinkedIn", "tags": "rf,commercial"},
]

NEUROINK_DEALS = [
    (0, "MIT LL — 4-Channel Oscilloscope Array", "Oscilloscope Array", "PO Received", 47200, 1),
    (0, "MIT LL — Signal Gen Expansion", "Signal Generator", "Quote Sent", 18500, 3),
    (1, "Northgate — Full Calibration Suite", "Calibration Suite", "Evaluation", 31000, 2),
    (2, "UCSD ECE — Teaching Lab Power Supplies (x12)", "Power Supply Unit", "Quote Sent", 14400, 5),
    (3, "Osei Defense — RF Test System", "RF Test Equipment", "Demo Scheduled", 88000, 1),
    (4, "Vanta — Spectral Analyzer Pair", "Spectral Analyzer", "New Inquiry", 22600, 7),
    (5, "Georgia Tech — Custom Signal Integration", "Custom Integration", "Evaluation", 56000, 4),
    (6, "Laurent MedTech — Annual Calibration Renewal", "Calibration Suite", "Won", 9800, None),
    (6, "Laurent MedTech — Oscilloscope Upgrade", "Oscilloscope Array", "PO Received", 28500, 2),
    (7, "SentinelRF — RF Signal Generator Fleet", "Signal Generator", "Quote Sent", 41000, 3),
]

NEUROINK_NOTES = [
    (0, "Call", "Spoke with Dr. Patel's procurement office. PO is being processed, expected delivery authorization within 5 business days. She confirmed 4-channel config is correct."),
    (0, "Meeting", "Zoom demo with the full lab team. Showed live waveform capture at 2.5 GS/s. Strong interest in signal gen expansion to pair with the array."),
    (1, "Email", "Sent expanded quote including full calibration suite with 18-month service contract. Marcus forwarded it to their VP of Ops for sign-off."),
    (2, "Call", "Ingrid confirmed the university purchasing cycle closes June 30. Need to get final specs by June 10 to make the deadline."),
    (3, "Meeting", "On-site demo at Reston facility. David and 2 engineers attended. They tested the RF test system for 3 hours. Very impressed with phase noise specs. Follow up with a written proposal."),
    (3, "Email", "Sent formal proposal doc. $88k total with 3-year warranty and free annual calibration. David said it's going to their contracting officer."),
    (5, "Call", "Initial discovery call with Rachel. Vanta is ramping production and needs spectrum analysis at multiple test stations. Invited them to our Portland partner site for a live demo."),
    (6, "Meeting", "Full-day onsite at Georgia Tech. Thomas walked us through their custom integration requirements for the RF/signal workflow. Significant scope — may need a dedicated integration team."),
    (7, "Email", "Laurent renewal processed automatically. Sophia mentioned they're evaluating an oscilloscope upgrade — sent preliminary spec sheet."),
]


# ── Database helpers ──────────────────────────────────────────────────────────

def _uid():
    return str(uuid.uuid4())


def _now():
    return datetime.utcnow().isoformat(timespec='seconds')


def _days(n):
    return (date.today() + timedelta(days=n)).isoformat() if n is not None else None


def setup_db(db_path: str):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS contacts (
            contact_id TEXT PRIMARY KEY, first_name TEXT NOT NULL, last_name TEXT NOT NULL,
            company TEXT, email TEXT, phone TEXT, city TEXT, state TEXT,
            source TEXT, tags TEXT, is_deleted INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS deals (
            deal_id TEXT PRIMARY KEY, contact_id TEXT NOT NULL REFERENCES contacts(contact_id),
            deal_name TEXT NOT NULL, service_type TEXT, stage TEXT NOT NULL DEFAULT 'New Lead',
            value REAL, probability INTEGER DEFAULT 50, next_follow_up TEXT,
            assigned_to TEXT, close_date TEXT, is_deleted INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS notes (
            note_id TEXT PRIMARY KEY, deal_id TEXT REFERENCES deals(deal_id),
            contact_id TEXT REFERENCES contacts(contact_id), note_type TEXT NOT NULL DEFAULT 'Internal',
            body TEXT, doc_link TEXT, created_by TEXT,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS stage_history (
            history_id TEXT PRIMARY KEY, deal_id TEXT NOT NULL REFERENCES deals(deal_id),
            from_stage TEXT, to_stage TEXT NOT NULL, changed_by TEXT, changed_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id TEXT PRIMARY KEY REFERENCES users(user_id),
            settings_json TEXT NOT NULL DEFAULT '{}'
        );
        CREATE INDEX IF NOT EXISTS idx_deals_contact ON deals(contact_id);
        CREATE INDEX IF NOT EXISTS idx_deals_stage   ON deals(stage);
        CREATE INDEX IF NOT EXISTS idx_notes_deal    ON notes(deal_id);
        CREATE INDEX IF NOT EXISTS idx_notes_contact ON notes(contact_id);
        CREATE INDEX IF NOT EXISTS idx_history_deal  ON stage_history(deal_id);
    """)
    conn.commit()
    return conn


def seed_user(conn, email: str, password: str) -> str:
    uid = _uid()
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn.execute(
        "INSERT OR REPLACE INTO users (user_id, email, password_hash, created_at) VALUES (?,?,?,?)",
        (uid, email, pw_hash, _now())
    )
    conn.commit()
    return uid


def seed_contacts(conn, contacts: list) -> list:
    ids = []
    for c in contacts:
        cid = _uid()
        now = _now()
        conn.execute("""
            INSERT INTO contacts
              (contact_id, first_name, last_name, company, email, phone,
               city, state, source, tags, is_deleted, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,0,?,?)
        """, (cid, c['first_name'], c['last_name'], c.get('company',''),
              c.get('email',''), c.get('phone',''), c.get('city',''),
              c.get('state',''), c.get('source',''), c.get('tags',''), now, now))
        ids.append(cid)
    conn.commit()
    return ids


def seed_deals(conn, deals: list, contact_ids: list, created_by: str) -> list:
    deal_ids = []
    for (ci, name, svc, stage, value, followup_days) in deals:
        did = _uid()
        now = _now()
        fu = _days(followup_days)
        prob = {"Won": 100, "Lost": 0, "Completed": 100, "PO Received": 90,
                "Proposal Signed": 70, "Estimate Sent": 50, "Quote Sent": 50,
                "Evaluation": 60, "Demo Scheduled": 40, "New Lead": 20,
                "New Inquiry": 15}.get(stage, 50)
        conn.execute("""
            INSERT INTO deals
              (deal_id, contact_id, deal_name, service_type, stage, value,
               probability, next_follow_up, assigned_to, close_date,
               is_deleted, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,0,?,?)
        """, (did, contact_ids[ci], name, svc, stage, value, prob, fu,
              created_by, None, now, now))
        conn.execute("""
            INSERT INTO stage_history (history_id, deal_id, from_stage, to_stage, changed_by, changed_at)
            VALUES (?,?,?,?,?,?)
        """, (_uid(), did, None, stage, created_by, now))
        deal_ids.append(did)
    conn.commit()
    return deal_ids


def seed_notes(conn, notes: list, deal_ids: list, contact_ids_by_deal: list, created_by: str):
    # contact_ids_by_deal: for each deal index, which contact_id
    for (di, ntype, body) in notes:
        did = deal_ids[di]
        cid = contact_ids_by_deal[di]
        now = _now()
        conn.execute("""
            INSERT INTO notes
              (note_id, deal_id, contact_id, note_type, body, doc_link,
               created_by, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (_uid(), did, cid, ntype, body, '', created_by, now, now))
    conn.commit()


# ── Main ──────────────────────────────────────────────────────────────────────

def run(demo_name: str):
    cfg = DEMOS.get(demo_name)
    if not cfg:
        print(f"ERROR: Unknown demo '{demo_name}'. Choose: {list(DEMOS.keys())}")
        sys.exit(1)

    db_path = cfg['db']
    email   = cfg['email']
    password = cfg['password']

    print(f"\n[seed_demo] Setting up '{demo_name}' demo")
    print(f"  DB:     {db_path}")
    print(f"  Config: {cfg['config']}")

    conn = setup_db(db_path)

    uid = seed_user(conn, email, password)
    print(f"  OK User created: {email}  /  {password}")

    if demo_name == "heritage":
        contacts = HERITAGE_CONTACTS
        deals_raw = HERITAGE_DEALS
        notes_raw = HERITAGE_NOTES
    else:
        contacts = NEUROINK_CONTACTS
        deals_raw = NEUROINK_DEALS
        notes_raw = NEUROINK_NOTES

    contact_ids = seed_contacts(conn, contacts)
    print(f"  OK {len(contact_ids)} contacts seeded")

    contact_ids_by_deal = [contact_ids[d[0]] for d in deals_raw]
    deal_ids = seed_deals(conn, deals_raw, contact_ids, email.split('@')[0])
    print(f"  OK {len(deal_ids)} deals seeded")

    seed_notes(conn, notes_raw, deal_ids, contact_ids_by_deal, email.split('@')[0])
    print(f"  OK {len(notes_raw)} notes seeded")

    conn.close()
    print(f"\n[seed_demo] Done. Run the demo with:")
    print(f"  Windows: run_{demo_name}.bat")
    print(f"  Mac/Linux: bash run_{demo_name}.sh\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Seed a demo CRM instance')
    parser.add_argument('--demo', required=True, choices=list(DEMOS.keys()),
                        help='Which demo to seed')
    args = parser.parse_args()
    run(args.demo)
