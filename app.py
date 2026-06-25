"""
app.py — EtherealCRM entry point.
Loads config, sets up Flask-Login, assembles Dash multi-page layout.
Run: python app.py
"""

import os
import yaml
import flask
import bcrypt
import flask_login

import dash
from dash import html, dcc, Input, Output, State, no_update
import dash_bootstrap_components as dbc

from components.sidebar import render_sidebar
from db import crud

# ── Load Config ───────────────────────────────────────────────────────────────

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.yaml')


def load_config() -> dict:
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)


CONFIG = load_config()


def css_vars_from_config(cfg: dict) -> str:
    """Build a <style> tag injecting CSS custom properties from config."""
    return f"""
    :root {{
        --color-primary:       {cfg.get('color_primary', '#FF120A')};
        --color-primary-hover: {cfg.get('color_primary_hover', '#960502')};
        --color-primary-deep:  {cfg.get('color_primary_deep', '#550A04')};
        --color-bg-dark:       {cfg.get('color_bg_dark', '#370E08')};
        --color-text-body:     {cfg.get('color_text_body', '#36454F')};
        --color-text-light:    {cfg.get('color_text_light', '#FFFFFF')};
    }}
    """


# ── Flask-Login Setup ─────────────────────────────────────────────────────────

login_manager = flask_login.LoginManager()


class User(flask_login.UserMixin):
    def __init__(self, user_id: str, email: str):
        self.id = user_id
        self.email = email


@login_manager.user_loader
def load_user(user_id: str):
    data = crud.get_user_by_id(user_id)
    if data:
        return User(data['user_id'], data['email'])
    return None


# ── Dash App ──────────────────────────────────────────────────────────────────

app = dash.Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap',
    ],
    title=CONFIG.get('agency_name', 'EtherealCRM') + ' CRM',
    meta_tags=[
        {'name': 'viewport', 'content': 'width=device-width, initial-scale=1'},
        {'name': 'description', 'content': 'Internal CRM for ' + CONFIG.get('agency_name', 'Etherea Labs')},
    ],
)
server = app.server
server.secret_key = os.environ.get('SECRET_KEY', 'ethereacrm-dev-secret-change-in-prod')
login_manager.init_app(server)
login_manager.login_view = '/login'


# ── Index Template ────────────────────────────────────────────────────────────

app.index_string = f"""<!DOCTYPE html>
<html lang="en">
<head>
    {{%metas%}}
    <title>{{%title%}}</title>
    {{%favicon%}}
    {{%css%}}
    <style>
        {css_vars_from_config(CONFIG)}
    </style>
</head>
<body>
{{%app_entry%}}
<footer>{{%config%}}{{%scripts%}}{{%renderer%}}</footer>
</body>
</html>"""


# ── Login Page Layout ─────────────────────────────────────────────────────────

def login_layout():
    cfg = load_config()
    return html.Div(
        id='login-page',
        children=[
            html.Div(
                className='login-card',
                children=[
                    html.Img(src=cfg.get('logo_url', ''), className='login-logo',
                             alt=cfg.get('agency_name', '')),
                    html.H1(cfg.get('agency_name', 'EtherealCRM'),
                            className='login-agency-name'),
                    html.P('Sign in to your CRM', className='login-tagline'),
                    html.Div(id='login-error-msg'),
                    dcc.Input(
                        id='login-email', type='email',
                        placeholder='Email address',
                        style={'width': '100%', 'padding': '10px 14px',
                               'border': '1px solid #d0d5dd', 'borderRadius': '6px',
                               'fontSize': '14px', 'marginBottom': '12px'},
                        debounce=False,
                        n_submit=0,
                    ),
                    dcc.Input(
                        id='login-password', type='password',
                        placeholder='Password',
                        style={'width': '100%', 'padding': '10px 14px',
                               'border': '1px solid #d0d5dd', 'borderRadius': '6px',
                               'fontSize': '14px', 'marginBottom': '20px'},
                        debounce=False,
                        n_submit=0,
                    ),
                    html.Button(
                        '🔐  Sign In',
                        id='login-submit-btn',
                        className='btn-primary',
                        style={'width': '100%', 'padding': '11px',
                               'fontSize': '14px', 'justifyContent': 'center'},
                        n_clicks=0,
                    ),
                ]
            )
        ]
    )


# ── Main App Layout ───────────────────────────────────────────────────────────

app.layout = html.Div([
    dcc.Location(id='url', refresh=True),
    dcc.Store(id='current-user-store', storage_type='session'),
    html.Div(id='app-root'),
])


# ── Auth Routing Callback ─────────────────────────────────────────────────────

@app.callback(
    Output('app-root', 'children'),
    Input('url', 'pathname'),
)
def route(pathname):
    # Reload config so branding changes in settings take effect
    cfg = load_config()

    if pathname in (None, '/', ''):
        return dcc.Location(pathname='/dashboard', id='redir-home', refresh=True)

    if pathname == '/logout':
        flask_login.logout_user()
        return dcc.Location(pathname='/login', id='redir-logout', refresh=True)

    if pathname == '/login':
        return login_layout()

    # All other routes require login
    if not flask_login.current_user.is_authenticated:
        return dcc.Location(pathname='/login', id='redir-auth', refresh=True)

    return html.Div(
        id='app-container',
        children=[
            render_sidebar(cfg, pathname),
            html.Div(id='page-content', children=[
                dash.page_container,
            ]),
        ]
    )


# ── Login Callback ─────────────────────────────────────────────────────────────

@app.callback(
    Output('url', 'pathname'),
    Output('login-error-msg', 'children'),
    Input('login-submit-btn', 'n_clicks'),
    Input('login-password', 'n_submit'),
    State('login-email', 'value'),
    State('login-password', 'value'),
    prevent_initial_call=True,
)
def handle_login(n_clicks, n_submit, email, password):
    if not email or not password:
        return no_update, html.Div('Please enter your email and password.',
                                   className='login-error')

    cfg = load_config()
    allowed = [e.lower() for e in cfg.get('allowed_emails', [])]
    if email.lower() not in allowed:
        return no_update, html.Div('Access denied for this email address.',
                                   className='login-error')

    user_data = crud.get_user_by_email(email)
    if not user_data:
        return no_update, html.Div('Invalid email or password.', className='login-error')

    if not bcrypt.checkpw(password.encode(), user_data['password_hash'].encode()):
        return no_update, html.Div('Invalid email or password.', className='login-error')

    user = User(user_data['user_id'], user_data['email'])
    flask_login.login_user(user, remember=True)
    return '/dashboard', ''


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # Run database migration on startup if db doesn't exist yet
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'etherealcrm.db')
    if not os.path.exists(db_path):
        print("[app] Database not found — running migration...")
        from db.migrate import run_migration
        run_migration()

    app.run(debug=True, host='0.0.0.0', port=8050)
