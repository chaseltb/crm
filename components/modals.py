"""
components/modals.py — Reusable modal dialogs for create/edit/delete operations.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc


# ── Generic Confirm Modal ─────────────────────────────────────────────────────

def confirm_modal(modal_id: str, title: str, message: str,
                  confirm_btn_id: str, cancel_btn_id: str,
                  danger: bool = True) -> dbc.Modal:
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(title), close_button=True),
        dbc.ModalBody(html.P(message, style={'color': '#374151'})),
        dbc.ModalFooter([
            dbc.Button("Cancel", id=cancel_btn_id, color="secondary", outline=True,
                       className="me-2", size="sm"),
            dbc.Button("Delete", id=confirm_btn_id,
                       color="danger" if danger else "primary", size="sm"),
        ]),
    ], id=modal_id, is_open=False, centered=True)


# ── Note Modal ────────────────────────────────────────────────────────────────

def note_modal(modal_id: str, title_id: str, save_btn_id: str,
               cancel_btn_id: str, note_type_id: str, body_id: str,
               doc_link_id: str, note_id_store: str) -> dbc.Modal:
    note_types = ['Call', 'Email', 'Meeting', 'Internal', 'Document Link']
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(html.Span(id=title_id)), close_button=True),
        dbc.ModalBody([
            dcc.Store(id=note_id_store),
            html.Div([
                html.Label("Note Type", className='form-label'),
                dcc.Dropdown(
                    id=note_type_id,
                    options=[{'label': t, 'value': t} for t in note_types],
                    value='Internal',
                    clearable=False,
                    className='mb-3',
                ),
            ]),
            html.Div([
                html.Label("Body", className='form-label'),
                dcc.Textarea(
                    id=body_id,
                    placeholder='Write your note here...',
                    style={
                        'width': '100%',
                        'height': '120px',
                        'border': '1px solid #d0d5dd',
                        'borderRadius': '6px',
                        'padding': '8px 12px',
                        'fontSize': '13px',
                        'fontFamily': 'Inter, sans-serif',
                        'resize': 'vertical',
                    }
                ),
            ], className='mb-3'),
            html.Div([
                html.Label("Document Link (optional)", className='form-label'),
                dcc.Input(
                    id=doc_link_id,
                    type='url',
                    placeholder='https://drive.google.com/...',
                    style={
                        'width': '100%',
                        'padding': '8px 12px',
                        'border': '1px solid #d0d5dd',
                        'borderRadius': '6px',
                        'fontSize': '13px',
                    }
                ),
            ]),
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id=cancel_btn_id, color="secondary",
                       outline=True, className="me-2", size="sm"),
            dbc.Button("Save Note", id=save_btn_id, size="sm",
                       style={'background': 'var(--color-primary)',
                              'border': 'none', 'fontWeight': '600'}),
        ]),
    ], id=modal_id, is_open=False, centered=True, size="lg")


# ── Contact Modal ─────────────────────────────────────────────────────────────

def contact_modal(modal_id: str, title_id: str, save_btn_id: str,
                  cancel_btn_id: str, contact_id_store: str,
                  lead_sources: list) -> dbc.Modal:
    field = lambda fid, label, typ='text', ph='': html.Div([
        html.Label(label, className='form-label'),
        dcc.Input(id=fid, type=typ, placeholder=ph,
                  style={'width': '100%', 'padding': '8px 12px',
                         'border': '1px solid #d0d5dd', 'borderRadius': '6px',
                         'fontSize': '13px'}),
    ], className='mb-3')

    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(html.Span(id=title_id)), close_button=True),
        dbc.ModalBody([
            dcc.Store(id=contact_id_store),
            html.Div([
                html.Div(field('c-first-name', 'First Name', ph='Jane'), style={'flex': 1}),
                html.Div(field('c-last-name',  'Last Name',  ph='Smith'), style={'flex': 1}),
            ], style={'display': 'flex', 'gap': '16px'}),
            field('c-company', 'Company / Business', ph='Acme Corp'),
            field('c-email', 'Email', typ='email', ph='jane@example.com'),
            html.Div([
                html.Div(field('c-phone', 'Phone', ph='(555) 000-0000'), style={'flex': 1}),
                html.Div([
                    html.Label("Lead Source", className='form-label'),
                    dcc.Dropdown(
                        id='c-source',
                        options=[{'label': s, 'value': s} for s in lead_sources],
                        placeholder='Select source',
                        clearable=False,
                    ),
                ], style={'flex': 1}),
            ], style={'display': 'flex', 'gap': '16px'}),
            html.Div([
                html.Div(field('c-city', 'City', ph='Nashville'), style={'flex': 1}),
                html.Div(field('c-state', 'State', ph='TN'), style={'flex': 1}),
            ], style={'display': 'flex', 'gap': '16px'}),
            field('c-tags', 'Tags (comma-separated)', ph='landscaping, local-seo'),
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id=cancel_btn_id, color="secondary",
                       outline=True, className="me-2", size="sm"),
            dbc.Button("Save Contact", id=save_btn_id, size="sm",
                       style={'background': 'var(--color-primary)',
                              'border': 'none', 'fontWeight': '600'}),
        ]),
    ], id=modal_id, is_open=False, centered=True, size="lg")


# ── Deal Modal ────────────────────────────────────────────────────────────────

def deal_modal(modal_id: str, title_id: str, save_btn_id: str,
               cancel_btn_id: str, deal_id_store: str,
               deal_stages: list, service_types: list,
               contacts: list) -> dbc.Modal:

    contact_options = [
        {'label': f"{c['first_name']} {c['last_name']} — {c.get('company','')}", 'value': c['contact_id']}
        for c in contacts
    ]

    field = lambda fid, label, typ='text', ph='': html.Div([
        html.Label(label, className='form-label'),
        dcc.Input(id=fid, type=typ, placeholder=ph,
                  style={'width': '100%', 'padding': '8px 12px',
                         'border': '1px solid #d0d5dd', 'borderRadius': '6px',
                         'fontSize': '13px'}),
    ], className='mb-3')

    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle(html.Span(id=title_id)), close_button=True),
        dbc.ModalBody([
            dcc.Store(id=deal_id_store),
            field('d-deal-name', 'Deal Name', ph='Acme Corp — Website Redesign'),
            html.Div([
                html.Label("Contact", className='form-label'),
                dcc.Dropdown(
                    id='d-contact-id',
                    options=contact_options,
                    placeholder='Search contacts...',
                    clearable=False,
                    className='mb-3',
                ),
            ]),
            html.Div([
                html.Div([
                    html.Label("Service Type", className='form-label'),
                    dcc.Dropdown(
                        id='d-service-type',
                        options=[{'label': s, 'value': s} for s in service_types],
                        placeholder='Select type',
                        clearable=False,
                    ),
                ], style={'flex': 1}),
                html.Div([
                    html.Label("Stage", className='form-label'),
                    dcc.Dropdown(
                        id='d-stage',
                        options=[{'label': s, 'value': s} for s in deal_stages],
                        value='New Lead',
                        clearable=False,
                    ),
                ], style={'flex': 1}),
            ], style={'display': 'flex', 'gap': '16px'}, className='mb-3'),
            html.Div([
                html.Div(field('d-value', 'Deal Value ($)', typ='number', ph='5000'), style={'flex': 1}),
                html.Div([
                    html.Label("Probability (%)", className='form-label'),
                    dcc.Input(id='d-probability', type='number', min=0, max=100,
                              placeholder='50',
                              style={'width': '100%', 'padding': '8px 12px',
                                     'border': '1px solid #d0d5dd', 'borderRadius': '6px',
                                     'fontSize': '13px'}),
                ], style={'flex': 1}),
            ], style={'display': 'flex', 'gap': '16px'}),
            html.Div([
                html.Div([
                    html.Label("Next Follow-Up", className='form-label'),
                    dcc.DatePickerSingle(
                        id='d-next-follow-up',
                        display_format='YYYY-MM-DD',
                        placeholder='Select date',
                        style={'width': '100%'},
                    ),
                ], style={'flex': 1}),
                html.Div([
                    html.Label("Expected Close Date", className='form-label'),
                    dcc.DatePickerSingle(
                        id='d-close-date',
                        display_format='YYYY-MM-DD',
                        placeholder='Select date',
                        style={'width': '100%'},
                    ),
                ], style={'flex': 1}),
            ], style={'display': 'flex', 'gap': '16px'}, className='mb-3'),
            field('d-assigned-to', 'Assigned To', ph='Team member name'),
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id=cancel_btn_id, color="secondary",
                       outline=True, className="me-2", size="sm"),
            dbc.Button("Save Deal", id=save_btn_id, size="sm",
                       style={'background': 'var(--color-primary)',
                              'border': 'none', 'fontWeight': '600'}),
        ]),
    ], id=modal_id, is_open=False, centered=True, size="xl")
