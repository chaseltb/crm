"""
pages/pipeline.py — Pipeline (Deals) management for EtherealCRM.
"""

import json
import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
from db import crud
from components.modals import deal_modal, confirm_modal, note_modal
from components.skeletons import skeleton_table, skeleton_kanban, empty_state
from utils.config import load_config
from datetime import date
import flask_login

dash.register_page(__name__, path='/pipeline')


def layout(deal_id=None, new_deal=None, contact_id=None, **kwargs):
    cfg = load_config()
    stages = cfg.get('deal_stages', [])
    service_types = cfg.get('service_types', [])
    contacts = crud.get_contacts()

    if deal_id:
        return render_deal_detail(deal_id, cfg)

    return html.Div([
        dcc.Store(id='pipeline-view-store', data='kanban', storage_type='local'),
        dcc.Store(id='pipeline-refresh-trigger', data=0),

        deal_modal('deal-crud-modal', 'deal-modal-title',
                   'deal-save-btn', 'deal-cancel-btn',
                   'deal-id-store', stages, service_types, contacts),
        confirm_modal('deal-delete-modal', 'Delete Deal',
                      'Are you sure you want to delete this deal? The deal will be marked as deleted but history is preserved.',
                      'deal-delete-confirm-btn', 'deal-delete-cancel-btn'),

        html.Div(
            className='page-header',
            children=[
                html.Div([
                    html.H1("Pipeline", className='page-title'),
                    html.P("Track your active deals, estimated revenue, and stages.", className='page-subtitle'),
                ]),
                html.Div([
                    html.Div(
                        className='view-toggle me-3',
                        children=[
                            html.Button(
                                [html.I(className='bi bi-kanban me-1'), "Kanban"],
                                id='view-kanban-btn', className='view-toggle-btn active'
                            ),
                            html.Button(
                                [html.I(className='bi bi-list-ul me-1'), "List"],
                                id='view-list-btn', className='view-toggle-btn'
                            )
                        ],
                        style={'display': 'inline-flex'}
                    ),
                    html.Button(
                        [html.I(className='bi bi-plus-lg me-2'), "New Deal"],
                        id='add-deal-btn', className='btn-primary'
                    )
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
                                id='deal-search-input',
                                type='text',
                                placeholder='Search deals, contacts, companies...'
                            )],
                            style={'flex': '2', 'minWidth': '250px'}
                        ),
                        html.Div(
                            dcc.Dropdown(
                                id='deal-filter-stage',
                                options=[{'label': s, 'value': s} for s in stages],
                                placeholder='Filter by Stage',
                                clearable=True,
                            ),
                            style={'flex': '1', 'minWidth': '180px'}
                        )
                    ]
                )]
            )]
        ),

        html.Div(
            # Generic loading skeleton shown before the view-store is read
            html.Div([
                html.Div(className='skeleton skeleton-text mb-3',
                         style={'height': '18px', 'width': '160px'}),
                skeleton_kanban(cols=5, cards_per_col=2),
            ]),
            id='pipeline-main-container'
        ),

        dcc.Store(id='deal-init-params', data={'new_deal': new_deal, 'contact_id': contact_id})
    ])


