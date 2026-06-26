"""
pages/followups.py — Dedicated follow-ups view for EtherealCRM.
Displays overdue, due-today, and due-soon deals with snooze and mark-contacted actions.
"""

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
from db import crud
from components.skeletons import empty_state
import yaml
import os
from datetime import date, timedelta
import flask_login

dash.register_page(__name__, path='/followups')

def load_config() -> dict:
    CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

# ── Page Layout ───────────────────────────────────────────────────────────────

def layout():
    cfg = load_config()
    warning_days = cfg.get('follow_up_warning_days', 3)
    deals = crud.get_followup_deals(warning_days)
    currency = cfg.get('currency_symbol', '$')
    
    # Render the list
    rows = []
    if not deals:
        rows = html.Div(
            className='empty-state',
            children=[
                html.Div(html.I(className='bi bi-check2-all',
                                style={'fontSize': '40px', 'color': '#22c55e'}),
                         className='empty-state-icon'),
                html.Div("You're all caught up!", className='empty-state-title'),
                html.Div("No deals require follow-up within your warning window. Time to prospect.",
                         className='empty-state-text'),
                dcc.Link([html.I(className='bi bi-funnel me-2'), "View Pipeline"],
                         href='/pipeline', className='btn btn-secondary mt-3',
                         style={'display': 'inline-flex', 'alignItems': 'center'})
            ]
        )
    else:
        for d in deals:
            badge_class = f"urgency-badge {d['urgency']}"
            badge_text = d['urgency'].replace('-', ' ').upper()
            
            rows.append(
                html.Div(
                    className=f"followup-row {d['urgency']}",
                    children=[
                        # Column 1: Deal name & contact
                        html.Div([
                            dcc.Link(
                                d['deal_name'], 
                                href=f"/pipeline?deal_id={d['deal_id']}", 
                                className='followup-deal-name',
                                style={'color': 'var(--color-primary)'}
                            ),
                            html.Div(
                                [
                                    dcc.Link(f"{d['first_name']} {d['last_name']}", href=f"/contacts?contact_id={d['contact_id']}", style={'textDecoration': 'underline'}),
                                    html.Span(f" ({d['company'] or 'No Company'})")
                                ], 
                                className='followup-contact'
                            )
                        ]),
                        # Column 2: Urgency badge
                        html.Div(html.Span(badge_text, className=badge_class)),
                        # Column 3: Value
                        html.Div(f"{currency}{d['value']:,.2f}" if d['value'] else '—', style={'fontWeight': '700'}),
                        # Column 4: Date due
                        html.Div([
                            html.Div(f"Due: {d['next_follow_up']}", style={'fontWeight': '600'}),
                            html.Div(f"Stage: {d['stage']}", style={'fontSize': '11.5px', 'color': '#6b7280'})
                        ]),
                        # Column 5: Action buttons
                        html.Div([
                            html.Button(
                                [html.I(className='bi bi-clock me-1'), "Snooze"],
                                id={'type': 'snooze-btn', 'index': d['deal_id']},
                                className='btn-secondary btn-sm me-2'
                            ),
                            html.Button(
                                [html.I(className='bi bi-telephone-fill me-1'), "Mark Contacted"],
                                id={'type': 'contacted-btn', 'index': d['deal_id']},
                                className='btn-primary btn-sm'
                            )
                        ], style={'display': 'flex', 'alignItems': 'center'})
                    ],
                    style={'marginBottom': '12px'}
                )
            )

    return html.Div([
        dcc.Store(id='followups-refresh-trigger', data=0),
        
        # Mark Contacted Modal
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Mark Deal as Contacted"), close_button=True),
            dbc.ModalBody([
                dcc.Store(id='contacted-deal-id-store'),
                html.Div([
                    html.Label("Contact Method", className='form-label'),
                    dcc.Dropdown(
                        id='c-method',
                        options=[
                            {'label': 'Outbound Call', 'value': 'Call'},
                            {'label': 'Email Sent', 'value': 'Email'},
                            {'label': 'Meeting Held', 'value': 'Meeting'}
                        ],
                        value='Call',
                        clearable=False,
                        className='mb-3'
                    ),
                ]),
                html.Div([
                    html.Label("Conversation Notes / Summary", className='form-label'),
                    dcc.Textarea(
                        id='c-notes',
                        placeholder='Summarize the discussion and next steps...',
                        style={
                            'width': '100%', 'height': '100px', 'border': '1px solid #d0d5dd',
                            'borderRadius': '6px', 'padding': '8px 12px', 'fontSize': '13px',
                            'fontFamily': 'Inter, sans-serif'
                        },
                        className='mb-3'
                    )
                ]),
                html.Div([
                    html.Label("Schedule Next Follow-Up Date", className='form-label'),
                    html.Br(),
                    dcc.DatePickerSingle(
                        id='c-next-date',
                        display_format='YYYY-MM-DD',
                        date=(date.today() + timedelta(days=warning_days)).isoformat(),
                        style={'width': '100%'}
                    )
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button("Cancel", id='contacted-cancel-btn', color="secondary", outline=True, className="me-2", size="sm"),
                dbc.Button("Log Contacted & Save", id='contacted-save-btn', size="sm",
                           style={'background': 'var(--color-primary)', 'border': 'none', 'fontWeight': '600'})
            ])
        ], id='contacted-modal', is_open=False, centered=True),

        html.Div(
            className='page-header',
            children=[
                html.Div([
                    html.H1("Pending Follow-Ups", className='page-title'),
                    html.P("Deals requiring prompt contact or follow-up schedules.", className='page-subtitle'),
                ])
            ]
        ),

        html.Div(rows, id='followups-list-container')
    ])


