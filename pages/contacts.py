"""
pages/contacts.py — Contacts management for EtherealCRM.
Handles contact list, search/filter, contact detail view, and CRUD modals.
"""

import dash
from dash import html, dcc, callback, Input, Output, State, no_update, dash_table
import dash_bootstrap_components as dbc
from db import crud
from components.modals import contact_modal, confirm_modal, note_modal
import yaml
import os
from datetime import date
import flask_login

dash.register_page(__name__, path='/contacts')

def load_config() -> dict:
    CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

# ── Page Layout ───────────────────────────────────────────────────────────────

def layout(contact_id=None, **kwargs):
    cfg = load_config()
    lead_sources = cfg.get('lead_sources', [])
    
    # If a specific contact_id is provided, show the Contact Detail View
    if contact_id:
        return render_contact_detail(contact_id, cfg)
        
    # Otherwise, show the Contacts List View
    contacts = crud.get_contacts()
    
    # Pre-calculate open deal count for each contact to show in the table
    table_data = []
    for c in contacts:
        open_deals = crud.get_open_deal_count_for_contact(c['contact_id'])
        c_dict = dict(c)
        c_dict['open_deals'] = open_deals
        c_dict['name'] = f"{c['first_name']} {c['last_name']}"
        table_data.append(c_dict)

    source_options = [{'label': s, 'value': s} for s in lead_sources]

    return html.Div([
        # Stores for modal states
        dcc.Store(id='contact-refresh-trigger', data=0),
        
        # Modals
        contact_modal('contact-crud-modal', 'contact-modal-title', 
                      'contact-save-btn', 'contact-cancel-btn', 
                      'contact-id-store', lead_sources),
        confirm_modal('contact-delete-modal', 'Delete Contact',
                      'Are you sure you want to delete this contact? All associated deals and notes will remain, but the contact will be marked as deleted.',
                      'contact-delete-confirm-btn', 'contact-delete-cancel-btn'),

        html.Div(
            className='page-header',
            children=[
                html.Div([
                    html.H1("Contacts Directory", className='page-title'),
                    html.P("Manage your relationships, prospects, and active clients.", className='page-subtitle'),
                ]),
                html.Button("➕ Add Contact", id='add-contact-btn', className='btn-primary')
            ]
        ),
        
        # Search & Filter Controls
        html.Div(
            className='panel mb-4',
            children=[
                html.Div(
                    className='panel-body',
                    children=[
                        html.Div(
                            className='filter-bar',
                            children=[
                                html.Div(
                                    className='search-input-wrapper',
                                    children=[
                                        dcc.Input(
                                            id='contact-search-input',
                                            type='text',
                                            placeholder='Search by name, company, email, tags...'
                                        )
                                    ],
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
                        )
                    ]
                )
            ]
        ),

        # Contacts Table Panel
        html.Div(
            className='panel',
            children=[
                html.Div(
                    className='panel-body',
                    children=[
                        html.Div(id='contacts-table-container')
                    ]
                )
            ]
        )
    ])


def render_contact_detail(contact_id: str, cfg: dict):
    contact = crud.get_contact(contact_id)
    currency = cfg.get('currency_symbol', '$')
    
    if not contact:
        return html.Div([
            html.Div(
                className='alert-banner danger',
                children="Contact not found or has been deleted."
            ),
            dcc.Link("← Back to Contacts", href='/contacts', className='btn btn-secondary')
        ])

    deals = crud.get_deals_for_contact(contact_id)
    notes = crud.get_notes_for_contact(contact_id)

    # Calculate some stats for the contact
    total_pipeline_val = sum(d['value'] or 0.0 for d in deals if d['stage'] not in ('Won', 'Lost'))
    
    # Detail Info Card
    info_card = html.Div(
        className='panel mb-4',
        children=[
            html.Div(
                className='panel-header',
                children=[
                    html.Div("Contact Profile", className='panel-title'),
                    html.Div([
                        html.Button("✏️ Edit Profile", id='edit-contact-profile-btn', className='btn-secondary btn-sm me-2', 
                                    **{'data-id': contact_id}),
                        html.Button("🗑️ Delete", id='delete-contact-profile-btn', className='btn-danger btn-sm',
                                    **{'data-id': contact_id})
                    ])
                ]
            ),
            html.Div(
                className='panel-body',
                children=[
                    html.H2(f"{contact['first_name']} {contact['last_name']}", className='mb-2', style={'color': '#1a1a2e', 'fontWeight': '700'}),
                    html.Div(f"🏢 {contact['company'] or 'No Company'}", style={'fontSize': '15px', 'fontWeight': '500', 'color': '#4b5563', 'marginBottom': '16px'}),
                    
                    html.Grid([
                        html.Div([
                            html.Div("Email", style={'fontSize': '11px', 'textTransform': 'uppercase', 'color': '#8890a0', 'fontWeight': '600'}),
                            html.Div(contact['email'] or '—', style={'fontSize': '13.5px', 'fontWeight': '500'}),
                        ], className='col-6 mb-3'),
                        html.Div([
                            html.Div("Phone", style={'fontSize': '11px', 'textTransform': 'uppercase', 'color': '#8890a0', 'fontWeight': '600'}),
                            html.Div(contact['phone'] or '—', style={'fontSize': '13.5px', 'fontWeight': '500'}),
                        ], className='col-6 mb-3'),
                        html.Div([
                            html.Div("Location", style={'fontSize': '11px', 'textTransform': 'uppercase', 'color': '#8890a0', 'fontWeight': '600'}),
                            html.Div(f"{contact['city'] or '—'}{', ' + contact['state'] if contact['state'] else ''}", style={'fontSize': '13.5px', 'fontWeight': '500'}),
                        ], className='col-6 mb-3'),
                        html.Div([
                            html.Div("Lead Source", style={'fontSize': '11px', 'textTransform': 'uppercase', 'color': '#8890a0', 'fontWeight': '600'}),
                            html.Span(contact['source'] or 'Other', className='tag', style={'background': '#fee2e2', 'color': 'var(--color-primary)', 'margin': '4px 0 0'}),
                        ], className='col-6 mb-3'),
                    ], style={'display': 'flex', 'flexWrap': 'wrap'}),
                    
                    html.Div([
                        html.Div("Tags", style={'fontSize': '11px', 'textTransform': 'uppercase', 'color': '#8890a0', 'fontWeight': '600', 'marginBottom': '6px'}),
                        html.Div([html.Span(t.strip(), className='tag') for t in contact['tags'].split(',') if t.strip()] if contact['tags'] else html.Span('No tags', style={'color': '#9ca3af', 'fontSize': '12.5px'}))
                    ], className='mt-2')
                ]
            )
        ]
    )

    # Linked Deals Table
    deal_rows = []
    if not deals:
        deal_rows = html.Div(
            className='empty-state',
            children=[
                html.Div("💼", className='empty-state-icon'),
                html.Div("No Deals Linked", className='empty-state-title'),
                html.Div("Create a deal for this contact to start tracking revenue.", className='empty-state-text')
            ]
        )
    else:
        deal_rows = html.Table(
            className='table table-hover align-middle',
            children=[
                html.Thead(
                    html.Tr([
                        html.Th("Deal Name"),
                        html.Th("Service Type"),
                        html.Th("Stage"),
                        html.Th("Value"),
                        html.Th("Next Follow-Up"),
                    ])
                ),
                html.Tbody([
                    html.Tr([
                        html.Td(dcc.Link(d['deal_name'], href=f"/pipeline?deal_id={d['deal_id']}", style={'color': 'var(--color-primary)', 'fontWeight': '600'})),
                        html.Td(d['service_type'] or '—'),
                        html.Td(html.Span(d['stage'], className=f"stage-badge {d['stage'].lower().replace(' ', '-')}")),
                        html.Td(f"{currency}{d['value']:,.2f}" if d['value'] else '—'),
                        html.Td(d['next_follow_up'] or '—', className='text-danger font-weight-bold' if d['next_follow_up'] and d['next_follow_up'] <= date.today().isoformat() else ''),
                    ]) for d in deals
                ])
            ],
            style={'width': '100%', 'marginTop': '10px'}
        )

    deals_panel = html.Div(
        className='panel mb-4',
        children=[
            html.Div(
                className='panel-header',
                children=[
                    html.Div(f"Linked Deals ({len(deals)})", className='panel-title'),
                    dcc.Link("➕ Create Deal", href=f"/pipeline?new_deal=1&contact_id={contact_id}", className='btn btn-primary btn-sm')
                ]
            ),
            html.Div(
                className='panel-body',
                children=[deal_rows]
            )
        ]
    )

    # Associated Notes Timeline
    note_items = []
    if not notes:
        note_items = html.Div(
            className='empty-state',
            children=[
                html.Div("📝", className='empty-state-icon'),
                html.Div("No Notes Logged", className='empty-state-title'),
                html.Div("Log follow-ups, calls, emails, or store file links here.", className='empty-state-text')
            ]
        )
    else:
        for n in notes:
            action_buttons = html.Div([
                html.Button("✏️", id={'type': 'edit-note-btn', 'index': n['note_id']}, className='btn-icon btn-sm me-1', title='Edit Note'),
                html.Button("🗑️", id={'type': 'delete-note-btn', 'index': n['note_id']}, className='btn-icon btn-sm text-danger', title='Delete Note')
            ], style={'display': 'flex'})
            
            doc_section = None
            if n['doc_link']:
                doc_section = html.Div(
                    className='note-doc-link',
                    children=[
                        html.Span("📎 Document Link: "),
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
                                html.Span(f"by {n['created_by']} on {n['created_at']}", className='note-meta')
                            ]),
                            action_buttons
                        ], className='note-header', style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}),
                        
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
                    html.Button("📝 Add Note", id='add-contact-note-btn', className='btn-primary btn-sm')
                ]
            ),
            html.Div(
                className='panel-body',
                children=[html.Div(note_items, className='notes-timeline')]
            )
        ]
    )

    return html.Div([
        # Modals for Contact Detail operations
        contact_modal('contact-crud-modal', 'contact-modal-title', 
                      'contact-save-btn', 'contact-cancel-btn', 
                      'contact-id-store', cfg.get('lead_sources', [])),
                      
        confirm_modal('contact-delete-modal', 'Delete Contact',
                      'Are you sure you want to delete this contact? All associated deals and notes will remain, but the contact will be marked as deleted.',
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
            children=[
                html.Div([
                    dcc.Link("⬅ Back to Contacts", href='/contacts', className='btn btn-secondary btn-sm mb-3'),
                    html.H1("Contact Details", className='page-title'),
                ])
            ]
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


# ── Callbacks ─────────────────────────────────────────────────────────────────

# Callback to render the contacts list table dynamically based on search & filter
@callback(
    Output('contacts-table-container', 'children'),
    Input('contact-search-input', 'value'),
    Input('contact-filter-source', 'value'),
    Input('contact-refresh-trigger', 'data'),
    prevent_initial_call=False
)
def update_contacts_table(search_val, source_val, refresh):
    contacts = crud.get_contacts()
    
    # Filter
    filtered = []
    for c in contacts:
        # Source filter
        if source_val and c['source'] != source_val:
            continue
            
        # Search filter
        if search_val:
            s_lower = search_val.lower()
            tags_str = c['tags'].lower() if c['tags'] else ''
            name_str = f"{c['first_name']} {c['last_name']}".lower()
            company_str = c['company'].lower() if c['company'] else ''
            email_str = c['email'].lower() if c['email'] else ''
            
            if (s_lower not in name_str and 
                s_lower not in company_str and 
                s_lower not in email_str and 
                s_lower not in tags_str):
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
            'created_at': c['created_at']
        })
        
    if not filtered:
        return html.Div(
            className='empty-state',
            children=[
                html.Div("👥", className='empty-state-icon'),
                html.Div("No Contacts Found", className='empty-state-title'),
                html.Div("Try adjusting your filters or search term.", className='empty-state-text')
            ]
        )
        
    # Render table
    return html.Table(
        className='table table-hover align-middle',
        children=[
            html.Thead(
                html.Tr([
                    html.Th("Name"),
                    html.Th("Company"),
                    html.Th("Email"),
                    html.Th("Phone"),
                    html.Th("Source"),
                    html.Th("Active Deals"),
                    html.Th("Action", style={'textAlign': 'right'}),
                ])
            ),
            html.Tbody([
                html.Tr([
                    html.Td(dcc.Link(c['name'], href=f"/contacts?contact_id={c['contact_id']}", style={'color': 'var(--color-primary)', 'fontWeight': '600'})),
                    html.Td(c['company']),
                    html.Td(c['email']),
                    html.Td(c['phone']),
                    html.Td(html.Span(c['source'], className='tag', style={'background': '#fee2e2', 'color': 'var(--color-primary)'})),
                    html.Td(html.Span(f"{c['open_deals']} Open", style={'fontWeight': 'bold', 'color': '#059669' if c['open_deals'] > 0 else '#6b7280'})),
                    html.Td(
                        html.Div([
                            html.Button("✏️ Edit", id={'type': 'edit-contact-btn', 'index': c['contact_id']}, className='btn-secondary btn-sm me-2'),
                            html.Button("🗑️ Delete", id={'type': 'delete-contact-btn', 'index': c['contact_id']}, className='btn-danger btn-sm')
                        ], style={'display': 'flex', 'justifyContent': 'flex-end'}),
                    )
                ]) for c in filtered
            ])
        ],
        style={'width': '100%'}
    )


# Callback to handle CRUD Modal display and form population for Contacts
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
    Input('edit-contact-profile-btn', 'n_clicks'),
    Input({'type': 'edit-contact-btn', 'index': dash.ALL}, 'n_clicks'),
    Input('contact-cancel-btn', 'n_clicks'),
    State({'type': 'edit-contact-btn', 'index': dash.ALL}, 'id'),
    State('contact-crud-modal', 'is_open'),
    prevent_initial_call=True
)
def toggle_contact_modal(add_clicks, edit_profile_clicks, edit_clicks, cancel_clicks, edit_ids, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update
        
    trigger_id = ctx.triggered[0]['prop_id']
    
    if 'contact-cancel-btn' in trigger_id:
        return False, no_update, no_update, *[None]*9

    # Add Contact
    if 'add-contact-btn' in trigger_id:
        return True, "➕ Add New Contact", None, *[None]*9

    # Edit Contact Profile
    if 'edit-contact-profile-btn' in trigger_id and edit_profile_clicks:
        # Get contact_id from context state
        # The edit-contact-profile-btn has data-id attribute, but in Dash we can parse it from URL or trigger
        # Actually, let's extract contact_id from current url parameter inside callback
        # To do this safely, we can query it using active page contact_id
        # Let's get it from the URL pathname or state. Since we are inside render_contact_detail, 
        # we can pass contact_id or grab it. Wait, how do we pass it? 
        # Let's check the button ID. Let's make the edit button have a dict ID or we can parse contact_id from referer or State.
        # Wait, a cleaner way is to make 'edit-contact-profile-btn' have a dict ID too!
        # E.g. id={'type': 'edit-contact-profile-btn', 'index': contact_id}
        # Let's do that or search for detail button triggers. Let's look at the trigger:
        pass

    # If dict ID was triggered
    # Let's handle dict ID edit triggers
    contact_id = None
    if 'index' in trigger_id:
        # Parse the JSON string of the triggered ID
        import json
        try:
            triggered_dict = json.loads(trigger_id.split('.')[0])
            contact_id = triggered_dict.get('index')
        except:
            pass

    if 'edit-contact-profile-btn' in trigger_id:
        # For the profile edit button, let's look up using the URL or state
        # A simpler way is to query contact_id from the detail page URL.
        # We can pass the pathname or query string using dcc.Location.
        # Let's add State('url', 'search') to this callback!
        # But we must be careful with state counts. Let's inspect trigger_id details:
        pass

    # To be extremely clean, let's re-run or get contact_id:
    # If the user clicked "Edit Profile" button, we can get the contact_id. Let's look at the triggers.
    # Wait, in render_contact_detail we assigned `edit-contact-profile-btn` an id of 'edit-contact-profile-btn'.
    # If we change it to type-index dict ID, it matches the edit-contact-btn callbacks perfectly!
    # Let's define the profile edit button with: id={'type': 'edit-contact-btn', 'index': contact_id}
    # And delete button with: id={'type': 'delete-contact-btn', 'index': contact_id}
    # This solves the problem perfectly with no extra logic!
    # Let's verify: Yes! If we use dict IDs, then the dash.ALL inputs will catch both the list page buttons and the detail page buttons!
    # Let's check if the trigger is 'edit-contact-btn':
    if 'edit-contact-btn' in trigger_id:
        # find the index
        import json
        try:
            triggered_dict = json.loads(trigger_id.split('.')[0])
            contact_id = triggered_dict.get('index')
        except:
            return no_update
            
        c = crud.get_contact(contact_id)
        if c:
            return (True, f"✏️ Edit {c['first_name']} {c['last_name']}", contact_id,
                    c['first_name'], c['last_name'], c['company'], c['email'],
                    c['phone'], c['source'], c['city'], c['state'], c['tags'])

    return False, no_update, no_update, *[None]*9


# Callback to Save Contact (Create or Update)
@callback(
    Output('contact-refresh-trigger', 'data'),
    Output('url', 'href'), # If in detail view, we might want to refresh the page to show new details
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
def save_contact(n_clicks, contact_id, first_name, last_name, company, email, phone, source, city, state, tags, refresh_val, pathname, search_val):
    if not n_clicks:
        return no_update
        
    if not first_name or not last_name:
        return no_update # Basic validation
        
    data = {
        'first_name': first_name,
        'last_name': last_name,
        'company': company,
        'email': email,
        'phone': phone,
        'source': source,
        'city': city,
        'state': state,
        'tags': tags
    }
    
    if contact_id:
        crud.update_contact(contact_id, data)
        # If we are on the contact detail page, reload the page to show updated profile
        if 'contact_id=' in search_val:
            return refresh_val + 1, f"{pathname}{search_val}"
    else:
        crud.create_contact(data)
        
    return refresh_val + 1, no_update


# Callback to handle delete confirmation dialog
@callback(
    Output('contact-delete-modal', 'is_open'),
    Output('contact-delete-confirm-btn', 'style'), # Can store the ID to delete as metadata
    Input({'type': 'delete-contact-btn', 'index': dash.ALL}, 'n_clicks'),
    Input('contact-delete-confirm-btn', 'n_clicks'),
    Input('contact-delete-cancel-btn', 'n_clicks'),
    State('contact-delete-modal', 'is_open'),
    prevent_initial_call=True
)
def toggle_delete_modal(delete_clicks, confirm_clicks, cancel_clicks, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update
        
    trigger_id = ctx.triggered[0]['prop_id']
    
    if 'contact-delete-cancel-btn' in trigger_id:
        return False, no_update
        
    if 'delete-contact-btn' in trigger_id:
        # Find which index clicked delete
        import json
        try:
            triggered_dict = json.loads(trigger_id.split('.')[0])
            contact_id = triggered_dict.get('index')
            # Store contact_id inside button style/custom data for access in confirm trigger
            return True, {'display': 'inline-block', 'data-id': contact_id}
        except Exception as e:
            print("Error parsing delete ID:", e)
            
    if 'contact-delete-confirm-btn' in trigger_id:
        # We need to perform the deletion
        return False, no_update
        
    return no_update


# Callback to perform actual delete
@callback(
    Output('url', 'pathname', allow_duplicate=True),
    Input('contact-delete-confirm-btn', 'n_clicks'),
    State('contact-delete-confirm-btn', 'style'),
    State('url', 'pathname'),
    prevent_initial_call=True
)
def delete_contact_action(n_clicks, btn_style, pathname):
    if not n_clicks or not btn_style or 'data-id' not in btn_style:
        return no_update
        
    contact_id = btn_style['data-id']
    crud.soft_delete_contact(contact_id)
    
    # If we delete from the detail view, redirect to main contacts list
    return '/contacts'


# ── Note Callbacks (detail view only) ─────────────────────────────────────────

# Add or Edit Note Modal Toggle
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
        return no_update
        
    trigger_id = ctx.triggered[0]['prop_id']
    
    if 'contact-note-cancel-btn' in trigger_id:
        return False, no_update, no_update, 'Internal', '', ''
        
    if 'add-contact-note-btn' in trigger_id:
        return True, "📝 Add Activity Note", None, 'Internal', '', ''
        
    if 'edit-note-btn' in trigger_id:
        import json
        try:
            triggered_dict = json.loads(trigger_id.split('.')[0])
            note_id = triggered_dict.get('index')
            n = crud.get_note(note_id)
            if n:
                return True, "✏️ Edit Note", note_id, n['note_type'], n['body'], n['doc_link']
        except Exception as e:
            print("Error parsing edit note ID:", e)
            
    return False, no_update, no_update, 'Internal', '', ''


# Save Note (Create or Update)
@callback(
    Output('url', 'search', allow_duplicate=True), # Reload the detail page by updating search parameter
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
        return no_update
        
    # Get contact_id from search query (e.g. ?contact_id=UUID)
    contact_id = None
    if search and 'contact_id=' in search:
        contact_id = search.split('contact_id=')[1].split('&')[0]
        
    user = flask_login.current_user
    username = user.email.split('@')[0] if user else 'teammate'

    # If note type is Document Link, set body or validation accordingly
    if note_type == 'Document Link' and not doc_link:
        # Validation fallback
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
        
    return search


# Delete Note Confirmation
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
        return no_update
        
    trigger_id = ctx.triggered[0]['prop_id']
    
    if 'contact-note-delete-cancel-btn' in trigger_id:
        return False, no_update
        
    if 'delete-note-btn' in trigger_id:
        import json
        try:
            triggered_dict = json.loads(trigger_id.split('.')[0])
            note_id = triggered_dict.get('index')
            return True, {'display': 'inline-block', 'data-id': note_id}
        except:
            pass
            
    if 'contact-note-delete-confirm-btn' in trigger_id:
        return False, no_update
        
    return no_update


# Delete Note Action
@callback(
    Output('contact-note-delete-confirm-btn', 'className'), # Dummy output to trigger state reload
    Input('contact-note-delete-confirm-btn', 'n_clicks'),
    State('contact-note-delete-confirm-btn', 'style'),
    prevent_initial_call=True
)
def delete_note_action(n_clicks, btn_style):
    if not n_clicks or not btn_style or 'data-id' not in btn_style:
        return no_update
        
    note_id = btn_style['data-id']
    crud.delete_note(note_id)
    return 'btn btn-danger'
