# EtherealCRM — MVP Specification

**Prepared for:** Etherea Labs Development Team
**Version:** 1.0 — MVP
**Status:** Ready for Development
**Confidentiality:** Internal Use Only

---

## 1. Executive Summary

EtherealCRM is a lightweight, internal CRM built specifically for Etherea Labs to manage prospects, active clients, notes, and follow-ups — without the bloat of enterprise tools or the pain of managing a hosted database.

The system is designed around three core principles:

- **Simple to use** — the team should be able to open it and immediately understand where everything is.
- **Easy to maintain** — the database is a single file on the server, inspectable and editable with a free GUI tool, and trivially backed up by copying one file.
- **White-label ready** — branding, agency name, colors, and logo are all driven by a config file so the product can be resold or licensed in the future.

---

## 2. Brand Identity

The CRM must reflect Etherea Labs branding from day one. All colors below should be applied consistently across the UI — sidebar, buttons, charts, cards, and status indicators.

### Color Palette

| Role | Name | Hex | Usage |
|---|---|---|---|
| Primary | Main Red | `#FF120A` | CTAs, logo mark, primary accents, active nav item, primary buttons |
| Secondary | Secondary Red | `#960502` | Hover states, gradient endpoints, button hover |
| Tertiary | Tertiary Red | `#550A04` | Deep accents, input focus rings, shadow tones |
| Background | Dark Background | `#370E08` | Sidebar, hero sections, dark UI panels, page background |
| Body Text | Slate Grey | `#36454F` | Body text on light backgrounds, secondary labels |
| Light | White | `#FFFFFF` | Text on dark backgrounds, card backgrounds |

### Logo

The Etherea Labs logo is served from the site CDN. Use this URL in `config.yaml` and display it in the sidebar header and login screen:

```
https://etherealabs.co/_astro/logo.CE6jKDrv_1rERT.webp
```

### CSS Variable Mapping

The developer should inject these as CSS custom properties at app startup so every component inherits them automatically:

```css
:root {
  --color-primary:     #FF120A;
  --color-primary-hover: #960502;
  --color-primary-deep: #550A04;
  --color-bg-dark:     #370E08;
  --color-text-body:   #36454F;
  --color-text-light:  #FFFFFF;
}
```

### UI Tone

The overall feel should mirror the Etherea Labs site: dark, premium, high-contrast. The sidebar and top bar use `#370E08` as the background with white text. Cards and data panels use a white or very light background with `#36454F` body text. The `#FF120A` red is used sparingly and intentionally — primary buttons, active states, and key callout numbers only.

---

## 3. Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| Frontend / UI | Plotly Dash (Python) | Requested by client; reactive, Python-native, no JS required |
| Database | SQLite | Single `.db` file, zero setup, built into Python stdlib, free forever |
| DB GUI | DB Browser for SQLite | Free desktop app for inspecting/editing the database directly |
| Auth | Flask-Login + password file | Simple whitelist auth; no external service required for MVP |
| Deployment | Render.com or Railway (free tier) | Zero-cost hosting; push-to-deploy via GitHub |
| Config / Branding | `config.yaml` | All white-label settings live here; change once, affects whole app |
| File / Doc Links | URLs stored in the database | Links to Google Drive, Dropbox, or any URL — no file storage to manage |

### Why SQLite?

SQLite is a single `.db` file that lives on the server alongside the app. Python has it built in (`import sqlite3`) — no extra dependencies, no server process, no account to create. For an internal team tool at agency scale, it's more than sufficient. The file can be backed up by simply copying it. If you ever need to scale up to a hosted Postgres database (Supabase, Neon, etc.), the schema translates directly with minimal code changes.

