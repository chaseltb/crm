"""
pages/contacts.py — Contacts management for EtherealCRM.
"""

import json
import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
from db import crud
from components.modals import contact_modal, confirm_modal, note_modal
from components.skeletons import skeleton_table, empty_state
from utils.import_contacts import parse_upload, auto_map, df_to_contact_rows, DISPLAY_NAMES
import yaml
import os
from datetime import date
import flask_login

dash.register_page(__name__, path='/contacts')

def load_config() -> dict:
    CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)


def layout(contact_id=None, **kwargs):
    cfg = load_config()
    lead_sources = cfg.get('lead_sources', [])

    if contact_id:
        return render_contact_detail(contact_id, cfg)

    source_options = [{'label': s, 'value': s} for s in lead_sources]

    return html.Div([
        dcc.Store(id='contact-refresh-trigger', data=0),
        dcc.Store(id='import-parsed-store'),

        contact_modal('contact-crud-modal', 'contact-modal-title',
                      'contact-save-btn', 'contact-cancel-btn',
                      'contact-id-store', lead_sources),
        confirm_modal('contact-delete-modal', 'Delete Contact',
                      'Are you sure you want to delete this contact? All associated deals will remain but the contact will be marked as deleted.',
                      'contact-delete-confirm-btn', 'contact-delete-cancel-btn'),
        _import_modal(),

        html.Div(
            className='page-header',
            children=[
                html.Div([
                    html.H1("Contacts Directory", className='page-title'),
                    html.P("Manage your relationships, prospects, and active clients.", className='page-subtitle'),
                ]),
                html.Div([
                    html.Button(
                        [html.I(className='bi bi-file-earmark-arrow-up me-2'), "Import Excel/CSV"],
                        id='open-import-btn', className='btn-secondary me-2'
                    ),
                    html.Button(
                        [html.I(className='bi bi-person-plus-fill me-2'), "Add Contact"],
                        id='add-contact-btn', className='btn-primary'
                    ),
                ], style={'display': 'flex', 'alignItems': 'center'})
            ]
        ),

        html.Div(
            className='panel mb-4',
            children=[html.Div(
                className='panel-body',
                children=[html.Div(
                    className='filter-bar',
                    children=[
                        html.Div(
                            className='search-input-wrapper',
                            children=[dcc.Input(
                                id='contact-search-input',
                                type='text',
                                placeholder='Search by name, company, email, tags...'
                            )],
                            style={'flex': '2', 'minWidth': '250px'}
                        ),
                        html.Div(
                            dcc.Dropdown(
                                id='contact-filter-source',
                                options=source_options,
                                placeholder='Filter by Source',
                                clearable=True,
                            ),
                            style={'flex': '1', 'minWidth': '180px'}
                        )
                    ]
                )]
            )]
        ),

        html.Div(
            className='panel',
            children=[html.Div(className='panel-body', children=[
                html.Div(skeleton_table(rows=6, cols=7), id='contacts-table-container')
            ])]
        )
    ])


