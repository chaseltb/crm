"""
pages/settings.py — Settings page for EtherealCRM.

Three sections, each with their own save scope:
  - User Accounts      → users table + allowed_emails in config  (live, no restart needed)
  - Personal Prefs     → user_settings table, per logged-in user
  - System Settings    → config.yaml  (branding, stages, lists)
"""

import dash
from dash import html, dcc, callback, Input, Output, State, no_update, ctx
import dash_bootstrap_components as dbc
import flask_login

from db import crud
from utils.config import load_config, save_config

dash.register_page(__name__, path='/settings')


# ── Layout ────────────────────────────────────────────────────────────────────

def layout():
    cfg       = load_config()
    user      = flask_login.current_user
    user_prefs = crud.get_user_settings(user.id) if user.is_authenticated else {}
    all_users = crud.get_all_users()

    stages_str   = "\n".join(cfg.get('deal_stages', []))
    services_str = "\n".join(cfg.get('service_types', []))
    sources_str  = "\n".join(cfg.get('lead_sources', []))
    emails_str   = "\n".join(cfg.get('allowed_emails', []))

    def form_input(label, fid, val, typ='text', placeholder=''):
        return html.Div(className='form-group mb-3', children=[
            html.Label(label, className='form-label'),
            dcc.Input(id=fid, type=typ, value=val, placeholder=placeholder,
                      className='form-control')
        ])

    def form_textarea(label, fid, val, help_text):
        return html.Div(className='form-group mb-3', children=[
            html.Label(label, className='form-label'),
            dcc.Textarea(id=fid, value=val, className='form-control',
                         style={'height': '120px', 'fontFamily': 'monospace'}),
            html.Small(help_text, style={'color': '#8890a0', 'marginTop': '4px', 'display': 'block'})
        ])

    # ── User list rows ────────────────────────────────────────────────────────
    def user_row(u):
        is_self = user.is_authenticated and u['user_id'] == user.id
        return html.Div(
            style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between',
                   'padding': '10px 0', 'borderBottom': '1px solid #f3f4f6'},
            children=[
                html.Div([
                    html.Span(u['email'], style={'fontWeight': '600', 'color': '#1a1a2e'}),
                    html.Span(' (you)' if is_self else '',
                              style={'color': '#9ca3af', 'fontSize': '12px', 'marginLeft': '6px'}),
                    html.Div(f"Added {u['created_at'][:10]}",
                             style={'fontSize': '11.5px', 'color': '#9ca3af', 'marginTop': '2px'}),
                ]),
                html.Button(
                    [html.I(className='bi bi-trash me-1'), "Remove"],
                    id={'type': 'remove-user-btn', 'index': u['user_id']},
                    className='btn-danger btn-sm',
                    disabled=is_self,
                    title="You cannot remove your own account" if is_self else "Remove this user",
                )
            ]
        )

    user_list = html.Div(
        id='user-list-container',
        children=[user_row(u) for u in all_users] if all_users else
                 html.Div("No users found.", style={'color': '#9ca3af', 'fontSize': '13px'})
    )

    return html.Div([
        dcc.Store(id='user-mgmt-refresh', data=0),

        html.Div(className='page-header', children=[
            html.Div([
                html.H1("Settings", className='page-title'),
                html.P("Manage user accounts, your preferences, and system configuration.",
                       className='page-subtitle'),
            ]),
        ]),

        html.Div(id='settings-alert-container'),

        # ── User Accounts ─────────────────────────────────────────────────────
        html.Div(className='settings-section mb-4', children=[
            html.Div("User Accounts", className='settings-section-header'),
            html.Div(className='settings-section-body', children=[
                html.P("Add or remove login accounts. Changes take effect immediately — "
                       "no restart required.",
                       style={'color': '#8890a0', 'fontSize': '13px', 'marginBottom': '16px'}),

                user_list,

                html.Div(style={'marginTop': '20px', 'paddingTop': '16px',
                                'borderTop': '1px solid #f3f4f6'}, children=[
                    html.Div("Add New User", style={'fontWeight': '600', 'fontSize': '13px',
                                                    'color': '#374151', 'marginBottom': '12px'}),
                    html.Div(style={'display': 'flex', 'gap': '12px', 'flexWrap': 'wrap',
                                    'alignItems': 'flex-end'}, children=[
                        html.Div(style={'flex': 2, 'minWidth': '200px'}, children=[
                            html.Label("Email", className='form-label'),
                            dcc.Input(id='new-user-email', type='email', placeholder='user@example.com',
                                      className='form-control'),
                        ]),
                        html.Div(style={'flex': 2, 'minWidth': '200px'}, children=[
                            html.Label("Password", className='form-label'),
                            dcc.Input(id='new-user-password', type='password',
                                      placeholder='Min 8 characters', className='form-control'),
                        ]),
                        html.Div(style={'flex': 1, 'minWidth': '140px', 'paddingBottom': '1px'}, children=[
                            html.Button(
                                [html.I(className='bi bi-person-plus-fill me-2'), "Add User"],
                                id='add-user-btn', className='btn-primary',
                                style={'width': '100%'}
                            )
                        ]),
                    ]),
                    html.Div(id='add-user-error', style={'marginTop': '8px'}),
                ])
            ])
        ]),

        # ── Personal Preferences ──────────────────────────────────────────────
        html.Div(className='settings-section mb-4', children=[
            html.Div("Personal Preferences", className='settings-section-header'),
            html.Div(className='settings-section-body', children=[
                html.P("Saved to your account only — other users are unaffected.",
                       style={'color': '#8890a0', 'fontSize': '13px', 'marginBottom': '16px'}),
                html.Div(style={'display': 'flex', 'gap': '16px', 'flexWrap': 'wrap'}, children=[
                    html.Div(style={'flex': 1, 'minWidth': '180px'}, children=[
                        form_input("Currency Symbol", "u-currency",
                                   user_prefs.get('currency_symbol', cfg.get('currency_symbol', '$')))
                    ]),
                    html.Div(style={'flex': 1, 'minWidth': '180px'}, children=[
                        form_input("Follow-up Warning (days)", "u-warning-days",
                                   user_prefs.get('follow_up_warning_days',
                                                  cfg.get('follow_up_warning_days', 3)), typ='number')
                    ]),
                ]),
                html.Button("Save My Preferences", id='save-user-prefs-btn', className='btn-primary'),
            ])
        ]),

        # ── System Settings ───────────────────────────────────────────────────
        html.Div(className='row', children=[
            html.Div([
                html.Div(className='settings-section', children=[
                    html.Div("Agency & Branding", className='settings-section-header'),
                    html.Div(className='settings-section-body', children=[
                        form_input("Agency Name", "s-agency-name", cfg.get('agency_name', '')),
                        form_input("Logo Image CDN URL", "s-logo-url", cfg.get('logo_url', '')),
                    ])
                ]),

                html.Div(className='settings-section mt-4', children=[
                    html.Div("Brand Theme Colors (HEX)", className='settings-section-header'),
                    html.Div(className='settings-section-body', children=[
                        html.Div([
                            html.Div(form_input("Primary Accent", "s-c-primary",
                                                cfg.get('color_primary', '')), style={'flex': 1}),
                            html.Div(form_input("Primary Hover", "s-c-primary-hover",
                                                cfg.get('color_primary_hover', '')), style={'flex': 1}),
                        ], style={'display': 'flex', 'gap': '12px'}),
                        html.Div([
                            html.Div(form_input("Primary Deep", "s-c-primary-deep",
                                                cfg.get('color_primary_deep', '')), style={'flex': 1}),
                            html.Div(form_input("Sidebar Background", "s-c-bg-dark",
                                                cfg.get('color_bg_dark', '')), style={'flex': 1}),
                        ], style={'display': 'flex', 'gap': '12px'}),
                        html.Div([
                            html.Div(form_input("Body Text", "s-c-text-body",
                                                cfg.get('color_text_body', '')), style={'flex': 1}),
                            html.Div(form_input("Light Panels", "s-c-text-light",
                                                cfg.get('color_text_light', '')), style={'flex': 1}),
                        ], style={'display': 'flex', 'gap': '12px'}),
                    ])
                ]),

                html.Div(className='settings-section mt-4', children=[
                    html.Div("Authentication Whitelist", className='settings-section-header'),
                    html.Div(className='settings-section-body', children=[
                        form_textarea("Allowed Emails", "s-emails", emails_str,
                                      "One email per line. Must match a user account above to log in.")
                    ])
                ]),
            ], className='col-lg-7 col-12'),

            html.Div([
                # Live Preview
                html.Div(className='settings-section mb-4', children=[
                    html.Div("Live Brand Preview", className='settings-section-header'),
                    html.Div(className='settings-section-body', children=[
                        html.Div([
                            html.Div(id='p-sidebar', children=[
                                html.Div(cfg.get('agency_name', 'Agency'), id='p-sidebar-text',
                                         style={'color': '#fff', 'fontWeight': 'bold', 'padding': '12px',
                                                'borderBottom': '1px solid rgba(255,255,255,0.1)'}),
                                html.Div("Dashboard", id='p-sidebar-link',
                                         style={'padding': '10px 12px', 'fontSize': '12.5px',
                                                'color': '#fff', 'marginTop': '10px'})
                            ], style={'width': '140px', 'height': '140px',
                                      'backgroundColor': cfg.get('color_bg_dark'),
                                      'borderRadius': '6px', 'overflow': 'hidden',
                                      'float': 'left', 'marginRight': '20px'}),
                            html.Div([
                                html.Button("Primary CTA", id='p-btn', className='btn-primary',
                                            style={'backgroundColor': cfg.get('color_primary'),
                                                   'border': 'none', 'color': '#fff'}),
                                html.Br(), html.Br(),
                                html.Span("Demo Tag", id='p-tag', className='tag',
                                          style={'backgroundColor': '#fee2e2',
                                                 'color': cfg.get('color_primary')})
                            ], style={'overflow': 'hidden'})
                        ], style={'display': 'flex', 'alignItems': 'center'})
                    ])
                ]),

                # System Lists
                html.Div(className='settings-section', children=[
                    html.Div("System List Values", className='settings-section-header'),
                    html.Div(className='settings-section-body', children=[
                        form_textarea("Deal Stages", "s-stages", stages_str,
                                      "One stage per line. Does not rename stages on existing deals."),
                        form_textarea("Service Types", "s-services", services_str,
                                      "One type per line."),
                        form_textarea("Lead Sources", "s-sources", sources_str,
                                      "One source per line.")
                    ])
                ]),

                html.Button("Save System Settings", id='save-settings-btn',
                            className='btn-primary mt-3'),
            ], className='col-lg-5 col-12')
        ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px'})
    ])


# ── Callbacks ─────────────────────────────────────────────────────────────────

@callback(
    Output('p-sidebar', 'style'),
    Output('p-sidebar-link', 'style'),
    Output('p-sidebar-text', 'innerHTML'),
    Output('p-btn', 'style'),
    Output('p-tag', 'style'),
    Input('s-agency-name', 'value'),
    Input('s-c-primary', 'value'),
    Input('s-c-bg-dark', 'value'),
    prevent_initial_call=True
)
def update_branding_preview(agency, primary, bg_dark):
    sidebar_style     = {'width': '140px', 'height': '140px',
                         'backgroundColor': bg_dark or '#370E08',
                         'borderRadius': '6px', 'overflow': 'hidden',
                         'float': 'left', 'marginRight': '20px'}
    sidebar_link_style = {'padding': '10px 12px', 'fontSize': '12.5px',
                          'backgroundColor': primary or '#FF120A',
                          'color': '#fff', 'marginTop': '10px'}
    btn_style  = {'backgroundColor': primary or '#FF120A', 'border': 'none', 'color': '#fff'}
    tag_style  = {'backgroundColor': '#fee2e2', 'color': primary or '#FF120A'}
    return sidebar_style, sidebar_link_style, agency or 'Agency', btn_style, tag_style


@callback(
    Output('settings-alert-container', 'children'),
    Input('save-user-prefs-btn', 'n_clicks'),
    Input('save-settings-btn', 'n_clicks'),
    State('u-currency', 'value'),
    State('u-warning-days', 'value'),
    State('s-agency-name', 'value'),
    State('s-logo-url', 'value'),
    State('s-c-primary', 'value'),
    State('s-c-primary-hover', 'value'),
    State('s-c-primary-deep', 'value'),
    State('s-c-bg-dark', 'value'),
    State('s-c-text-body', 'value'),
    State('s-c-text-light', 'value'),
    State('s-emails', 'value'),
    State('s-stages', 'value'),
    State('s-services', 'value'),
    State('s-sources', 'value'),
    prevent_initial_call=True
)
def save_settings(user_clicks, sys_clicks,
                  currency, warning_days,
                  agency, logo, primary, hover, deep, bg_dark, text_body, text_light,
                  emails, stages, services, sources):
    try:
        if ctx.triggered_id == 'save-user-prefs-btn':
            user = flask_login.current_user
            if not user.is_authenticated:
                return _alert('danger', 'Not authenticated.')
            crud.save_user_settings(user.id, {
                'currency_symbol':        currency or '$',
                'follow_up_warning_days': int(warning_days or 3),
            })
            return _alert('success', 'Your preferences saved.')

        if ctx.triggered_id == 'save-settings-btn':
            cfg = load_config()
            cfg.update({
                'agency_name':         agency,
                'logo_url':            logo,
                'color_primary':       primary,
                'color_primary_hover': hover,
                'color_primary_deep':  deep,
                'color_bg_dark':       bg_dark,
                'color_text_body':     text_body,
                'color_text_light':    text_light,
                'allowed_emails':  [e.strip() for e in (emails  or '').split('\n') if e.strip()],
                'deal_stages':     [s.strip() for s in (stages  or '').split('\n') if s.strip()],
                'service_types':   [s.strip() for s in (services or '').split('\n') if s.strip()],
                'lead_sources':    [s.strip() for s in (sources  or '').split('\n') if s.strip()],
            })
            save_config(cfg)
            return _alert('success', 'System settings saved. Branding updates on next page load.')

    except Exception as exc:
        return _alert('danger', f'Error: {exc}')

    return no_update


@callback(
    Output('user-list-container', 'children'),
    Output('add-user-error', 'children'),
    Output('new-user-email', 'value'),
    Output('new-user-password', 'value'),
    Input('add-user-btn', 'n_clicks'),
    Input({'type': 'remove-user-btn', 'index': dash.ALL}, 'n_clicks'),
    State('new-user-email', 'value'),
    State('new-user-password', 'value'),
    prevent_initial_call=True
)
def manage_users(add_clicks, remove_clicks, email, password):
    triggered_id  = ctx.triggered_id
    trigger_value = ctx.triggered[0]['value'] if ctx.triggered else None

    # Guard against DOM-injection spurious fires (n_clicks == 0 or None)
    if not trigger_value:
        return no_update, no_update, no_update, no_update

    current_user = flask_login.current_user

    # ── Remove user ───────────────────────────────────────────────────────────
    if isinstance(triggered_id, dict) and triggered_id.get('type') == 'remove-user-btn':
        user_id = triggered_id['index']
        if current_user.is_authenticated and user_id == current_user.id:
            return no_update, _alert('danger', 'You cannot remove your own account.'), \
                   no_update, no_update
        try:
            # Get the email before deleting so we can remove it from allowed_emails
            target = crud.get_user_by_id(user_id)
            if target:
                crud.delete_user_account(user_id)
                cfg = load_config()
                cfg['allowed_emails'] = [
                    e for e in cfg.get('allowed_emails', [])
                    if e.lower() != target['email'].lower()
                ]
                save_config(cfg)
        except Exception as exc:
            return no_update, _alert('danger', f'Error removing user: {exc}'), \
                   no_update, no_update
        return _user_list_children(current_user), '', no_update, no_update

    # ── Add user ──────────────────────────────────────────────────────────────
    if triggered_id == 'add-user-btn':
        if not email or not password:
            return no_update, _alert('danger', 'Email and password are required.'), \
                   no_update, no_update
        if len(password) < 8:
            return no_update, _alert('danger', 'Password must be at least 8 characters.'), \
                   no_update, no_update
        if crud.get_user_by_email(email.lower().strip()):
            return no_update, _alert('danger', f'{email} already has an account.'), \
                   no_update, no_update
        try:
            crud.create_user_account(email, password)
            # Automatically add to allowed_emails so the new user can log in
            cfg = load_config()
            allowed = cfg.get('allowed_emails', [])
            if email.lower().strip() not in [e.lower() for e in allowed]:
                allowed.append(email.lower().strip())
                cfg['allowed_emails'] = allowed
                save_config(cfg)
        except Exception as exc:
            return no_update, _alert('danger', f'Error creating user: {exc}'), \
                   no_update, no_update
        return _user_list_children(current_user), \
               _alert('success', f'{email} added successfully.'), '', ''

    return no_update, no_update, no_update, no_update


# ── Helpers ───────────────────────────────────────────────────────────────────

def _user_list_children(current_user):
    """Re-render the user list after an add or remove."""
    all_users = crud.get_all_users()
    if not all_users:
        return html.Div("No users found.", style={'color': '#9ca3af', 'fontSize': '13px'})

    rows = []
    for u in all_users:
        is_self = current_user.is_authenticated and u['user_id'] == current_user.id
        rows.append(html.Div(
            style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between',
                   'padding': '10px 0', 'borderBottom': '1px solid #f3f4f6'},
            children=[
                html.Div([
                    html.Span(u['email'], style={'fontWeight': '600', 'color': '#1a1a2e'}),
                    html.Span(' (you)' if is_self else '',
                              style={'color': '#9ca3af', 'fontSize': '12px', 'marginLeft': '6px'}),
                    html.Div(f"Added {u['created_at'][:10]}",
                             style={'fontSize': '11.5px', 'color': '#9ca3af', 'marginTop': '2px'}),
                ]),
                html.Button(
                    [html.I(className='bi bi-trash me-1'), "Remove"],
                    id={'type': 'remove-user-btn', 'index': u['user_id']},
                    className='btn-danger btn-sm',
                    disabled=is_self,
                    title="You cannot remove your own account" if is_self else "Remove this user",
                )
            ]
        ))
    return rows


def _alert(kind, msg):
    cls = 'success' if kind == 'success' else 'danger'
    return html.Div(className=f'alert-banner {cls}', children=msg)
