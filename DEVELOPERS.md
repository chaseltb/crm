# EtherealCRM — Developer Guide

A practical reference for anyone maintaining or extending this codebase.

---

## Table of Contents

1. [Project Layout](#1-project-layout)
2. [Tech Stack](#2-tech-stack)
3. [Running the App](#3-running-the-app)
4. [Running Demo Instances](#4-running-demo-instances)
5. [Architecture Decisions](#5-architecture-decisions)
6. [How Dash Callbacks Work Here](#6-how-dash-callbacks-work-here)
7. [Adding a New Page](#7-adding-a-new-page)
8. [Adding a New Database Field](#8-adding-a-new-database-field)
9. [Adding a New Config Option](#9-adding-a-new-config-option)
10. [User Management](#10-user-management)
11. [Common Gotchas](#11-common-gotchas)
12. [Deployment (Render.com)](#12-deployment-rendercom)

---

## 1. Project Layout

```
crm/
├── app.py                    Entry point. Flask-Login, Dash setup, auth routing.
├── config.yaml               Live system config (gitignored). Edit in Settings UI.
├── config.heritage.yaml      Heritage Landscaping demo config.
├── config.neuroink.yaml      NeuroInk demo config.
├── requirements.txt
├── render.yaml               Render.com deployment blueprint.
│
├── assets/
│   └── styles.css            All CSS. CSS custom properties are injected from config.
│
├── components/
│   ├── sidebar.py            Fixed left nav, rendered per-route by app.py.
│   ├── modals.py             Reusable modal builders (contact, deal, note, confirm).
│   └── skeletons.py          Shimmer loading placeholders + empty-state component.
│
├── pages/                    One file = one page. Dash auto-discovers these.
│   ├── dashboard.py          Stats, charts, alerts, activity feed.
│   ├── contacts.py           Contact list, CSV/Excel import, detail view.
│   ├── pipeline.py           Kanban & list view, deal CRUD, stage history.
│   ├── followups.py          Follow-up queue with snooze and mark-contacted.
│   └── settings.py           User accounts, personal prefs, system config.
│
├── db/
│   ├── migrate.py            Schema creation. Safe to re-run (CREATE IF NOT EXISTS).
│   ├── crud.py               All database helpers. One function per operation.
│   ├── seed_user.py          CLI: create a login user interactively.
│   ├── seed_auto.py          Test-user seeder (dev convenience).
│   └── seed_demo.py          Seeds a full demo instance (contacts, deals, notes).
│
├── utils/
│   ├── config.py             load_config() / save_config(). Import from here only.
│   └── import_contacts.py    Excel/CSV parser and column auto-mapper.
│
└── data/                     SQLite databases (gitignored).
    ├── etherealcrm.db        Main database.
    ├── heritage/             Heritage demo database.
    └── neuroink/             NeuroInk demo database.
```

---

## 2. Tech Stack

| Layer        | Library            | Why                                                   |
|--------------|--------------------|-------------------------------------------------------|
| UI           | Plotly Dash        | Python-only reactive UI, no JS required               |
| Components   | Dash Bootstrap     | Grid, modals, buttons                                 |
| Charts       | Plotly             | Interactive charts with Python dicts                  |
| Database     | SQLite 3           | Single file, zero config, persists on Render disk     |
| Auth         | Flask-Login        | Session-based, bcrypt password hashing                |
| Config       | YAML               | Human-readable, gitignored, editable in Settings UI   |
| Styling      | CSS custom props   | Colors injected at startup from config, theme-able    |
| Deployment   | Render.com         | Free tier, persistent disk for SQLite                 |

---

## 3. Running the App

```bash
# First time setup
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux
pip install -r requirements.txt

# Create the database
python db/migrate.py

# Create your login account (interactive — prompts for password)
python db/seed_user.py --email you@example.com

# Start the app
python app.py                  # http://localhost:8050
```

After that, add more users directly in the **Settings → User Accounts** section — no restart needed.

---

## 4. Running Demo Instances

Each demo runs as a completely separate process with its own config and database.
They do not share any data with each other or with your main instance.

```bash
# Seed the demo databases (one-time)
python db/seed_demo.py --demo heritage
python db/seed_demo.py --demo neuroink

# Launch (run each in its own terminal)
run_heritage.bat     # http://localhost:8051  |  demo@heritagelandscaping.com / heritage2024
run_neuroink.bat     # http://localhost:8052  |  demo@neuroink.io / neuroink2024

# Mac/Linux
bash run_heritage.sh
bash run_neuroink.sh
```

### How isolation works

Each launch script sets three env vars before starting `app.py`:

| Variable     | Purpose                                             |
|--------------|-----------------------------------------------------|
| `CRM_CONFIG` | Path to the instance's config YAML                  |
| `CRM_DB`     | Path to the instance's SQLite database              |
| `CRM_PORT`   | Port number (8050 main, 8051 heritage, 8052 neuro)  |

`utils/config.py` and `db/crud.py` both read these at import time — every
module in the app automatically uses the right file for the active instance.

### Resetting a demo

```bash
# Delete the demo's database folder and re-seed
rmdir /s /q data\heritage
python db/seed_demo.py --demo heritage
```

---

## 5. Architecture Decisions

### Config lives in YAML, user preferences in SQLite

`config.yaml` holds system-wide settings (branding, stages, allowed emails).
It is gitignored so each deployment has its own branding without conflicts.

Per-user preferences (currency symbol, follow-up warning days) are stored in
the `user_settings` table as a JSON blob keyed by `user_id`. This lets multiple
users share one instance with different personal settings.

### Soft deletes

Contacts and deals are soft-deleted (`is_deleted = 1`) so data and history are
never permanently lost. Notes are hard-deleted (they are low-value individually).

### Every page loads config fresh on each render

`load_config()` is called inside `layout()`, not at module import time.
This means branding changes take effect on the next page navigation without
requiring an app restart.

### Pattern-matched callbacks need n_clicks guards

When Dash's `render_pipeline_view` callback injects new buttons into the DOM,
Dash fires the modal callbacks with `n_clicks=0`. Always guard button-triggered
branches with:

```python
if not ctx.triggered[0]['value']:
    return no_update, ...
```

---

## 6. How Dash Callbacks Work Here

Dash callbacks are Python functions decorated with `@callback`. They run on the
server every time an Input changes. The browser never executes Python.

### Key patterns used in this app

**Page skeleton → real content**
```python
# Layout renders the skeleton immediately (SSR):
html.Div(skeleton_table(rows=6), id='my-table')

# Callback replaces it with live data:
@callback(Output('my-table', 'children'), Input('refresh', 'data'),
          prevent_initial_call=False)
def load_table(refresh):
    return build_real_table(crud.get_data())
```

**Pattern-matched buttons** (edit/delete rows in a dynamic table)
```python
Input({'type': 'edit-btn', 'index': dash.ALL}, 'n_clicks')
# Then in the callback:
triggered_dict = json.loads(ctx.triggered[0]['prop_id'].split('.')[0])
row_id = triggered_dict['index']
```

**Modal open/close**
All modals follow the same three-input pattern:
```python
Input('add-btn', 'n_clicks'),           # opens with blank form
Input({'type': 'edit-btn', ...}, 'n_clicks'),  # opens with existing data
Input('cancel-btn', 'n_clicks'),        # closes
```

**`prevent_initial_call=False`** — used for components that should load data
immediately when the page renders (tables, kanban boards).

**`prevent_initial_call=True`** — used for modals and actions so they don't
fire on page navigation.

---

## 7. Adding a New Page

1. **Create the file** `pages/mypage.py`:

```python
import dash
from dash import html, dcc, callback, Input, Output
from db import crud
from utils.config import load_config

dash.register_page(__name__, path='/mypage')

def layout():
    cfg = load_config()
    return html.Div([
        html.H1("My Page", className='page-title'),
        # ...
    ])

@callback(Output('my-output', 'children'), Input('my-input', 'value'))
def my_callback(val):
    return f"You typed: {val}"
```

2. **Add a nav link** in `components/sidebar.py`:

```python
nav_link("/mypage", "bi bi-star", "My Page", pathname),
```

That's it. Dash discovers the page automatically via `use_pages=True` in `app.py`.

---

## 8. Adding a New Database Field

**Step 1 — Add column to the schema** in `db/migrate.py`:

```python
-- inside the contacts CREATE TABLE block:
my_new_field  TEXT,
```

**Step 2 — Run the migration** (safe to re-run; uses `ADD COLUMN IF NOT EXISTS`
for existing tables — SQLite doesn't support `IF NOT EXISTS` on `ADD COLUMN`,
so add a new migration block):

```python
# At the bottom of run_migration(), after the executescript:
try:
    conn.execute("ALTER TABLE contacts ADD COLUMN my_new_field TEXT")
    conn.commit()
except sqlite3.OperationalError:
    pass  # Column already exists
```

**Step 3 — Update `db/crud.py`** — add the field to `INSERT` and `UPDATE`
statements in `create_contact` and `update_contact`.

**Step 4 — Update the UI** — add an input to the contact modal in
`components/modals.py`, read it in the `save_contact` callback in
`pages/contacts.py`, and display it in `render_contact_detail`.

---

## 9. Adding a New Config Option

1. **Add a default** to `config.yaml` and `config.heritage.yaml` / `config.neuroink.yaml`.
2. **Read it** anywhere with `cfg.get('my_option', default_value)` after calling `load_config()`.
3. **Expose it in the UI** by adding an input to the System Settings section in `pages/settings.py` and saving it in the `save_settings` callback via `cfg['my_option'] = value`.

---

## 10. User Management

Users are stored in the `users` table with a bcrypt password hash.
The `allowed_emails` list in `config.yaml` is a second gate — an email must be
in both places to log in.

**Adding a user without the UI** (e.g. initial setup or from CLI):

```bash
python db/seed_user.py --email newuser@example.com
# Prompts for password, creates DB record and adds to allowed_emails
```

**From the running app**: Settings → User Accounts → Add New User.
This creates the DB record and updates `allowed_emails` automatically.
The new user can log in immediately — no restart required.

**Removing a user**: click "Remove" next to the user in Settings → User Accounts.
You cannot remove your own account.

**Changing a password**: no UI yet — re-run `seed_user.py` with the same email
(it uses `INSERT OR REPLACE`).

---

## 11. Common Gotchas

### `TypeError: update_layout() got multiple values for keyword argument 'margin'`
`_CHART_LAYOUT` in `dashboard.py` must NOT include `margin`. Each chart passes
its own `margin=_MARGIN` or `margin=_MARGIN_SRC` explicitly. Never add `margin`
back to `_CHART_LAYOUT`.

### Edit modal opens when navigating to the Pipeline page
Caused by Dash re-triggering pattern-matched callbacks when new buttons are
injected into the DOM with `n_clicks=0`. Always check
`if not ctx.triggered[0]['value']: return no_update` before acting on a
button trigger.

### Demo instances showing wrong branding
All pages import `load_config` from `utils/config.py`, which reads `CRM_CONFIG`
at import time. If `CRM_CONFIG` is not set before `import app`, the demo will
load the wrong config. The `.bat` / `.sh` scripts set it before `python app.py`.

### SQLite WAL mode
The database uses WAL (Write-Ahead Logging) for better concurrency. Do not copy
the `.db` file while the app is running — copy `.db` + `.db-wal` + `.db-shm`
together, or use `sqlite3 source.db ".backup dest.db"`.

### Config changes require a page reload
`app.py` injects CSS custom properties from config into the HTML `<head>` at
startup. Color changes made in Settings take effect on the next full page
navigation (not just a callback — a real URL change). Other config values
(stages, lists, etc.) are read fresh on each `layout()` call, so they update
immediately.

---

## 12. Deployment (Render.com)

The `render.yaml` blueprint handles everything:

```yaml
services:
  - type: web
    name: etherealcrm
    env: python
    buildCommand: pip install -r requirements.txt && python db/migrate.py
    startCommand: gunicorn app:server
    disk:
      name: crm-data
      mountPath: /opt/render/project/src/data
      sizeGB: 1
```

**After first deploy:**
1. Open a Render shell and run:
   ```bash
   python db/seed_user.py --email you@example.com
   ```
2. Add `you@example.com` to `allowed_emails` in the Settings UI.
3. Set `SECRET_KEY` as an environment variable in Render's dashboard
   (never use the default dev key in production).

**Environment variables on Render:**

| Variable     | Required | Notes                                          |
|--------------|----------|------------------------------------------------|
| `SECRET_KEY` | Yes      | Long random string, set in Render dashboard    |
| `CRM_CONFIG` | No       | Defaults to `config.yaml` in project root      |
| `CRM_DB`     | No       | Defaults to `data/etherealcrm.db`              |