def render_contact_detail(contact_id: str, cfg: dict):
    contact = crud.get_contact(contact_id)
    currency = cfg.get('currency_symbol', '$')

    if not contact:
        return html.Div([
            html.Div(className='alert-banner danger', children="Contact not found or has been deleted."),
            dcc.Link([html.I(className='bi bi-arrow-left me-1'), "Back to Contacts"],
                     href='/contacts', className='btn btn-secondary')
        ])

    deals = crud.get_deals_for_contact(contact_id)
    notes = crud.get_notes_for_contact(contact_id)

    info_card = html.Div(
        className='panel mb-4',
        children=[
            html.Div(
                className='panel-header',
                children=[
                    html.Div("Contact Profile", className='panel-title'),
                    html.Div([
                        html.Button(
                            [html.I(className='bi bi-pencil me-1'), "Edit Profile"],
                            id={'type': 'edit-contact-btn', 'index': contact_id},
                            className='btn-secondary btn-sm me-2'
                        ),
                        html.Button(
                            [html.I(className='bi bi-trash me-1'), "Delete"],
                            id={'type': 'delete-contact-btn', 'index': contact_id},
                            className='btn-danger btn-sm'
                        )
                    ])
                ]
            ),
            html.Div(
                className='panel-body',
                children=[
                    html.H2(f"{contact['first_name']} {contact['last_name']}", className='mb-2',
                            style={'color': '#1a1a2e', 'fontWeight': '700'}),
                    html.Div(
                        [html.I(className='bi bi-building me-2'), contact['company'] or 'No Company'],
                        style={'fontSize': '15px', 'fontWeight': '500', 'color': '#4b5563', 'marginBottom': '16px'}
                    ),

                    html.Div(style={'display': 'flex', 'flexWrap': 'wrap'}, children=[
                        html.Div([
                            html.Div("Email", className='detail-label'),
                            html.Div(contact['email'] or '—', className='detail-value'),
                        ], className='col-6 mb-3'),
                        html.Div([
                            html.Div("Phone", className='detail-label'),
                            html.Div(contact['phone'] or '—', className='detail-value'),
                        ], className='col-6 mb-3'),
                        html.Div([
                            html.Div("Location", className='detail-label'),
                            html.Div(
                                f"{contact['city'] or '—'}{', ' + contact['state'] if contact['state'] else ''}",
                                className='detail-value'
                            ),
                        ], className='col-6 mb-3'),
                        html.Div([
                            html.Div("Lead Source", className='detail-label'),
                            html.Span(contact['source'] or 'Other', className='tag source-tag'),
                        ], className='col-6 mb-3'),
                    ]),

                    html.Div([
                        html.Div("Tags", className='detail-label mb-1'),
                        html.Div(
                            [html.Span(t.strip(), className='tag') for t in contact['tags'].split(',') if t.strip()]
                            if contact['tags']
                            else html.Span('No tags', style={'color': '#9ca3af', 'fontSize': '12.5px'})
                        )
                    ], className='mt-2')
                ]
            )
        ]
    )

    if not deals:
        deal_rows = empty_state(
            'bi bi-briefcase text-muted',
            'No deals linked yet',
            'Create a deal to start tracking revenue and move this contact through your pipeline.',
            action_label='Create First Deal',
            action_href=f"/pipeline?new_deal=1&contact_id={contact_id}"
        )
    else:
        deal_rows = html.Table(
            className='table table-hover align-middle',
            children=[
                html.Thead(html.Tr([
                    html.Th("Deal Name"), html.Th("Service"), html.Th("Stage"),
                    html.Th("Value"), html.Th("Next Follow-Up"),
                ])),
                html.Tbody([
                    html.Tr([
                        html.Td(dcc.Link(d['deal_name'], href=f"/pipeline?deal_id={d['deal_id']}",
                                         style={'color': 'var(--color-primary)', 'fontWeight': '600'})),
                        html.Td(d['service_type'] or '—'),
                        html.Td(html.Span(d['stage'], className=f"stage-badge {d['stage'].lower().replace(' ', '-')}")),
                        html.Td(f"{currency}{d['value']:,.2f}" if d['value'] else '—'),
                        html.Td(d['next_follow_up'] or '—',
                                className='text-danger fw-bold'
                                if d['next_follow_up'] and d['next_follow_up'] <= date.today().isoformat() else ''),
                    ]) for d in deals
                ])
            ],
            style={'width': '100%', 'marginTop': '4px'}
        )

    deals_panel = html.Div(
        className='panel mb-4',
        children=[
            html.Div(
                className='panel-header',
                children=[
                    html.Div(f"Linked Deals ({len(deals)})", className='panel-title'),
                    dcc.Link(
                        [html.I(className='bi bi-plus-lg me-1'), "Create Deal"],
                        href=f"/pipeline?new_deal=1&contact_id={contact_id}",
                        className='btn btn-primary btn-sm'
                    )
                ]
            ),
            html.Div(className='panel-body', children=[deal_rows])
        ]
    )

    note_items = []
    if not notes:
        note_items = empty_state(
            'bi bi-journal-text text-muted',
            'No activity logged yet',
            'Log calls, emails, or meetings to keep a full history of this relationship.',
            action_label='Log First Note',
            action_id='add-contact-note-btn'
        )
    else:
        for n in notes:
            action_buttons = html.Div([
                html.Button(html.I(className='bi bi-pencil'),
                            id={'type': 'edit-note-btn', 'index': n['note_id']},
                            className='btn-icon btn-sm me-1', title='Edit Note'),
                html.Button(html.I(className='bi bi-trash'),
                            id={'type': 'delete-note-btn', 'index': n['note_id']},
                            className='btn-icon btn-sm btn-icon-danger', title='Delete Note')
            ], style={'display': 'flex'})

            doc_section = None
            if n['doc_link']:
                doc_section = html.Div(
                    className='note-doc-link',
                    children=[
                        html.I(className='bi bi-paperclip me-1'),
                        html.A(n['doc_link'], href=n['doc_link'], target='_blank')
                    ]
                )

            note_items.append(
                html.Div(
                    className='note-item mb-3',
                    children=[
                        html.Div([
                            html.Div([
                                html.Span(n['note_type'], className='note-type-badge me-2'),
                                html.Span(f"by {n['created_by']} · {n['created_at']}", className='note-meta')
                            ]),
                            action_buttons
                        ], className='note-header'),
                        html.Div(n['body'], className='note-body mt-2'),
                        doc_section
                    ]
                )
            )

    notes_panel = html.Div(
        className='panel',
        children=[
            html.Div(
                className='panel-header',
                children=[
                    html.Div(f"Activity Notes ({len(notes)})", className='panel-title'),
                    html.Button(
                        [html.I(className='bi bi-plus-lg me-1'), "Add Note"],
                        id='add-contact-note-btn', className='btn-primary btn-sm'
                    )
                ]
            ),
            html.Div(className='panel-body', children=[
                html.Div(note_items, className='notes-timeline')
            ])
        ]
    )

    return html.Div([
        contact_modal('contact-crud-modal', 'contact-modal-title',
                      'contact-save-btn', 'contact-cancel-btn',
                      'contact-id-store', cfg.get('lead_sources', [])),
        confirm_modal('contact-delete-modal', 'Delete Contact',
                      'Are you sure you want to delete this contact?',
                      'contact-delete-confirm-btn', 'contact-delete-cancel-btn'),
        note_modal('contact-note-crud-modal', 'contact-note-modal-title',
                   'contact-note-save-btn', 'contact-note-cancel-btn',
                   'contact-n-type', 'contact-n-body', 'contact-n-doc-link', 'contact-note-id-store'),
        confirm_modal('contact-note-delete-modal', 'Delete Note',
                      'Are you sure you want to permanently delete this note?',
                      'contact-note-delete-confirm-btn', 'contact-note-delete-cancel-btn'),

        dcc.Store(id='contact-refresh-trigger', data=0),

        html.Div(
            className='page-header',
            children=[html.Div([
                dcc.Link(
                    [html.I(className='bi bi-arrow-left me-1'), "Back to Contacts"],
                    href='/contacts', className='btn btn-secondary btn-sm mb-3'
                ),
                html.H1("Contact Details", className='page-title'),
            ])]
        ),

        html.Div(
            className='row',
            children=[
                html.Div(info_card, className='col-lg-4 col-12'),
                html.Div([deals_panel, notes_panel], className='col-lg-8 col-12')
            ],
            style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px'}
        )
    ])


