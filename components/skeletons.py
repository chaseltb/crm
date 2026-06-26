"""
components/skeletons.py — Shimmer skeleton loaders for table and kanban views.
"""

from dash import html


def skeleton_row(cols: int = 7) -> html.Tr:
    return html.Tr([
        html.Td(html.Div(className='skeleton skeleton-text')) for _ in range(cols)
    ])


def skeleton_table(rows: int = 6, cols: int = 7) -> html.Div:
    return html.Div(
        className='skeleton-table-wrap',
        children=[
            html.Table(
                className='table',
                children=[
                    html.Thead(html.Tr([
                        html.Th(html.Div(className='skeleton skeleton-th')) for _ in range(cols)
                    ])),
                    html.Tbody([skeleton_row(cols) for _ in range(rows)])
                ],
                style={'width': '100%'}
            )
        ]
    )


def skeleton_kanban(cols: int = 5, cards_per_col: int = 3) -> html.Div:
    def card():
        return html.Div(
            className='deal-card',
            children=[
                html.Div(className='skeleton skeleton-text skeleton-title mb-2'),
                html.Div(className='skeleton skeleton-text skeleton-sub mb-3'),
                html.Div(className='skeleton skeleton-text skeleton-sub'),
            ],
            style={'marginBottom': '10px'}
        )

    columns = []
    for _ in range(cols):
        columns.append(html.Div(
            className='kanban-column',
            children=[
                html.Div(
                    className='kanban-column-header',
                    children=[
                        html.Div(className='skeleton skeleton-text', style={'width': '80px', 'height': '10px'}),
                        html.Div(className='skeleton', style={'width': '22px', 'height': '18px', 'borderRadius': '999px'}),
                    ]
                ),
                html.Div([card() for _ in range(cards_per_col)], className='kanban-cards')
            ]
        ))

    return html.Div(columns, style={'display': 'flex', 'gap': '14px', 'overflowX': 'auto'})


def skeleton_stat_cards(n: int = 4) -> html.Div:
    return html.Div(
        className='stat-cards-row',
        children=[
            html.Div(
                className='stat-card',
                children=[
                    html.Div(className='skeleton skeleton-text mb-2', style={'width': '60%'}),
                    html.Div(className='skeleton skeleton-text', style={'width': '40%', 'height': '28px'}),
                    html.Div(className='skeleton skeleton-text mt-1', style={'width': '50%', 'height': '10px'}),
                ]
            ) for _ in range(n)
        ]
    )


def empty_state(icon_class: str, title: str, subtitle: str,
                action_label: str = None, action_id: str = None,
                action_href: str = None) -> html.Div:
    """Meaningful empty state with optional primary action."""
    action = None
    if action_label and action_href:
        from dash import dcc
        action = dcc.Link(
            [html.I(className='bi bi-plus-lg me-2'), action_label],
            href=action_href,
            className='btn btn-primary mt-3'
        )
    elif action_label and action_id:
        action = html.Button(
            [html.I(className='bi bi-plus-lg me-2'), action_label],
            id=action_id,
            className='btn-primary mt-3'
        )

    return html.Div(
        className='empty-state',
        children=[
            html.Div(
                html.I(className=icon_class, style={'fontSize': '40px'}),
                className='empty-state-icon'
            ),
            html.Div(title, className='empty-state-title'),
            html.Div(subtitle, className='empty-state-text'),
            action,
        ]
    )
