"""
pages/dashboard.py — Dashboard page for EtherealCRM.
Shows stat cards, pipeline chart, follow-up alerts, and recent notes activity.
"""

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from datetime import date
from db import crud
import yaml
import os

dash.register_page(__name__, path='/dashboard')

def load_config() -> dict:
    CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def layout():
    cfg = load_config()
    stats = crud.get_pipeline_stats()
    recent_notes = crud.get_recent_notes(10)
    followups = crud.get_followup_deals(cfg.get('follow_up_warning_days', 3))
    
    # Filter for overdue or due today follow-up alerts specifically
    today_str = date.today().isoformat()
    alerts = [f for f in followups if f.get('next_follow_up', '') <= today_str]
    
    currency = cfg.get('currency_symbol', '$')

    # Stat Cards
    stat_cards = html.Div(
        className='stat-cards-row',
        children=[
            html.Div(
                className='stat-card',
                children=[
                    html.Div("Open Deals", className='stat-card-label'),
                    html.Div(f"{stats['open_deals']}", className='stat-card-value'),
                    html.Div("Active in pipeline", className='stat-card-sub'),
                ]
            ),
            html.Div(
                className='stat-card',
                children=[
                    html.Div("Pipeline Value", className='stat-card-label'),
                    html.Div(f"{currency}{stats['pipeline_value']:,.2f}", className='stat-card-value'),
                    html.Div("Total estimated value", className='stat-card-sub'),
                ]
            ),
            html.Div(
                className='stat-card',
                children=[
                    html.Div("Win Rate", className='stat-card-label'),
                    html.Div(f"{stats['win_rate']}%", className='stat-card-value'),
                    html.Div(f"{stats['won']} Won / {stats['lost']} Lost", className='stat-card-sub'),
                ]
            ),
            html.Div(
                className='stat-card',
                children=[
                    html.Div("Pending Follow-Ups", className='stat-card-label'),
                    html.Div(f"{stats['overdue_followups']}", className='stat-card-value'),
                    html.Div("Today or overdue", className='stat-card-sub'),
                ]
            ),
        ]
    )

    # Pipeline Chart
    stages = cfg.get('deal_stages', [])
    stage_data = {s['stage']: s for s in stats['by_stage']}
    x_data = stages
    y_count = [stage_data.get(st, {}).get('cnt', 0) for st in stages]
    y_val = [stage_data.get(st, {}).get('total_value', 0.0) for st in stages]
    
    primary_color = cfg.get('color_primary', '#FF120A')
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x_data,
        y=y_count,
        name='Deals Count',
        marker_color=primary_color,
        yaxis='y',
        hovertemplate='%{x}: %{y} deals<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=x_data,
        y=y_val,
        name='Value',
        marker_color='#36454F',
        line=dict(color='#36454F', width=2),
        yaxis='y2',
        hovertemplate='%{x}: ' + currency + '%{y:,.2f}<extra></extra>'
    ))

    fig.update_layout(
        title='Pipeline by Stage',
        title_font=dict(size=14, family='Inter, sans-serif', color='#1a1a2e', weight='bold'),
        template='plotly_white',
        margin=dict(l=40, r=40, t=40, b=40),
        height=320,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(
            title='Number of Deals',
            titlefont=dict(color=primary_color),
            tickfont=dict(color=primary_color)
        ),
        yaxis2=dict(
            title='Pipeline Value',
            titlefont=dict(color='#36454F'),
            tickfont=dict(color='#36454F'),
            overlaying='y',
            side='right'
        )
    )

    chart_panel = html.Div(
        className='panel mb-4',
        children=[
            html.Div(
                className='panel-header',
                children=[html.Div("Pipeline Chart Summary", className='panel-title')]
            ),
            html.Div(
                className='panel-body',
                children=[dcc.Graph(figure=fig, config={'displayModeBar': False})]
            )
        ]
    )

    # Alerts List
    alert_items = []
    if not alerts:
        alert_items = html.Div(
            className='empty-state',
            children=[
                html.Div("✅", className='empty-state-icon'),
                html.Div("All caught up!", className='empty-state-title'),
                html.Div("No overdue or pending follow-ups for today.", className='empty-state-text')
            ]
        )
    else:
        for a in alerts[:5]:
            badge_class = 'urgency-badge overdue' if a['urgency'] == 'overdue' else 'urgency-badge due-today'
            alert_items.append(
                html.Div(
                    className=f"followup-row {a['urgency']}",
                    children=[
                        html.Div([
                            dcc.Link(
                                a['deal_name'],
                                href=f"/pipeline?deal_id={a['deal_id']}",
                                className='followup-deal-name',
                                style={'color': 'var(--color-primary)', 'fontWeight': '600'}
                            ),
                            html.Div(f"{a['first_name']} {a['last_name']} ({a['company']})", className='followup-contact')
                        ]),
                        html.Div(html.Span(a['urgency'].replace('-', ' ').upper(), className=badge_class)),
                        html.Div(f"{currency}{a['value']:,.2f}", style={'fontWeight': 'bold'}),
                        html.Div(f"Due: {a['next_follow_up']}", style={'fontSize': '12px', 'color': '#6b7280'}),
                        html.Div([
                            dcc.Link(
                                "Go to Deal ➜",
                                href=f"/pipeline?deal_id={a['deal_id']}",
                                className='btn btn-primary btn-sm'
                            )
                        ])
                    ],
                    style={'padding': '10px 14px', 'gridTemplateColumns': '1.5fr 1fr 1fr 1fr 1fr', 'marginBottom': '8px'}
                )
            )

    alert_panel = html.Div(
        className='panel mb-4',
        children=[
            html.Div(
                className='panel-header',
                children=[html.Div("Critical Follow-Up Alerts", className='panel-title')]
            ),
            html.Div(
                className='panel-body',
                children=alert_items
            )
        ],
        style={'flex': '1', 'minWidth': '320px'}
    )

    # Recent Activity (Notes)
    activity_items = []
    if not recent_notes:
        activity_items = html.Div(
            className='empty-state',
            children=[
                html.Div("📝", className='empty-state-icon'),
                html.Div("No Activity Yet", className='empty-state-title'),
                html.Div("Create contacts or deals and log notes to see activity here.", className='empty-state-text')
            ]
        )
    else:
        for n in recent_notes:
            ref_name = f"Deal: {n['deal_name']}" if n['deal_name'] else f"Contact: {n['contact_name']}"
            ref_link = f"/pipeline?deal_id={n['deal_id']}" if n['deal_id'] else f"/contacts?contact_id={n['contact_id']}"
            
            activity_items.append(
                html.Div(
                    className='activity-item',
                    children=[
                        html.Div(className='activity-dot'),
                        html.Div([
                            html.Div([
                                html.Span(f"{n['created_by']} logged a ", style={'color': '#6b7280'}),
                                html.Span(n['note_type'], style={'fontWeight': 'bold', 'color': 'var(--color-primary)'}),
                                html.Span(" on ", style={'color': '#6b7280'}),
                                dcc.Link(ref_name, href=ref_link, style={'color': '#1a1a2e', 'textDecoration': 'underline', 'fontWeight': '500'})
                            ], className='activity-text'),
                            html.Div(
                                n['body'][:120] + ('...' if len(n['body'] or '') > 120 else ''),
                                style={'fontSize': '12.5px', 'color': '#4b5563', 'marginTop': '4px', 'fontStyle': 'italic'}
                            ),
                            html.Div(n['created_at'], className='activity-time')
                        ])
                    ]
                )
            )

    activity_panel = html.Div(
        className='panel mb-4',
        children=[
            html.Div(
                className='panel-header',
                children=[html.Div("Recent Notes & Updates", className='panel-title')]
            ),
            html.Div(
                className='panel-body',
                children=activity_items
            )
        ],
        style={'flex': '1', 'minWidth': '320px'}
    )

    bottom_row = html.Div(
        className='row',
        children=[
            html.Div(alert_panel, className='col-lg-6 col-12'),
            html.Div(activity_panel, className='col-lg-6 col-12')
        ],
        style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px'}
    )

    return html.Div([
        html.Div(
            className='page-header',
            children=[
                html.Div([
                    html.H1(f"{cfg.get('agency_name', 'Etherea Labs')} CRM Dashboard", className='page-title'),
                    html.P("Overview of active deals, follow-ups, and recent team updates.", className='page-subtitle'),
                ]),
            ]
        ),
        stat_cards,
        chart_panel,
        bottom_row
    ])
