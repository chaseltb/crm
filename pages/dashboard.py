"""
pages/dashboard.py — Dashboard for EtherealCRM.
"""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from datetime import date
from db import crud
from components.skeletons import empty_state
from utils.config import load_config

dash.register_page(__name__, path='/dashboard')


# ── Shared chart theme ────────────────────────────────────────────────────────

_CHART_LAYOUT = dict(
    template='plotly_white',
    plot_bgcolor='#ffffff',
    paper_bgcolor='#ffffff',
    font=dict(family='Inter, sans-serif', size=12, color='#374151'),
    legend=dict(
        orientation='h', yanchor='bottom', y=1.02,
        xanchor='right', x=1,
        font=dict(size=11),
    ),
)
# Margin kept separate so each chart can override without a kwarg conflict
_MARGIN     = dict(l=48,  r=24, t=48, b=40)
_MARGIN_SRC = dict(l=100, r=24, t=48, b=40)  # source chart needs wider left for labels

_AXIS_BASE = dict(gridcolor='#f3f4f6', linecolor='#e5e7eb')

GREY = '#e5e7eb'


def _panel(title, graph, subtitle=None):
    header_children = [html.Div(title, className='panel-title')]
    if subtitle:
        header_children.append(
            html.Div(subtitle, style={'fontSize': '11px', 'color': '#9ca3af', 'fontWeight': '400'})
        )
    return html.Div(
        className='panel',
        children=[
            html.Div(className='panel-header',
                     children=[html.Div(header_children, style={'display': 'flex', 'flexDirection': 'column', 'gap': '1px'})]),
            html.Div(className='panel-body', children=[
                dcc.Graph(figure=graph, config={'displayModeBar': False})
            ])
        ]
    )


# ── Layout ────────────────────────────────────────────────────────────────────