# ── Callbacks ─────────────────────────────────────────────────────────────────

# Callback to render the list of followups and handle snooze/log refresh
@callback(
    Output('followups-list-container', 'children'),
    Input('followups-refresh-trigger', 'data'),
    prevent_initial_call=False
)
def refresh_followups_list(refresh):
    cfg = load_config()
    warning_days = cfg.get('follow_up_warning_days', 3)
    deals = crud.get_followup_deals(warning_days)
    currency = cfg.get('currency_symbol', '$')
    
    rows = []
    if not deals:
        return html.Div(
            className='empty-state',
            children=[
                html.Div(html.I(className='bi bi-check2-all',
                                style={'fontSize': '40px', 'color': '#22c55e'}),
                         className='empty-state-icon'),
                html.Div("You're all caught up!", className='empty-state-title'),
                html.Div("No deals require follow-up within your warning window. Time to prospect.",
                         className='empty-state-text'),
                dcc.Link([html.I(className='bi bi-funnel me-2'), "View Pipeline"],
                         href='/pipeline', className='btn btn-secondary mt-3',
                         style={'display': 'inline-flex', 'alignItems': 'center'})
            ]
        )
        
    for d in deals:
        badge_class = f"urgency-badge {d['urgency']}"
        badge_text = d['urgency'].replace('-', ' ').upper()
        
        rows.append(
            html.Div(
                className=f"followup-row {d['urgency']}",
                children=[
                    html.Div([
                        dcc.Link(
                            d['deal_name'], 
                            href=f"/pipeline?deal_id={d['deal_id']}", 
                            className='followup-deal-name',
                            style={'color': 'var(--color-primary)'}
                        ),
                        html.Div(
                            [
                                dcc.Link(f"{d['first_name']} {d['last_name']}", href=f"/contacts?contact_id={d['contact_id']}", style={'textDecoration': 'underline'}),
                                html.Span(f" ({d['company'] or 'No Company'})")
                            ], 
                            className='followup-contact'
                        )
                    ]),
                    html.Div(html.Span(badge_text, className=badge_class)),
                    html.Div(f"{currency}{d['value']:,.2f}" if d['value'] else '—', style={'fontWeight': '700'}),
                    html.Div([
                        html.Div(f"Due: {d['next_follow_up']}", style={'fontWeight': '600'}),
                        html.Div(f"Stage: {d['stage']}", style={'fontSize': '11.5px', 'color': '#6b7280'})
                    ]),
                    html.Div([
                        html.Button(
                            [html.I(className='bi bi-clock me-1'), "Snooze"],
                            id={'type': 'snooze-btn', 'index': d['deal_id']},
                            className='btn-secondary btn-sm me-2'
                        ),
                        html.Button(
                            [html.I(className='bi bi-telephone-fill me-1'), "Mark Contacted"],
                            id={'type': 'contacted-btn', 'index': d['deal_id']},
                            className='btn-primary btn-sm'
                        )
                    ], style={'display': 'flex', 'alignItems': 'center'})
                ],
                style={'marginBottom': '12px'}
            )
        )
    return rows