def render_deal_detail(deal_id: str, cfg: dict):
    deal = crud.get_deal(deal_id)
    currency = cfg.get('currency_symbol', '$')

    if not deal:
        return html.Div([
            html.Div(className='alert-banner danger', children="Deal not found or has been deleted."),
            dcc.Link([html.I(className='bi bi-arrow-left me-1'), "Back to Pipeline"],
                     href='/pipeline', className='btn btn-secondary')
        ])

    notes = crud.get_notes_for_deal(deal_id)
    history = crud.get_stage_history(deal_id)

    info_card = html.Div(
        className='panel mb-4',
        children=[
            html.Div(
                className='panel-header',
                children=[
                    html.Div("Deal Information", className='panel-title'),
                    html.Div([
                        html.Button(
                            [html.I(className='bi bi-pencil me-1'), "Edit Deal"],
                            id={'type': 'edit-deal-btn', 'index': deal_id},
                            className='btn-secondary btn-sm me-2'
                        ),
                        html.Button(
                            html.I(className='bi bi-trash'),
                            id={'type': 'delete-deal-btn', 'index': deal_id},
                            className='btn-icon btn-sm btn-icon-danger'
                        )
                    ])
                ]
            ),
            html.Div(
                className='panel-body',
                children=[
                    html.H2(deal['deal_name'], className='mb-2',
                            style={'color': '#1a1a2e', 'fontWeight': '700'}),
                    html.Div([
                        html.Span("Stage: ", style={'color': '#6b7280'}),
                        html.Span(deal['stage'],
                                  className=f"stage-badge {deal['stage'].lower().replace(' ', '-')}")
                    ], className='mb-3'),

                    html.Div(style={'display': 'flex', 'flexWrap': 'wrap'}, children=[
                        html.Div([
                            html.Div("Deal Value", className='detail-label'),
                            html.Div(f"{currency}{deal['value']:,.2f}" if deal['value'] else '—',
                                     style={'fontSize': '18px', 'fontWeight': '700',
                                            'color': 'var(--color-primary)'}),
                        ], className='col-6 mb-3'),
                        html.Div([
                            html.Div("Probability", className='detail-label'),
                            html.Div(f"{deal['probability']}%",
                                     style={'fontSize': '15px', 'fontWeight': '600'}),
                        ], className='col-6 mb-3'),
                        html.Div([
                            html.Div("Contact Person", className='detail-label'),
                            dcc.Link(
                                f"{deal['first_name']} {deal['last_name']}",
                                href=f"/contacts?contact_id={deal['contact_id']}",
                                style={'color': 'var(--color-primary)', 'fontWeight': '600',
                                       'textDecoration': 'underline'}
                            ),
                            html.Div(deal['company'], style={'fontSize': '12px', 'color': '#6b7280'}),
                        ], className='col-6 mb-3'),
                        html.Div([
                            html.Div("Service Type", className='detail-label'),
                            html.Div(deal['service_type'] or '—', className='detail-value'),
                        ], className='col-6 mb-3'),
                        html.Div([
                            html.Div("Next Follow-Up", className='detail-label'),
                            html.Div(deal['next_follow_up'] or '—',
                                     style={'fontSize': '13px', 'fontWeight': '600',
                                            'color': '#ef4444'
                                            if deal['next_follow_up'] and
                                            deal['next_follow_up'] <= date.today().isoformat()
                                            else '#1a1a2e'}),
                        ], className='col-6 mb-3'),
                        html.Div([
                            html.Div("Expected Close", className='detail-label'),
                            html.Div(deal['close_date'] or '—', className='detail-value'),
                        ], className='col-6 mb-3'),
                        html.Div([
                            html.Div("Assigned To", className='detail-label'),
                            html.Div(deal['assigned_to'] or 'Unassigned', className='detail-value'),
                        ], className='col-6 mb-3'),
                    ])
                ]
            )
        ]
    )

    history_items = []
    if not history:
        history_items = html.Div("No stage history yet.",
                                 style={'color': '#9ca3af', 'fontSize': '12px'})
    else:
        for h in history:
            transition = (f"Changed stage: {h['from_stage']} → {h['to_stage']}"
                          if h['from_stage'] else f"Moved to {h['to_stage']}")
            history_items.append(
                html.Div(
                    className='stage-history-item',
                    children=[
                        html.Div(className='stage-history-dot'),
                        html.Div([
                            html.Div(transition, className='stage-history-text'),
                            html.Div(f"by {h['changed_by']} · {h['changed_at']}",
                                     className='stage-history-time')
                        ])
                    ]
                )
            )

    history_panel = html.Div(
        className='panel mb-4',
        children=[
            html.Div(className='panel-header',
                     children=[html.Div("Stage Transition Log", className='panel-title')]),
            html.Div(className='panel-body', children=[html.Div(history_items)])
        ]
    )

    note_items = []
    if not notes:
        note_items = empty_state(
            'bi bi-journal-text text-muted',
            'No notes yet',
            'Log calls, proposals, meetings, and milestones to keep the full deal history here.',
            action_label='Log First Note',
            action_id='add-deal-note-btn'
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
                                html.Span(f"by {n['created_by']} · {n['created_at']}",
                                          className='note-meta')
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
                    html.Div(f"Deal Notes ({len(notes)})", className='panel-title'),
                    html.Button(
                        [html.I(className='bi bi-plus-lg me-1'), "Add Note"],
                        id='add-deal-note-btn', className='btn-primary btn-sm'
                    )
                ]
            ),
            html.Div(className='panel-body',
                     children=[html.Div(note_items, className='notes-timeline')])
        ]
    )

    return html.Div([
        deal_modal('deal-crud-modal', 'deal-modal-title',
                   'deal-save-btn', 'deal-cancel-btn',
                   'deal-id-store', cfg.get('deal_stages', []),
                   cfg.get('service_types', []), crud.get_contacts()),
        confirm_modal('deal-delete-modal', 'Delete Deal',
                      'Are you sure you want to permanently delete this deal?',
                      'deal-delete-confirm-btn', 'deal-delete-cancel-btn'),
        note_modal('deal-note-crud-modal', 'deal-note-modal-title',
                   'deal-note-save-btn', 'deal-note-cancel-btn',
                   'deal-n-type', 'deal-n-body', 'deal-n-doc-link', 'deal-note-id-store'),
        confirm_modal('deal-note-delete-modal', 'Delete Note',
                      'Are you sure you want to permanently delete this note?',
                      'deal-note-delete-confirm-btn', 'deal-note-delete-cancel-btn'),

        dcc.Store(id='pipeline-refresh-trigger', data=0),

        html.Div(
            className='page-header',
            children=[html.Div([
                dcc.Link(
                    [html.I(className='bi bi-arrow-left me-1'), "Back to Pipeline"],
                    href='/pipeline', className='btn btn-secondary btn-sm mb-3'
                ),
                html.H1("Deal Details", className='page-title'),
            ])]
        ),

        html.Div(
            className='row',
            children=[
                html.Div([info_card, history_panel], className='col-lg-4 col-12'),
                html.Div(notes_panel, className='col-lg-8 col-12')
            ],
            style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px'}
        )
    ])


