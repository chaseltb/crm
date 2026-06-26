"""
components/sidebar.py — Persistent left navigation sidebar.
"""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc


NAV_ITEMS = [
    {'label': 'Dashboard',  'icon': 'bi bi-grid-1x2-fill',  'href': '/dashboard'},
    {'label': 'Contacts',   'icon': 'bi bi-people-fill',    'href': '/contacts'},
    {'label': 'Pipeline',   'icon': 'bi bi-funnel-fill',    'href': '/pipeline'},
    {'label': 'Follow-Ups', 'icon': 'bi bi-bell-fill',      'href': '/followups'},
    {'label': 'Settings',   'icon': 'bi bi-gear-fill',      'href': '/settings'},
]


def render_sidebar(config: dict, current_path: str = '/dashboard') -> html.Div:
    agency_name = config.get('agency_name', 'EtherealCRM')
    logo_url = config.get('logo_url', '')

    nav_links = []
    for item in NAV_ITEMS:
        is_active = current_path.startswith(item['href'])
        nav_links.append(
            dcc.Link(
                href=item['href'],
                className=f"nav-link {'active' if is_active else ''}",
                children=[
                    html.I(className=f"{item['icon']} nav-icon"),
                    html.Span(item['label'], className='nav-label'),
                ]
            )
        )

    logo_el = html.Img(
        src=logo_url, id='sidebar-logo', alt=agency_name
    ) if logo_url else html.I(className='bi bi-lightning-fill', style={'fontSize': '22px', 'color': 'var(--color-primary)'})

    return html.Div(
        id='sidebar',
        children=[
            html.Div(
                id='sidebar-header',
                children=[
                    logo_el,
                    html.Span(agency_name, id='sidebar-agency-name'),
                ]
            ),
            html.Nav(id='sidebar-nav', children=nav_links),
            html.Div(
                id='sidebar-footer',
                children=[
                    dcc.Link(
                        href='/logout',
                        className='nav-link',
                        children=[
                            html.I(className='bi bi-box-arrow-right nav-icon'),
                            html.Span('Logout', className='nav-label'),
                        ]
                    )
                ]
            )
        ]
    )