def layout():
    cfg = load_config()
    stats          = crud.get_pipeline_stats()
    contact_count  = crud.get_contact_count()
    recent_notes   = crud.get_recent_notes(10)
    followups      = crud.get_followup_deals(cfg.get('follow_up_warning_days', 3))
    won_by_month   = crud.get_won_revenue_by_month(6)
    by_source      = crud.get_pipeline_by_source()

    today_str  = date.today().isoformat()
    alerts     = [f for f in followups if f.get('next_follow_up', '') <= today_str]
    overdue    = [f for f in alerts if f.get('urgency') == 'overdue']
    currency   = cfg.get('currency_symbol', '$')
    primary    = cfg.get('color_primary', '#FF120A')

    # ── Overdue banner ───────────────────────────────────────────────────────
    reminder_banner = None
    if overdue:
        reminder_banner = html.Div(
            className='reminder-banner',
            children=[
                html.I(className='bi bi-exclamation-triangle-fill me-2'),
                html.Strong(f"{len(overdue)} overdue follow-up{'s' if len(overdue) > 1 else ''}"),
                html.Span(" — deals waiting on you: "),
                html.Span(", ".join(f['deal_name'] for f in overdue[:3]) +
                          (f" +{len(overdue) - 3} more" if len(overdue) > 3 else "")),
                dcc.Link("Review now →", href='/followups',
                         style={'marginLeft': '12px', 'color': '#92400e',
                                'fontWeight': '700', 'textDecoration': 'underline'})
            ]
        )

    # ── Stat cards ───────────────────────────────────────────────────────────
    def stat_card(label, value, sub, icon, accent=False):
        return html.Div(
            className=f"stat-card{'  stat-card-accent' if accent else ''}",
            children=[
                html.Div([
                    html.Div(label, className='stat-card-label'),
                    html.I(className=f"{icon} stat-card-icon"),
                ], style={'display': 'flex', 'justifyContent': 'space-between'}),
                html.Div(str(value), className='stat-card-value'),
                html.Div(sub, className='stat-card-sub'),
            ]
        )

    stat_cards = html.Div(
        className='stat-cards-row mb-4',
        children=[
            stat_card("Total Contacts",  contact_count,
                      "In your database", "bi bi-people-fill"),
            stat_card("Open Deals",      stats['open_deals'],
                      "Active in pipeline", "bi bi-briefcase-fill"),
            stat_card("Pipeline Value",  f"{currency}{stats['pipeline_value']:,.0f}",
                      "Estimated revenue", "bi bi-currency-dollar"),
            stat_card("Win Rate",        f"{stats['win_rate']}%",
                      f"{stats['won']} Won · {stats['lost']} Lost", "bi bi-trophy-fill"),
            stat_card("Follow-Ups Due",  stats['overdue_followups'],
                      "Today or overdue", "bi bi-bell-fill",
                      accent=stats['overdue_followups'] > 0),
        ]
    )

    # ── Chart 1: Pipeline by Stage ───────────────────────────────────────────
    stages     = cfg.get('deal_stages', [])
    stage_data = {s['stage']: s for s in stats['by_stage']}
    y_count    = [stage_data.get(st, {}).get('cnt', 0) for st in stages]
    y_val      = [stage_data.get(st, {}).get('total_value', 0.0) for st in stages]

    fig_pipeline = go.Figure([
        go.Bar(
            x=stages, y=y_count, name='# Deals',
            marker_color=primary, yaxis='y',
            hovertemplate='%{x}: %{y} deal(s)<extra></extra>'
        ),
        go.Scatter(
            x=stages, y=y_val, name='Pipeline Value',
            line=dict(color='#6b7280', width=2, dash='dot'),
            marker=dict(size=6, color='#6b7280'),
            yaxis='y2',
            hovertemplate='%{x}: ' + currency + '%{y:,.0f}<extra></extra>'
        ),
    ])
    fig_pipeline.update_layout(**_CHART_LAYOUT, height=300, bargap=0.35,
        margin=_MARGIN,
        title=dict(text='Deals by Stage', font=dict(size=13, color='#1a1a2e')))
    fig_pipeline.update_layout(
        xaxis=dict(**_AXIS_BASE),
        yaxis=dict(**_AXIS_BASE, title=None),
        yaxis2=dict(title=None, overlaying='y', side='right',
                    showgrid=False,
                    tickprefix=currency),
    )
    chart_pipeline = _panel("Pipeline by Stage",
                            fig_pipeline,
                            "Deal count and estimated value per stage")

    # ── Chart 2: Won Revenue by Month ────────────────────────────────────────
    # Short month labels (e.g. "Jun '25")
    def _month_label(ym: str) -> str:
        y, m = ym.split('-')
        import calendar
        return f"{calendar.month_abbr[int(m)]} '{y[2:]}"

    months_labels  = [_month_label(r['month']) for r in won_by_month]
    months_revenue = [r['revenue'] for r in won_by_month]
    months_count   = [r['deals_closed'] for r in won_by_month]
    total_won      = sum(months_revenue)
    has_won_data   = total_won > 0

    if has_won_data:
        fig_revenue = go.Figure([
            go.Bar(
                x=months_labels, y=months_revenue,
                name='Revenue Closed',
                marker_color=[primary if v > 0 else GREY for v in months_revenue],
                hovertemplate='%{x}: ' + currency + '%{y:,.0f}<extra></extra>',
                yaxis='y',
            ),
            go.Scatter(
                x=months_labels, y=months_count,
                name='Deals Won',
                mode='lines+markers',
                line=dict(color='#6b7280', width=2),
                marker=dict(size=6, color='#6b7280'),
                yaxis='y2',
                hovertemplate='%{x}: %{y} deal(s)<extra></extra>',
            ),
        ])
        fig_revenue.update_layout(**_CHART_LAYOUT, height=300, bargap=0.4,
            margin=_MARGIN,
            title=dict(text='Won Revenue — Last 6 Months',
                       font=dict(size=13, color='#1a1a2e')))
        fig_revenue.update_layout(
            xaxis=dict(**_AXIS_BASE),
            yaxis=dict(**_AXIS_BASE, title=None,
                       tickprefix=currency),
            yaxis2=dict(title=None, overlaying='y', side='right',
                        showgrid=False),
        )
    else:
        fig_revenue = go.Figure()
        fig_revenue.update_layout(
            **_CHART_LAYOUT, height=300,
            margin=_MARGIN,
            title=dict(text='Won Revenue — Last 6 Months',
                       font=dict(size=13, color='#1a1a2e')),
            annotations=[dict(
                text="No closed deals yet — revenue will appear here as you win deals.",
                x=0.5, y=0.5, xref='paper', yref='paper',
                showarrow=False, font=dict(size=12, color='#9ca3af')
            )]
        )

    chart_revenue = _panel(
        "Won Revenue Trend",
        fig_revenue,
        "Closed revenue & deal count per month · last 6 months"
    )

    # ── Chart 3: Pipeline Value by Lead Source ───────────────────────────────
    has_source_data = bool(by_source)

    if has_source_data:
        sources       = [r['source'] for r in by_source]
        pipeline_vals = [r['total_pipeline'] for r in by_source]
        won_vals      = [r['won_value'] for r in by_source]
        deal_counts   = [r['deal_count'] for r in by_source]

        fig_source = go.Figure([
            go.Bar(
                name='Total Pipeline',
                y=sources, x=pipeline_vals,
                orientation='h',
                marker_color=primary,
                opacity=0.35,
                hovertemplate='%{y}: ' + currency + '%{x:,.0f} pipeline<extra></extra>',
            ),
            go.Bar(
                name='Won Revenue',
                y=sources, x=won_vals,
                orientation='h',
                marker_color=primary,
                hovertemplate='%{y}: ' + currency + '%{x:,.0f} won<extra></extra>',
            ),
        ])
        fig_source.update_layout(**_CHART_LAYOUT, height=300,
            barmode='overlay', bargap=0.3,
            margin=_MARGIN_SRC,
            title=dict(text='Pipeline by Lead Source',
                       font=dict(size=13, color='#1a1a2e')))
        fig_source.update_layout(
            xaxis=dict(**_AXIS_BASE, title=None, tickprefix=currency),
            yaxis=dict(**_AXIS_BASE, title=None, autorange='reversed'),
        )
    else:
        fig_source = go.Figure()
        fig_source.update_layout(
            **_CHART_LAYOUT, height=300,
            margin=_MARGIN_SRC,
            title=dict(text='Pipeline by Lead Source',
                       font=dict(size=13, color='#1a1a2e')),
            annotations=[dict(
                text="No deals with source data yet.",
                x=0.5, y=0.5, xref='paper', yref='paper',
                showarrow=False, font=dict(size=12, color='#9ca3af')
            )]
        )

    chart_source = _panel(
        "Pipeline by Lead Source",
        fig_source,
        "Total pipeline vs won revenue per acquisition channel"
    )

    # Row: revenue trend (left, wider) + source breakdown (right)
    charts_row2 = html.Div(
        className='charts-row mb-4',
        children=[
            html.Div(chart_revenue, className='chart-col-wide'),
            html.Div(chart_source,  className='chart-col-narrow'),
        ]
    )

    # ── Follow-up alerts ─────────────────────────────────────────────────────
    if not alerts:
        alert_items = html.Div(
            className='empty-state',
            children=[
                html.Div(html.I(className='bi bi-check-circle-fill',
                                style={'fontSize': '40px', 'color': '#22c55e'}),
                         className='empty-state-icon'),
                html.Div("All caught up!", className='empty-state-title'),
                html.Div("No overdue or due-today follow-ups. Keep the momentum going.",
                         className='empty-state-text'),
                dcc.Link([html.I(className='bi bi-bell me-2'), "View All Follow-Ups"],
                         href='/followups', className='btn btn-secondary mt-3',
                         style={'display': 'inline-flex', 'alignItems': 'center'})
            ]
        )
    else:
        alert_items = []
        for a in alerts[:5]:
            badge_class = ('urgency-badge overdue' if a['urgency'] == 'overdue'
                           else 'urgency-badge due-today')
            alert_items.append(html.Div(
                className=f"followup-row {a['urgency']}",
                children=[
                    html.Div([
                        dcc.Link(a['deal_name'], href=f"/pipeline?deal_id={a['deal_id']}",
                                 className='followup-deal-name',
                                 style={'color': 'var(--color-primary)', 'fontWeight': '600'}),
                        html.Div(f"{a['first_name']} {a['last_name']} · {a['company']}",
                                 className='followup-contact')
                    ]),
                    html.Div(html.Span(a['urgency'].replace('-', ' ').upper(),
                                      className=badge_class)),
                    html.Div(f"{currency}{a['value']:,.0f}" if a['value'] else '—',
                             style={'fontWeight': '600'}),
                    html.Div(f"Due: {a['next_follow_up']}",
                             style={'fontSize': '12px', 'color': '#6b7280'}),
                    html.Div(dcc.Link(
                        [html.I(className='bi bi-arrow-right me-1'), "View"],
                        href=f"/pipeline?deal_id={a['deal_id']}",
                        className='btn btn-primary btn-sm'
                    ))
                ],
                style={'padding': '10px 14px',
                       'gridTemplateColumns': '1.5fr 1fr 1fr 1fr auto',
                       'marginBottom': '8px'}
            ))

    alert_panel = html.Div(
        className='panel mb-4',
        style={'flex': '1', 'minWidth': '320px'},
        children=[
            html.Div(className='panel-header',
                     children=[html.Div("Critical Follow-Up Alerts", className='panel-title')]),
            html.Div(className='panel-body', children=alert_items)
        ]
    )

    # ── Recent activity ───────────────────────────────────────────────────────
    if not recent_notes:
        activity_items = html.Div(
            className='empty-state',
            children=[
                html.Div(html.I(className='bi bi-journal', style={'fontSize': '40px'}),
                         className='empty-state-icon'),
                html.Div("No Activity Yet", className='empty-state-title'),
                html.Div("Log calls, emails, or meetings on any deal or contact.",
                         className='empty-state-text'),
                dcc.Link([html.I(className='bi bi-people me-2'), "Go to Contacts"],
                         href='/contacts', className='btn btn-secondary mt-3',
                         style={'display': 'inline-flex', 'alignItems': 'center'})
            ]
        )
    else:
        activity_items = []
        for n in recent_notes:
            ref_name = (f"Deal: {n['deal_name']}" if n['deal_name']
                        else f"Contact: {n['contact_name']}")
            ref_link = (f"/pipeline?deal_id={n['deal_id']}" if n['deal_id']
                        else f"/contacts?contact_id={n['contact_id']}")
            activity_items.append(html.Div(
                className='activity-item',
                children=[
                    html.Div(className='activity-dot'),
                    html.Div([
                        html.Div([
                            html.Span(f"{n['created_by']} logged a ",
                                      style={'color': '#6b7280'}),
                            html.Span(n['note_type'],
                                      style={'fontWeight': '600',
                                             'color': 'var(--color-primary)'}),
                            html.Span(" on ", style={'color': '#6b7280'}),
                            dcc.Link(ref_name, href=ref_link,
                                     style={'color': '#1a1a2e',
                                            'textDecoration': 'underline',
                                            'fontWeight': '500'})
                        ], className='activity-text'),
                        html.Div(
                            (n['body'] or '')[:120] +
                            ('…' if len(n['body'] or '') > 120 else ''),
                            style={'fontSize': '12.5px', 'color': '#4b5563',
                                   'marginTop': '4px', 'fontStyle': 'italic'}
                        ),
                        html.Div(n['created_at'], className='activity-time')
                    ])
                ]
            ))

    activity_panel = html.Div(
        className='panel mb-4',
        style={'flex': '1', 'minWidth': '320px'},
        children=[
            html.Div(className='panel-header',
                     children=[html.Div("Recent Activity", className='panel-title')]),
            html.Div(className='panel-body', children=activity_items)
        ]
    )

    bottom_row = html.Div(
        className='row',
        style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px'},
        children=[
            html.Div(alert_panel,    className='col-lg-5 col-12'),
            html.Div(activity_panel, className='col-lg-5 col-12'),
        ]
    )

    return html.Div([
        reminder_banner,
        html.Div(
            className='page-header',
            children=[html.Div([
                html.H1(f"{cfg.get('agency_name', 'Etherea Labs')} Dashboard",
                        className='page-title'),
                html.P("Pipeline health, revenue trends, and today's priorities.",
                       className='page-subtitle'),
            ])]
        ),
        stat_cards,
        html.Div(className='mb-4', children=[chart_pipeline]),
        charts_row2,
        bottom_row,
    ])