# ── Callbacks ─────────────────────────────────────────────────────────────────

@callback(
    Output('pipeline-view-store', 'data'),
    Output('view-kanban-btn', 'className'),
    Output('view-list-btn', 'className'),
    Input('view-kanban-btn', 'n_clicks'),
    Input('view-list-btn', 'n_clicks'),
    State('pipeline-view-store', 'data'),
    prevent_initial_call=True
)
def toggle_view(kanban_clicks, list_clicks, current):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update, no_update
    trigger = ctx.triggered[0]['prop_id']
    if 'view-kanban-btn' in trigger:
        return 'kanban', 'view-toggle-btn active', 'view-toggle-btn'
    elif 'view-list-btn' in trigger:
        return 'list', 'view-toggle-btn', 'view-toggle-btn active'
    return current, no_update, no_update


@callback(
    Output('pipeline-main-container', 'children'),
    Input('pipeline-view-store', 'data'),
    Input('deal-search-input', 'value'),
    Input('deal-filter-stage', 'value'),
    Input('pipeline-refresh-trigger', 'data'),
    prevent_initial_call=False
)
def render_pipeline_view(view_mode, search_val, stage_val, refresh):
    deals = crud.get_deals()
    cfg = load_config()
    stages = cfg.get('deal_stages', [])
    currency = cfg.get('currency_symbol', '$')
    today_str = date.today().isoformat()

    filtered = []
    for d in deals:
        if stage_val and d['stage'] != stage_val:
            continue
        if search_val:
            s = search_val.lower()
            if (s not in d['deal_name'].lower() and
                    s not in f"{d['first_name']} {d['last_name']}".lower() and
                    s not in (d['company'] or '').lower() and
                    s not in (d['service_type'] or '').lower()):
                continue
        filtered.append(d)

    if view_mode == 'kanban':
        by_stage = {s: [] for s in stages}
        for d in filtered:
            if d['stage'] in by_stage:
                by_stage[d['stage']].append(d)

        columns = []
        for st in stages:
            stage_deals = by_stage[st]
            cards = []
            for d in stage_deals:
                fu_class = 'deal-card-followup'
                if d['next_follow_up']:
                    if d['next_follow_up'] < today_str:
                        fu_class += ' overdue'
                    elif d['next_follow_up'] == today_str:
                        fu_class += ' due-today'

                cards.append(html.Div(
                    className='deal-card',
                    children=[
                        dcc.Link(
                            d['deal_name'],
                            href=f"/pipeline?deal_id={d['deal_id']}",
                            className='deal-card-name',
                        ),
                        html.Div(
                            f"{d['first_name']} {d['last_name']}" +
                            (f" · {d['company']}" if d['company'] else ''),
                            className='deal-card-contact'
                        ),
                        html.Div([
                            dcc.Dropdown(
                                id={'type': 'card-stage-select', 'index': d['deal_id']},
                                options=[{'label': s, 'value': s} for s in stages],
                                value=d['stage'],
                                clearable=False,
                                style={'fontSize': '11.5px'}
                            )
                        ], className='mt-2 card-stage-dropdown'),
                        html.Div(
                            className='deal-card-meta',
                            children=[
                                html.Span(
                                    f"{currency}{d['value']:,.0f}" if d['value'] else '—',
                                    className='deal-card-value'
                                ),
                                html.Span(
                                    [html.I(className='bi bi-calendar3 me-1'),
                                     d['next_follow_up'] or 'No date'],
                                    className=fu_class
                                )
                            ]
                        )
                    ]
                ))

            columns.append(html.Div(
                className='kanban-column',
                children=[
                    html.Div(
                        className='kanban-column-header',
                        children=[
                            html.Span(st),
                            html.Span(f"{len(stage_deals)}", className='stage-count')
                        ]
                    ),
                    html.Div(cards, className='kanban-cards')
                ]
            ))

        return html.Div(columns, id='kanban-board')

    else:
        if not filtered:
            if search_val or stage_val:
                return html.Div(className='panel', children=[html.Div(className='panel-body', children=[
                    empty_state('bi bi-search text-muted', 'No deals match your filters',
                                'Try a different search term or clear the stage filter.')
                ])])
            return html.Div(className='panel', children=[html.Div(className='panel-body', children=[
                empty_state(
                    'bi bi-funnel text-muted',
                    'Your pipeline is empty',
                    'Add your first deal to start tracking revenue and moving contacts through stages.',
                    action_label='Add First Deal', action_id='add-deal-btn'
                )
            ])])

        return html.Div(
            className='panel',
            children=[html.Div(
                className='panel-body',
                children=[html.Table(
                    className='table table-hover align-middle',
                    children=[
                        html.Thead(html.Tr([
                            html.Th("Deal Name"), html.Th("Contact"), html.Th("Service"),
                            html.Th("Stage"), html.Th("Value"), html.Th("Prob."),
                            html.Th("Follow-Up"), html.Th("Assigned"),
                            html.Th("", style={'textAlign': 'right'})
                        ])),
                        html.Tbody([
                            html.Tr([
                                html.Td(dcc.Link(
                                    d['deal_name'],
                                    href=f"/pipeline?deal_id={d['deal_id']}",
                                    style={'color': 'var(--color-primary)', 'fontWeight': '600'}
                                )),
                                html.Td(dcc.Link(
                                    f"{d['first_name']} {d['last_name']}",
                                    href=f"/contacts?contact_id={d['contact_id']}",
                                    style={'textDecoration': 'underline'}
                                )),
                                html.Td(d['service_type'] or '—'),
                                html.Td(html.Span(
                                    d['stage'],
                                    className=f"stage-badge {d['stage'].lower().replace(' ', '-')}"
                                )),
                                html.Td(
                                    f"{currency}{d['value']:,.2f}" if d['value'] else '—',
                                    style={'fontWeight': '600'}
                                ),
                                html.Td(f"{d['probability']}%"),
                                html.Td(
                                    d['next_follow_up'] or '—',
                                    className='text-danger fw-bold'
                                    if d['next_follow_up'] and d['next_follow_up'] <= today_str
                                    else ''
                                ),
                                html.Td(d['assigned_to'] or '—'),
                                html.Td(html.Div([
                                    html.Button(
                                        [html.I(className='bi bi-pencil me-1'), "Edit"],
                                        id={'type': 'edit-deal-btn', 'index': d['deal_id']},
                                        className='btn-secondary btn-sm me-2'
                                    ),
                                    html.Button(
                                        html.I(className='bi bi-trash'),
                                        id={'type': 'delete-deal-btn', 'index': d['deal_id']},
                                        className='btn-icon btn-sm btn-icon-danger'
                                    )
                                ], style={'display': 'flex', 'justifyContent': 'flex-end',
                                          'alignItems': 'center'}))
                            ]) for d in filtered
                        ])
                    ],
                    style={'width': '100%'}
                )]
            )]
        )