# ── Import Modal Builder ──────────────────────────────────────────────────────

def _import_modal():
    return dbc.Modal([
        dbc.ModalHeader(
            dbc.ModalTitle([html.I(className='bi bi-file-earmark-spreadsheet me-2'), "Import Contacts"]),
            close_button=True
        ),
        dbc.ModalBody([
            # Step 1 — upload zone
            html.Div(id='import-step-upload', children=[
                dcc.Upload(
                    id='import-upload',
                    children=html.Div([
                        html.I(className='bi bi-cloud-upload-fill',
                               style={'fontSize': '36px', 'color': '#d0d5dd', 'display': 'block', 'marginBottom': '10px'}),
                        html.Div("Drag & drop your spreadsheet here, or click to browse",
                                 style={'fontWeight': '600', 'color': '#374151'}),
                        html.Div(".xlsx · .xls · .csv supported",
                                 style={'fontSize': '12px', 'color': '#9ca3af', 'marginTop': '4px'}),
                    ], style={'textAlign': 'center', 'padding': '40px 20px'}),
                    style={
                        'border': '2px dashed #d0d5dd', 'borderRadius': '10px',
                        'cursor': 'pointer', 'transition': 'border-color 0.18s',
                    },
                    accept='.csv,.xlsx,.xls',
                    multiple=False,
                ),
                html.Div(id='import-upload-error', className='mt-3'),

                # Column reference
                html.Details([
                    html.Summary("Expected column headers", style={'fontSize': '12px', 'color': '#6b7280',
                                                                    'cursor': 'pointer', 'marginTop': '16px'}),
                    html.Div(
                        [html.Span(v, className='tag me-1 mt-1') for v in [
                            'First Name', 'Last Name', 'Name', 'Company', 'Email',
                            'Phone', 'City', 'State', 'Source', 'Tags'
                        ]],
                        style={'marginTop': '8px', 'flexWrap': 'wrap', 'display': 'flex'}
                    ),
                    html.Div("Column names are matched case-insensitively. A 'Name' column is split into first/last.",
                             style={'fontSize': '11px', 'color': '#9ca3af', 'marginTop': '6px'})
                ])
            ]),

            # Step 2 — preview (hidden until file uploaded)
            html.Div(id='import-step-preview', style={'display': 'none'}, children=[
                html.Div(id='import-preview-content')
            ]),
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id='import-cancel-btn', color='secondary',
                       outline=True, size='sm', className='me-2'),
            dbc.Button(
                [html.I(className='bi bi-check-lg me-1'), html.Span(id='import-confirm-label', children='Import')],
                id='import-confirm-btn', size='sm', disabled=True,
                style={'background': 'var(--color-primary)', 'border': 'none', 'fontWeight': '600'}
            ),
        ])
    ], id='import-modal', is_open=False, centered=True, size='xl')