# Callback to Snooze follow up schedule directly
@callback(
    Output('followups-refresh-trigger', 'data'),
    Input({'type': 'snooze-btn', 'index': dash.ALL}, 'n_clicks'),
    State('followups-refresh-trigger', 'data'),
    prevent_initial_call=True
)
def handle_snooze(snooze_clicks, refresh):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update
        
    trigger_id = ctx.triggered[0]['prop_id']
    if 'snooze-btn' in trigger_id:
        import json
        try:
            triggered_dict = json.loads(trigger_id.split('.')[0])
            deal_id = triggered_dict.get('index')
            cfg = load_config()
            warning_days = cfg.get('follow_up_warning_days', 3)
            crud.snooze_deal_followup(deal_id, warning_days)
            return refresh + 1
        except Exception as e:
            print("Error executing snooze action:", e)
            
    return no_update


# Callback to Open Mark Contacted Modal
@callback(
    Output('contacted-modal', 'is_open'),
    Output('contacted-deal-id-store', 'data'),
    Input({'type': 'contacted-btn', 'index': dash.ALL}, 'n_clicks'),
    Input('contacted-cancel-btn', 'n_clicks'),
    Input('contacted-save-btn', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_contacted_modal(contacted_clicks, cancel_clicks, save_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update
        
    trigger_id = ctx.triggered[0]['prop_id']
    
    if 'contacted-cancel-btn' in trigger_id or 'contacted-save-btn' in trigger_id:
        return False, None
        
    if 'contacted-btn' in trigger_id:
        import json
        try:
            triggered_dict = json.loads(trigger_id.split('.')[0])
            deal_id = triggered_dict.get('index')
            return True, deal_id
        except:
            pass
            
    return False, None


# Callback to Save Contacted log note and update follow up schedule
@callback(
    Output('followups-refresh-trigger', 'data', allow_duplicate=True),
    Input('contacted-save-btn', 'n_clicks'),
    State('contacted-deal-id-store', 'data'),
    State('c-method', 'value'),
    State('c-notes', 'value'),
    State('c-next-date', 'date'),
    State('followups-refresh-trigger', 'data'),
    prevent_initial_call=True
)
def save_contacted_log(n_clicks, deal_id, method, notes, next_date, refresh):
    if not n_clicks or not deal_id:
        return no_update
        
    user = flask_login.current_user
    username = user.email.split('@')[0] if user else 'teammate'
    
    deal = crud.get_deal(deal_id)
    if not deal:
        return no_update
        
    # Log Note in Database
    note_body = f"Logged follow-up action: {method}.\nNotes: {notes or 'No details provided.'}"
    crud.create_note({
        'deal_id': deal_id,
        'contact_id': deal['contact_id'],
        'note_type': method,
        'body': note_body,
        'created_by': username
    })
    
    # Update Deal follow up date
    deal['next_follow_up'] = next_date
    crud.update_deal(deal_id, deal, changed_by=username)
    
    return refresh + 1