@callback(
    Output('pipeline-refresh-trigger', 'data'),
    Input({'type': 'card-stage-select', 'index': dash.ALL}, 'value'),
    State({'type': 'card-stage-select', 'index': dash.ALL}, 'id'),
    State('pipeline-refresh-trigger', 'data'),
    prevent_initial_call=True
)
def update_stage_from_card(stages_val, ids, refresh):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update
    trigger_id = ctx.triggered[0]['prop_id']
    if 'card-stage-select' in trigger_id:
        try:
            triggered_dict = json.loads(trigger_id.split('.')[0])
            deal_id = triggered_dict.get('index')
            new_stage = None
            for d_id, val in zip(ids, stages_val):
                if d_id['index'] == deal_id:
                    new_stage = val
                    break
            if new_stage:
                deal = crud.get_deal(deal_id)
                if deal and deal['stage'] != new_stage:
                    user = flask_login.current_user
                    username = user.email.split('@')[0] if user else 'teammate'
                    data = dict(deal)
                    data['stage'] = new_stage
                    crud.update_deal(deal_id, data, changed_by=username)
                    return refresh + 1
        except Exception as e:
            print("Error updating stage from card:", e)
    return no_update


@callback(
    Output('deal-crud-modal', 'is_open'),
    Output('deal-modal-title', 'children'),
    Output('deal-id-store', 'data'),
    Output('d-deal-name', 'value'),
    Output('d-contact-id', 'value'),
    Output('d-service-type', 'value'),
    Output('d-stage', 'value'),
    Output('d-value', 'value'),
    Output('d-probability', 'value'),
    Output('d-next-follow-up', 'date'),
    Output('d-close-date', 'date'),
    Output('d-assigned-to', 'value'),
    Input('add-deal-btn', 'n_clicks'),
    Input({'type': 'edit-deal-btn', 'index': dash.ALL}, 'n_clicks'),
    Input('deal-cancel-btn', 'n_clicks'),
    Input('deal-init-params', 'data'),
    State('deal-crud-modal', 'is_open'),
    prevent_initial_call=False
)
def toggle_deal_modal(add_clicks, edit_clicks, cancel_clicks, init_params, is_open):
    ctx = dash.callback_context

    if not ctx.triggered:
        return no_update, no_update, no_update, *[no_update]*9

    trigger_id  = ctx.triggered[0]['prop_id']
    trigger_val = ctx.triggered[0]['value']

    # URL param auto-open (navigating from contacts detail with ?new_deal=1)
    if trigger_id == 'deal-init-params.data':
        if isinstance(init_params, dict) and init_params.get('new_deal') == '1':
            return (True,
                    [html.I(className='bi bi-plus-lg me-2'), "Add New Deal"],
                    None, None, init_params.get('contact_id'),
                    None, 'New Lead', None, 50, None, None, None)
        return no_update, no_update, no_update, *[no_update]*9

    if 'deal-cancel-btn' in trigger_id:
        return False, no_update, no_update, *[None]*9

    if 'add-deal-btn' in trigger_id:
        if not trigger_val:
            return no_update, no_update, no_update, *[no_update]*9
        return (True,
                [html.I(className='bi bi-plus-lg me-2'), "Add New Deal"],
                None, None, None, None, 'New Lead', None, 50, None, None, None)

    if 'edit-deal-btn' in trigger_id:
        # n_clicks=0 or None means the button was just injected into the DOM — not a real click
        if not trigger_val:
            return no_update, no_update, no_update, *[no_update]*9
        try:
            triggered_dict = json.loads(trigger_id.split('.')[0])
            deal_id = triggered_dict.get('index')
            d = crud.get_deal(deal_id)
            if d:
                return (True,
                        [html.I(className='bi bi-pencil me-2'), f"Edit: {d['deal_name']}"],
                        deal_id,
                        d['deal_name'], d['contact_id'], d['service_type'],
                        d['stage'], d['value'], d['probability'],
                        d['next_follow_up'], d['close_date'], d['assigned_to'])
        except Exception as e:
            print("Error toggling edit deal modal:", e)

    return no_update, no_update, no_update, *[no_update]*9


