# EtherealCRM — MVP Setup & Deployment

EtherealCRM is a lightweight, internal CRM built specifically for Etherea Labs to manage prospects, active clients, notes, and follow-ups.

## Features

- **Dashboard**: High-level stats, follow-up alerts, recent notes activity, and deals by stage (Plotly bar chart).
- **Contacts**: List view with searching, filtering, detail profile view, associated deals, notes timeline, and full CRUD.
- **Pipeline**: Kanban board view, List view toggle, detail deal page, stage history transition logging, and CRUD.
- **Follow-ups**: Overdue/today/soon follow-ups with color-coded urgency, snooze, and mark contacted logging.
- **Settings**: Complete brand customization, system list editor, whitelist email whitelist, and live preview.

## Developer Setup Checklist

1. **Clone Repo and Create Python Virtual Environment**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Database Setup (SQLite)**:
   Run the migration script to create `data/etherealcrm.db` with all tables:
   ```bash
   python db/migrate.py
   ```
4. **Seed First Login User**:
   Run the seed CLI script to create your login password:
   ```bash
   python db/seed_user.py --email etherealabsco@gmail.com
   ```
5. **Run Locally**:
   ```bash
   python app.py
   ```
   Open your browser at `http://localhost:8050/`.

## White-Labeling

To white-label EtherealCRM for another brand, simply edit `config.yaml` or change branding settings directly inside the **System Settings** in-app editor. No code modifications are needed.

## Deployment on Render.com

This repository includes a `render.yaml` file for easy deployment using Render's Blueprint:
1. Push this code to your GitHub repository.
2. In Render dashboard, click **New > Blueprint**.
3. Select this repository.
4. Render will provision the web service, build dependencies, and start the app automatically.