# ── Callbacks ─────────────────────────────────────────────────────────────────

@callback(
    Output('import-modal', 'is_open'),
    Input('open-import-btn', 'n_clicks'),
    Input('import-cancel-btn', 'n_clicks'),
    Input('import-confirm-btn', 'n_clicks'),
    State('import-modal', 'is_open'),
    prevent_initial_call=True
)
def toggle_import_modal(open_clicks, cancel_clicks, confirm_clicks, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update
    trigger = ctx.triggered[0]['prop_id']
    if 'open-import-btn' in trigger:
        return True
    return False


@callback(
    Output('import-parsed-store', 'data'),
    Output('import-step-upload', 'style'),
    Output('import-step-preview', 'style'),
    Output('import-preview-content', 'children'),
    Output('import-confirm-btn', 'disabled'),
    Output('import-confirm-label', 'children'),
    Output('import-upload-error', 'children'),
    Input('import-upload', 'contents'),
    State('import-upload', 'filename'),
    prevent_initial_call=True
)
def parse_import_file(contents, filename):
    if not contents:
        return no_update, no_update, no_update, no_update, True, 'Import', no_update

    try:
        df = parse_upload(contents, filename)
        mapping = auto_map(list(df.columns))
        rows = df_to_contact_rows(df, mapping)

        if not rows:
            raise ValueError("No importable rows found. Check that your file has name columns.")

        # Build mapped-fields chips
        mapped_chips = []
        for field, col in mapping.items():
            if field == 'full_name':
                label = f"Name → First + Last"
            else:
                label = f"{DISPLAY_NAMES.get(field, field)} ← '{col}'"
            mapped_chips.append(html.Span(label, className='import-field-chip me-1 mb-1'))

        # Preview table (first 5 rows)
        preview_rows = rows[:5]
        preview_cols = ['first_name', 'last_name', 'company', 'email', 'phone', 'source']
        preview_headers = ['First', 'Last', 'Company', 'Email', 'Phone', 'Source']

        preview_table = html.Table(
            className='table',
            style={'fontSize': '12px', 'marginTop': '12px'},
            children=[
                html.Thead(html.Tr([html.Th(h) for h in preview_headers])),
                html.Tbody([
                    html.Tr([html.Td(r.get(c, '') or '—') for c in preview_cols])
                    for r in preview_rows
                ])
            ]
        )

        skipped = len(df) - len(rows)
        skip_note = (html.Div(f"{skipped} row(s) skipped — missing name.",
                              style={'fontSize': '11px', 'color': '#9ca3af', 'marginTop': '4px'})
                     if skipped else None)

        preview_content = html.Div([
            html.Div([
                html.I(className='bi bi-check-circle-fill me-2', style={'color': '#22c55e'}),
                html.Strong(f"{len(rows)} contacts ready to import"),
                html.Span(f" from {filename}", style={'color': '#6b7280', 'fontSize': '13px'}),
            ], style={'marginBottom': '10px'}),
            html.Div("Detected columns:", style={'fontSize': '12px', 'fontWeight': '600',
                                                  'color': '#374151', 'marginBottom': '6px'}),
            html.Div(mapped_chips, style={'display': 'flex', 'flexWrap': 'wrap', 'marginBottom': '4px'}),
            skip_note,
            html.Div(f"Preview (first {min(5, len(rows))} of {len(rows)}):",
                     style={'fontSize': '12px', 'fontWeight': '600', 'color': '#374151',
                             'marginTop': '14px', 'marginBottom': '4px'}),
            html.Div(preview_table, style={'overflowX': 'auto'}),
            html.Button(
                [html.I(className='bi bi-arrow-left me-1'), "Upload a different file"],
                id='import-reset-btn',
                className='btn-secondary btn-sm mt-3',
                style={'fontSize': '12px'}
            ),
        ])

        label = f"Import {len(rows)} Contact{'s' if len(rows) != 1 else ''}"
        stored = [r for r in rows]  # plain list of dicts — JSON-serialisable

        return (stored,
                {'display': 'none'}, {'display': 'block'},
                preview_content, False, label, '')

    except Exception as e:
        err = html.Div(
            [html.I(className='bi bi-exclamation-circle me-2'), str(e)],
            className='alert-banner danger'
        )
        return None, {'display': 'block'}, {'display': 'none'}, '', True, 'Import', err


@callback(
    Output('import-step-upload', 'style', allow_duplicate=True),
    Output('import-step-preview', 'style', allow_duplicate=True),
    Output('import-parsed-store', 'data', allow_duplicate=True),
    Output('import-confirm-btn', 'disabled', allow_duplicate=True),
    Output('import-confirm-label', 'children', allow_duplicate=True),
    Output('import-upload-error', 'children', allow_duplicate=True),
    Input('import-reset-btn', 'n_clicks'),
    prevent_initial_call=True
)
def reset_import(_):
    return {'display': 'block'}, {'display': 'none'}, None, True, 'Import', ''


@callback(
    Output('contact-refresh-trigger', 'data', allow_duplicate=True),
    Output('import-modal', 'is_open', allow_duplicate=True),
    Input('import-confirm-btn', 'n_clicks'),
    State('import-parsed-store', 'data'),
    State('contact-refresh-trigger', 'data'),
    prevent_initial_call=True
)
def confirm_import(n_clicks, rows, refresh):
    if not n_clicks or not rows:
        return no_update, no_update
    inserted = crud.bulk_create_contacts(rows)
    return refresh + 1, False


@callback(
    Output('contacts-table-container', 'children'),
    Input('contact-search-input', 'value'),
    Input('contact-filter-source', 'value'),
    Input('contact-refresh-trigger', 'data'),
    prevent_initial_call=False
)
def update_contacts_table(search_val, source_val, refresh):
    contacts = crud.get_contacts()

    filtered = []
    for c in contacts:
        if source_val and c['source'] != source_val:
            continue
        if search_val:
            s_lower = search_val.lower()
            if (s_lower not in f"{c['first_name']} {c['last_name']}".lower() and
                    s_lower not in (c['company'] or '').lower() and
                    s_lower not in (c['email'] or '').lower() and
                    s_lower not in (c['tags'] or '').lower()):
                continue
        open_deals = crud.get_open_deal_count_for_contact(c['contact_id'])
        filtered.append({
            'contact_id': c['contact_id'],
            'name': f"{c['first_name']} {c['last_name']}",
            'company': c['company'] or '—',
            'email': c['email'] or '—',
            'phone': c['phone'] or '—',
            'source': c['source'] or 'Other',
            'open_deals': open_deals,
        })

    if not filtered:
        if search_val or source_val:
            return empty_state(
                'bi bi-search text-muted',
                'No contacts match your filters',
                'Try a different search term or clear the source filter.'
            )
        return empty_state(
            'bi bi-people text-muted',
            'No contacts yet',
            'Start building your network — add your first contact to track deals and activity.',
            action_label='Add Your First Contact',
            action_id='add-contact-btn'
        )

    return html.Table(
        className='table table-hover align-middle',
        children=[
            html.Thead(html.Tr([
                html.Th("Name"), html.Th("Company"), html.Th("Email"),
                html.Th("Phone"), html.Th("Source"), html.Th("Active Deals"),
                html.Th("", style={'textAlign': 'right'}),
            ])),
            html.Tbody([
                html.Tr([
                    html.Td(dcc.Link(c['name'], href=f"/contacts?contact_id={c['contact_id']}",
                                     style={'color': 'var(--color-primary)', 'fontWeight': '600'})),
                    html.Td(c['company']),
                    html.Td(c['email']),
                    html.Td(c['phone']),
                    html.Td(html.Span(c['source'], className='tag source-tag')),
                    html.Td(html.Span(
                        f"{c['open_deals']} Open",
                        style={'fontWeight': '600',
                               'color': '#059669' if c['open_deals'] > 0 else '#9ca3af'}
                    )),
                    html.Td(
                        html.Div([
                            html.Button(
                                [html.I(className='bi bi-pencil me-1'), "Edit"],
                                id={'type': 'edit-contact-btn', 'index': c['contact_id']},
                                className='btn-secondary btn-sm me-2'
                            ),
                            html.Button(
                                html.I(className='bi bi-trash'),
                                id={'type': 'delete-contact-btn', 'index': c['contact_id']},
                                className='btn-icon btn-sm btn-icon-danger'
                            )
                        ], style={'display': 'flex', 'justifyContent': 'flex-end', 'alignItems': 'center'}),
                    )
                ]) for c in filtered
            ])
        ],
        style={'width': '100%'}
    )


@callback(
    Output('contact-crud-modal', 'is_open'),
    Output('contact-modal-title', 'children'),
    Output('contact-id-store', 'data'),
    Output('c-first-name', 'value'),
    Output('c-last-name', 'value'),
    Output('c-company', 'value'),
    Output('c-email', 'value'),
    Output('c-phone', 'value'),
    Output('c-source', 'value'),
    Output('c-city', 'value'),
    Output('c-state', 'value'),
    Output('c-tags', 'value'),
    Input('add-contact-btn', 'n_clicks'),
    Input({'type': 'edit-contact-btn', 'index': dash.ALL}, 'n_clicks'),
    Input('contact-cancel-btn', 'n_clicks'),
    State('contact-crud-modal', 'is_open'),
    prevent_initial_call=True
)
def toggle_contact_modal(add_clicks, edit_clicks, cancel_clicks, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update, no_update, *[no_update]*9

    trigger_id = ctx.triggered[0]['prop_id']

    if 'contact-cancel-btn' in trigger_id:
        return False, no_update, no_update, *[None]*9

    if 'add-contact-btn' in trigger_id:
        return True, [html.I(className='bi bi-person-plus-fill me-2'), "Add New Contact"], None, *[None]*9

    if 'edit-contact-btn' in trigger_id:
        try:
            triggered_dict = json.loads(trigger_id.split('.')[0])
            contact_id = triggered_dict.get('index')
            c = crud.get_contact(contact_id)
            if c:
                return (True,
                        [html.I(className='bi bi-pencil me-2'), f"Edit {c['first_name']} {c['last_name']}"],
                        contact_id,
                        c['first_name'], c['last_name'], c['company'], c['email'],
                        c['phone'], c['source'], c['city'], c['state'], c['tags'])
        except Exception as e:
            print("Error toggling contact modal:", e)

    return no_update, no_update, no_update, *[no_update]*9


@callback(
    Output('contact-refresh-trigger', 'data'),
    Output('url', 'href'),
    Output('contact-crud-modal', 'is_open', allow_duplicate=True),
    Input('contact-save-btn', 'n_clicks'),
    State('contact-id-store', 'data'),
    State('c-first-name', 'value'),
    State('c-last-name', 'value'),
    State('c-company', 'value'),
    State('c-email', 'value'),
    State('c-phone', 'value'),
    State('c-source', 'value'),
    State('c-city', 'value'),
    State('c-state', 'value'),
    State('c-tags', 'value'),
    State('contact-refresh-trigger', 'data'),
    State('url', 'pathname'),
    State('url', 'search'),
    prevent_initial_call=True
)
def save_contact(n_clicks, contact_id, first_name, last_name, company, email,
                 phone, source, city, state, tags, refresh_val, pathname, search_val):
    if not n_clicks or not first_name or not last_name:
        return no_update, no_update, no_update

    data = {
        'first_name': first_name, 'last_name': last_name, 'company': company,
        'email': email, 'phone': phone, 'source': source,
        'city': city, 'state': state, 'tags': tags
    }

    if contact_id:
        crud.update_contact(contact_id, data)
        if search_val and 'contact_id=' in search_val:
            return refresh_val + 1, f"{pathname}{search_val}", False
    else:
        crud.create_contact(data)

    return refresh_val + 1, no_update, False


@callback(
    Output('contact-delete-modal', 'is_open'),
    Output('contact-delete-confirm-btn', 'style'),
    Input({'type': 'delete-contact-btn', 'index': dash.ALL}, 'n_clicks'),
    Input('contact-delete-confirm-btn', 'n_clicks'),
    Input('contact-delete-cancel-btn', 'n_clicks'),
    State('contact-delete-modal', 'is_open'),
    prevent_initial_call=True
)
def toggle_delete_modal(delete_clicks, confirm_clicks, cancel_clicks, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update

    trigger_id = ctx.triggered[0]['prop_id']

    if 'contact-delete-cancel-btn' in trigger_id:
        return False, no_update

    if 'delete-contact-btn' in trigger_id:
        try:
            triggered_dict = json.loads(trigger_id.split('.')[0])
            contact_id = triggered_dict.get('index')
            return True, {'display': 'inline-block', 'data-id': contact_id}
        except Exception as e:
            print("Error parsing delete ID:", e)

    if 'contact-delete-confirm-btn' in trigger_id:
        return False, no_update

    return no_update, no_update


@callback(
    Output('url', 'pathname', allow_duplicate=True),
    Input('contact-delete-confirm-btn', 'n_clicks'),
    State('contact-delete-confirm-btn', 'style'),
    prevent_initial_call=True
)
def delete_contact_action(n_clicks, btn_style):
    if not n_clicks or not btn_style or 'data-id' not in btn_style:
        return no_update
    crud.soft_delete_contact(btn_style['data-id'])
    return '/contacts'


# ── Note Callbacks (detail view only) ─────────────────────────────────────────

@callback(
    Output('contact-note-crud-modal', 'is_open'),
    Output('contact-note-modal-title', 'children'),
    Output('contact-note-id-store', 'data'),
    Output('contact-n-type', 'value'),
    Output('contact-n-body', 'value'),
    Output('contact-n-doc-link', 'value'),
    Input('add-contact-note-btn', 'n_clicks'),
    Input({'type': 'edit-note-btn', 'index': dash.ALL}, 'n_clicks'),
    Input('contact-note-cancel-btn', 'n_clicks'),
    State('contact-note-crud-modal', 'is_open'),
    prevent_initial_call=True
)
def toggle_note_modal(add_clicks, edit_clicks, cancel_clicks, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update, no_update, 'Internal', '', ''

    trigger_id = ctx.triggered[0]['prop_id']

    if 'contact-note-cancel-btn' in trigger_id:
        return False, no_update, no_update, 'Internal', '', ''

    if 'add-contact-note-btn' in trigger_id:
        return True, [html.I(className='bi bi-plus-lg me-2'), "Add Activity Note"], None, 'Internal', '', ''

    if 'edit-note-btn' in trigger_id:
        try:
            triggered_dict = json.loads(trigger_id.split('.')[0])
            note_id = triggered_dict.get('index')
            n = crud.get_note(note_id)
            if n:
                return (True, [html.I(className='bi bi-pencil me-2'), "Edit Note"],
                        note_id, n['note_type'], n['body'], n['doc_link'])
        except Exception as e:
            print("Error parsing edit note ID:", e)

    return False, no_update, no_update, 'Internal', '', ''


@callback(
    Output('url', 'search', allow_duplicate=True),
    Output('contact-note-crud-modal', 'is_open', allow_duplicate=True),
    Input('contact-note-save-btn', 'n_clicks'),
    State('contact-note-id-store', 'data'),
    State('contact-n-type', 'value'),
    State('contact-n-body', 'value'),
    State('contact-n-doc-link', 'value'),
    State('url', 'search'),
    prevent_initial_call=True
)
def save_note(n_clicks, note_id, note_type, body, doc_link, search):
    if not n_clicks or not body:
        return no_update, no_update

    contact_id = None
    if search and 'contact_id=' in search:
        contact_id = search.split('contact_id=')[1].split('&')[0]

    user = flask_login.current_user
    username = user.email.split('@')[0] if user else 'teammate'

    if note_type == 'Document Link' and not doc_link:
        doc_link = body if body.startswith('http') else ''

    data = {
        'contact_id': contact_id,
        'note_type': note_type,
        'body': body,
        'doc_link': doc_link,
        'created_by': username
    }

    if note_id:
        crud.update_note(note_id, data)
    else:
        crud.create_note(data)

    return search, False


@callback(
    Output('contact-note-delete-modal', 'is_open'),
    Output('contact-note-delete-confirm-btn', 'style'),
    Input({'type': 'delete-note-btn', 'index': dash.ALL}, 'n_clicks'),
    Input('contact-note-delete-confirm-btn', 'n_clicks'),
    Input('contact-note-delete-cancel-btn', 'n_clicks'),
    State('contact-note-delete-modal', 'is_open'),
    prevent_initial_call=True
)
def toggle_note_delete_modal(delete_clicks, confirm_clicks, cancel_clicks, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update

    trigger_id = ctx.triggered[0]['prop_id']

    if 'contact-note-delete-cancel-btn' in trigger_id:
        return False, no_update

    if 'delete-note-btn' in trigger_id:
        try:
            triggered_dict = json.loads(trigger_id.split('.')[0])
            note_id = triggered_dict.get('index')
            return True, {'display': 'inline-block', 'data-id': note_id}
        except Exception:
            pass

    if 'contact-note-delete-confirm-btn' in trigger_id:
        return False, no_update

    return no_update, no_update


@callback(
    Output('url', 'search', allow_duplicate=True),
    Input('contact-note-delete-confirm-btn', 'n_clicks'),
    State('contact-note-delete-confirm-btn', 'style'),
    State('url', 'search'),
    prevent_initial_call=True
)
def delete_note_action(n_clicks, btn_style, search):
    if not n_clicks or not btn_style or 'data-id' not in btn_style:
        return no_update
    crud.delete_note(btn_style['data-id'])
    return search