@callback(
    Output('deal-init-params', 'data'),
    Output('url', 'search', allow_duplicate=True),
    Output('deal-crud-modal', 'is_open', allow_duplicate=True),
    Input('deal-save-btn', 'n_clicks'),
    State('deal-id-store', 'data'),
    State('d-deal-name', 'value'),
    State('d-contact-id', 'value'),
    State('d-service-type', 'value'),
    State('d-stage', 'value'),
    State('d-value', 'value'),
    State('d-probability', 'value'),
    State('d-next-follow-up', 'date'),
    State('d-close-date', 'date'),
    State('d-assigned-to', 'value'),
    State('url', 'pathname'),
    State('url', 'search'),
    prevent_initial_call=True
)
def save_deal(n_clicks, deal_id, name, contact_id, service_type, stage, value,
              prob, follow_up, close_date, assigned_to, pathname, search):
    if not n_clicks or not name or not contact_id:
        return no_update, no_update, no_update

    user = flask_login.current_user
    username = user.email.split('@')[0] if user else 'teammate'

    data = {
        'contact_id': contact_id, 'deal_name': name, 'service_type': service_type,
        'stage': stage, 'value': value, 'probability': prob or 50,
        'next_follow_up': follow_up, 'close_date': close_date, 'assigned_to': assigned_to
    }

    if deal_id:
        crud.update_deal(deal_id, data, changed_by=username)
        if search and 'deal_id=' in search:
            return None, search, False
    else:
        crud.create_deal(data, created_by=username)

    return None, '', False


