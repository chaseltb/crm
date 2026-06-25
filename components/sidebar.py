"""
components/sidebar.py — Persistent left navigation sidebar.
Reads agency name and logo URL from config at render time.
"""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc


NAV_ITEMS = [
    {'label': 'Dashboard',  'icon': '📊', 'href': '/dashboard'},
    {'label': 'Contacts',   'icon': '👥', 'href': '/contacts'},
    {'label': 'Pipeline',   'icon': '💼', 'href': '/pipeline'},
    {'label': 'Follow-Ups', 'icon': '🔔', 'href': '/followups'},
    {'label': 'Settings',   'icon': '⚙️',  'href': '/settings'},
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
                    html.Span(item['icon'], className='nav-icon'),
                    html.Span(item['label'], className='nav-label'),
                ]
            )
        )

    logo_el = html.Img(
        src=logo_url, id='sidebar-logo', alt=agency_name
    ) if logo_url else html.Span('⚡', style={'fontSize': '24px', 'color': '#FF120A'})

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
                            html.Span('🚪', className='nav-icon'),
                            html.Span('Logout', className='nav-label'),
                        ]
                    )
                ]
            )
        ]
    )