A free GUI called [DB Browser for SQLite](https://sqlitebrowser.org/) lets anyone on the team open the `.db` file and view or edit data directly, similar to a spreadsheet.

---

## 4. Data Model

All tables live in a single `etherealcrm.db` SQLite file. The developer should run the schema migration on first deploy.

### 4.1 contacts

| Column | Type | Notes |
|---|---|---|
| contact_id | TEXT (UUID) | Primary key, generated on creation |
| first_name | TEXT | |
| last_name | TEXT | |
| company | TEXT | Business name |
| email | TEXT | Primary contact email |
| phone | TEXT | |
| city | TEXT | |
| state | TEXT | |
| source | TEXT | Website, Referral, LinkedIn, Cold Outreach, Other |
| tags | TEXT | Comma-separated: e.g. `landscaping,local-seo` |
| created_at | TEXT (ISO timestamp) | Auto-set on creation |
| updated_at | TEXT (ISO timestamp) | Auto-updated on any edit |

### 4.2 deals

| Column | Type | Notes |
|---|---|---|
| deal_id | TEXT (UUID) | Primary key |
| contact_id | TEXT (UUID) | Foreign key → contacts |
| deal_name | TEXT | e.g. `Heritage Landscaping — Website Redesign` |
| service_type | TEXT | Web Design, Web App, SEO, Consulting, Landing Page, Other |
| stage | TEXT | New Lead, Contacted, Proposal Sent, Negotiating, Won, Lost, On Hold |
| value | REAL | Estimated deal value in USD |
| probability | INTEGER | 0–100; used for pipeline forecasting |
| next_follow_up | TEXT (ISO date) | Drives the Follow-Up view; required if stage is not Won or Lost |
| assigned_to | TEXT | Team member name |
| close_date | TEXT (ISO date) | Expected or actual close date |
| created_at | TEXT (ISO timestamp) | Auto-set |
| updated_at | TEXT (ISO timestamp) | Auto-updated |

### 4.3 notes

| Column | Type | Notes |
|---|---|---|
| note_id | TEXT (UUID) | Primary key |
| deal_id | TEXT (UUID) | Foreign key → deals (nullable if contact-level note) |
| contact_id | TEXT (UUID) | Foreign key → contacts (nullable if deal-level note) |
| note_type | TEXT | Call, Email, Meeting, Internal, Document Link |
| body | TEXT | Free-text note content |
| doc_link | TEXT | URL to any linked file (Google Drive, Dropbox, etc.) |
| created_by | TEXT | Team member who added the note |
| created_at | TEXT (ISO timestamp) | Auto-set |

### 4.4 stage_history

Automatically logged whenever a deal's stage changes. No manual input required.

| Column | Type | Notes |
|---|---|---|
| history_id | TEXT (UUID) | Primary key |
| deal_id | TEXT (UUID) | Foreign key → deals |
| from_stage | TEXT | Previous stage |
| to_stage | TEXT | New stage |
| changed_by | TEXT | Team member who made the change |
| changed_at | TEXT (ISO timestamp) | Auto-set |

---

## 5. Configuration

All branding and app-level settings live in `config.yaml` at the project root. This file is loaded at app startup. To white-label for another client, update this file and redeploy — no code changes required.

```yaml
# config.yaml

agency_name: "Etherea Labs"
logo_url: "https://etherealabs.co/_astro/logo.CE6jKDrv_1rERT.webp"

# Brand colors — update these to white-label for another client
color_primary:        "#FF120A"   # Main Red — CTAs, buttons, active nav, primary accents
color_primary_hover:  "#960502"   # Secondary Red — hover states, gradient endpoints
color_primary_deep:   "#550A04"   # Tertiary Red — deep accents, focus rings, shadows
color_bg_dark:        "#370E08"   # Dark Background — sidebar, hero panels, page bg
color_text_body:      "#36454F"   # Slate Grey — body text on light backgrounds
color_text_light:     "#FFFFFF"   # White — text on dark backgrounds, card surfaces

currency_symbol: "$"

follow_up_warning_days: 3

deal_stages:
  - New Lead
  - Contacted
  - Proposal Sent
  - Negotiating
  - Won
  - Lost
  - On Hold

service_types:
  - Web Design
  - Web App
  - SEO
  - Consulting
  - Landing Page
  - Other

lead_sources:
  - Website
  - Referral
  - LinkedIn
  - Cold Outreach
  - Other

# Auth: comma-separated list of allowed login emails
allowed_emails:
  - you@etherealabs.co
  - teammate@etherealabs.co
```

---

## 6. MVP Features

### 6.1 Dashboard

- Pipeline summary: total open deals, total pipeline value, deals by stage (bar chart)
- Follow-up alerts: deals where `next_follow_up` is today or overdue, sorted by urgency
- Recent activity: last 10 notes added across all deals
- Win rate: Won / (Won + Lost) displayed as a stat card

### 6.2 Contacts

- List view: searchable, filterable table (name, company, email, source, number of open deals)
- Create / Edit contact form with validation
- Delete contact with confirmation (soft-delete recommended — see open questions)
- Contact detail page: contact info + linked deals + associated notes

### 6.3 Deals (Pipeline)

- Kanban view: columns per stage, cards show deal name, contact, value, next follow-up date
- List view: sortable/filterable table as alternative to kanban
- Create / Edit deal form: all fields, contact autocomplete from existing contacts
- Delete deal with confirmation
- Deal detail page: full deal info, notes, document links, stage history log
- Stage changes auto-log a row to `stage_history`

### 6.4 Notes & Documents

- Add notes from the deal or contact detail page
- Note types: Call, Email, Meeting, Internal, Document Link
- Document Link type: stores a URL and displays it as a clickable link on the deal
- Edit / Delete notes with confirmation
- Notes sorted newest-first by default

### 6.5 Follow-Up View

- Dedicated page listing all deals with `next_follow_up` today or earlier
- Color-coded urgency: red = overdue, amber = due today, green = due within `follow_up_warning_days`
- Snooze button: pushes `next_follow_up` forward by `follow_up_warning_days` (from config)
- Mark Contacted button: logs a note and prompts for a new follow-up date

### 6.6 Settings Page

An in-app settings UI that reads/writes `config.yaml`. Editable fields:

- Agency name, logo URL, and all brand colors (with live branding preview)
- Deal stage list (add, remove, reorder)
- Service type list
- Lead source list
- Follow-up warning threshold in days
- Currency symbol
- Allowed email list (for auth whitelist)

---

## 7. Navigation & Layout

Persistent left sidebar, multi-page routing via `dash.page_registry`.

| Nav Item | Description |
|---|---|
| Dashboard | Overview cards, pipeline chart, follow-up alerts, recent activity |
| Contacts | Contact list with links to individual contact detail pages |
| Pipeline | Kanban or list view of all deals; toggle between views |
| Follow-Ups | Urgency-sorted list of pending follow-ups |
| Settings | Branding and configuration editor |

The sidebar header shows the agency logo and name from `config.yaml`. On smaller screens the sidebar collapses to icons only.

---

## 8. White-Labeling

All customer-facing branding is controlled by `config.yaml`. To white-label for a new client:

1. Update `agency_name`, `logo_url`, and all `color_*` fields in `config.yaml`
2. Push to GitHub — Render/Railway auto-deploys
3. No code changes required

The colors from `config.yaml` are injected as CSS variables (`--color-primary`, `--color-bg-dark`, etc.) at app startup, so Dash components, charts, and sidebar all update automatically.

---

## 9. Authentication

For MVP, authentication uses Flask-Login with a simple email + password approach. Allowed emails are defined in `config.yaml`. Passwords are stored as bcrypt hashes in a `users` table in the SQLite database (never plain text).

Post-MVP, this can be upgraded to Google OAuth or SSO with minimal changes to the auth layer.

---

## 10. Out of Scope for MVP

The following are explicitly deferred to keep the build lean:

- Email integration (sending/receiving from within the CRM)
- Automated follow-up reminders via email or SMS
- Invoice or billing management
- Time tracking
- Client-facing portal
- Mobile app
- Role-based permissions beyond email whitelist
- Advanced reporting or analytics

---

## 11. Suggested Development Milestones

| # | Milestone | Deliverables | Est. Effort |
|---|---|---|---|
| 1 | Project Setup | Repo, Render deployment, SQLite schema migration, config.yaml loader, auth skeleton | 1–2 days |
| 2 | Data Layer | CRUD helper functions for all tables, UUID generation, timestamp logic | 1–2 days |
| 3 | Contacts Module | List, create, edit, delete, detail page | 2 days |
| 4 | Deals / Pipeline | Kanban + list view, create, edit, delete, deal detail page, stage history logging | 3–4 days |
| 5 | Notes & Docs | Add/edit/delete notes, document link type, display on deal/contact pages | 1–2 days |
| 6 | Dashboard | Stat cards, pipeline bar chart (Plotly), follow-up alerts, recent activity | 2 days |
| 7 | Follow-Up View | Urgency list, snooze, mark contacted | 1 day |
| 8 | Settings Page | In-app config editor wired to config.yaml, live brand preview | 1–2 days |
| 9 | Polish & QA | Mobile sidebar, error states, empty states, cross-browser test | 2 days |

**Total estimated effort:** 14–19 developer days for a solo developer familiar with Dash.

---

## 12. Dependencies

Add to `requirements.txt`:

```
dash
dash-bootstrap-components
plotly
pandas
pyyaml
flask-login
bcrypt
```

Everything else (`sqlite3`, `uuid`, `datetime`) is Python stdlib — no install needed.

### Developer Setup Checklist

- [ ] Clone repo and create a Python virtual environment
- [ ] `pip install -r requirements.txt`
- [ ] Copy `config.yaml.example` to `config.yaml` and fill in values
- [ ] Run `python db/migrate.py` to create `etherealcrm.db` with schema
- [ ] Run `python db/seed_user.py --email you@etherealabs.co` to create the first login
- [ ] `python app.py` to run locally
- [ ] Push to GitHub and connect to Render or Railway for deployment
- [ ] Set `config.yaml` values as environment variables on the host (never commit secrets to Git)

### Recommended Dev Tools

- [DB Browser for SQLite](https://sqlitebrowser.org/) — free GUI to view/edit the `.db` file directly
- [Dash documentation](https://dash.plotly.com/) — multi-page apps, callbacks, components

---

## 13. Open Questions for the Developer

1. **Kanban drag-and-drop:** Use a drag-and-drop library (e.g. `dash-draggable`) or just a dropdown for stage changes on MVP?
2. **Soft vs. hard delete:** Archive contacts/deals (hide but keep) or permanently delete? Soft-delete is recommended for data safety.
3. **Note editability:** Should notes be editable after creation, or append-only for auditability?
4. **SQLite file location:** Store `etherealcrm.db` in the repo root, or a dedicated `/data` directory that's excluded from Git?
5. **Hosting preference:** Render.com or Railway? (Both free tiers work; Railway has slightly more generous free compute.)

---

*Prepared by Etherea Labs Leadership — Not for external distribution*