@callback(
    Output('deal-delete-modal', 'is_open'),
    Output('deal-delete-confirm-btn', 'style'),
    Input({'type': 'delete-deal-btn', 'index': dash.ALL}, 'n_clicks'),
    Input('deal-delete-confirm-btn', 'n_clicks'),
    Input('deal-delete-cancel-btn', 'n_clicks'),
    State('deal-delete-modal', 'is_open'),
    prevent_initial_call=True
)
def toggle_delete_modal(delete_clicks, confirm_clicks, cancel_clicks, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update
    trigger_id = ctx.triggered[0]['prop_id']

    if 'deal-delete-cancel-btn' in trigger_id:
        return False, no_update

    if 'delete-deal-btn' in trigger_id:
        if not ctx.triggered[0]['value']:
            return no_update, no_update
        try:
            triggered_dict = json.loads(trigger_id.split('.')[0])
            deal_id = triggered_dict.get('index')
            return True, {'display': 'inline-block', 'data-id': deal_id}
        except Exception:
            pass

    if 'deal-delete-confirm-btn' in trigger_id:
        return False, no_update

    return no_update, no_update


@callback(
    Output('url', 'pathname', allow_duplicate=True),
    Input('deal-delete-confirm-btn', 'n_clicks'),
    State('deal-delete-confirm-btn', 'style'),
    prevent_initial_call=True
)
def delete_deal_action(n_clicks, btn_style):
    if not n_clicks or not btn_style or 'data-id' not in btn_style:
        return no_update
    crud.soft_delete_deal(btn_style['data-id'])
    return '/pipeline'


# ── Note Callbacks (detail view only) ────────────────────────────────────────

@callback(
    Output('deal-note-crud-modal', 'is_open'),
    Output('deal-note-modal-title', 'children'),
    Output('deal-note-id-store', 'data'),
    Output('deal-n-type', 'value'),
    Output('deal-n-body', 'value'),
    Output('deal-n-doc-link', 'value'),
    Input('add-deal-note-btn', 'n_clicks'),
    Input({'type': 'edit-note-btn', 'index': dash.ALL}, 'n_clicks'),
    Input('deal-note-cancel-btn', 'n_clicks'),
    State('deal-note-crud-modal', 'is_open'),
    prevent_initial_call=True
)
def toggle_deal_note_modal(add_clicks, edit_clicks, cancel_clicks, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update, no_update, 'Internal', '', ''
    trigger_id = ctx.triggered[0]['prop_id']

    if 'deal-note-cancel-btn' in trigger_id:
        return False, no_update, no_update, 'Internal', '', ''

    if 'add-deal-note-btn' in trigger_id:
        return True, [html.I(className='bi bi-plus-lg me-2'), "Add Deal Note"], None, 'Internal', '', ''

    if 'edit-note-btn' in trigger_id:
        try:
            triggered_dict = json.loads(trigger_id.split('.')[0])
            note_id = triggered_dict.get('index')
            n = crud.get_note(note_id)
            if n:
                return (True, [html.I(className='bi bi-pencil me-2'), "Edit Note"],
                        note_id, n['note_type'], n['body'], n['doc_link'])
        except Exception as e:
            print("Error toggling edit note:", e)

    return False, no_update, no_update, 'Internal', '', ''


@callback(
    Output('url', 'search', allow_duplicate=True),
    Output('deal-note-crud-modal', 'is_open', allow_duplicate=True),
    Input('deal-note-save-btn', 'n_clicks'),
    State('deal-note-id-store', 'data'),
    State('deal-n-type', 'value'),
    State('deal-n-body', 'value'),
    State('deal-n-doc-link', 'value'),
    State('url', 'search'),
    prevent_initial_call=True
)
def save_deal_note(n_clicks, note_id, note_type, body, doc_link, search):
    if not n_clicks or not body:
        return no_update, no_update

    deal_id = None
    if search and 'deal_id=' in search:
        deal_id = search.split('deal_id=')[1].split('&')[0]

    deal = crud.get_deal(deal_id)
    contact_id = deal['contact_id'] if deal else None
    user = flask_login.current_user
    username = user.email.split('@')[0] if user else 'teammate'

    data = {
        'deal_id': deal_id, 'contact_id': contact_id,
        'note_type': note_type, 'body': body,
        'doc_link': doc_link, 'created_by': username
    }

    if note_id:
        crud.update_note(note_id, data)
    else:
        crud.create_note(data)

    return search, False


@callback(
    Output('deal-note-delete-modal', 'is_open'),
    Output('deal-note-delete-confirm-btn', 'style'),
    Input({'type': 'delete-note-btn', 'index': dash.ALL}, 'n_clicks'),
    Input('deal-note-delete-confirm-btn', 'n_clicks'),
    Input('deal-note-delete-cancel-btn', 'n_clicks'),
    State('deal-note-delete-modal', 'is_open'),
    prevent_initial_call=True
)
def toggle_note_delete_modal(delete_clicks, confirm_clicks, cancel_clicks, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update
    trigger_id = ctx.triggered[0]['prop_id']

    if 'deal-note-delete-cancel-btn' in trigger_id:
        return False, no_update

    if 'delete-note-btn' in trigger_id:
        try:
            triggered_dict = json.loads(trigger_id.split('.')[0])
            note_id = triggered_dict.get('index')
            return True, {'display': 'inline-block', 'data-id': note_id}
        except Exception:
            pass

    if 'deal-note-delete-confirm-btn' in trigger_id:
        return False, no_update

    return no_update, no_update


@callback(
    Output('url', 'search', allow_duplicate=True),
    Input('deal-note-delete-confirm-btn', 'n_clicks'),
    State('deal-note-delete-confirm-btn', 'style'),
    State('url', 'search'),
    prevent_initial_call=True
)
def delete_note_action(n_clicks, btn_style, search):
    if not n_clicks or not btn_style or 'data-id' not in btn_style:
        return no_update
    crud.delete_note(btn_style['data-id'])
    return search
