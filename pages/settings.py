"""
pages/settings.py — Settings & White-labeling configuration page for EtherealCRM.
Reads/writes config.yaml and provides a live branding preview.
"""

import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import yaml
import os

dash.register_page(__name__, path='/settings')

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')

def load_config() -> dict:
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def save_config(cfg: dict):
    with open(CONFIG_PATH, 'w') as f:
        yaml.safe_dump(cfg, f, default_flow_style=False, sort_keys=False)

# ── Page Layout ───────────────────────────────────────────────────────────────

def layout():
    cfg = load_config()
    
    # Pre-format lists as new-line separated strings for editing
    stages_str = "\n".join(cfg.get('deal_stages', []))
    services_str = "\n".join(cfg.get('service_types', []))
    sources_str = "\n".join(cfg.get('lead_sources', []))
    emails_str = "\n".join(cfg.get('allowed_emails', []))

    # Field helpers
    def form_input(label, fid, val, typ='text'):
        return html.Div(
            className='form-group mb-3',
            children=[
                html.Label(label, className='form-label'),
                dcc.Input(id=fid, type=typ, value=val, className='form-control')
            ]
        )

    def form_textarea(label, fid, val, help_text):
        return html.Div(
            className='form-group mb-3',
            children=[
                html.Label(label, className='form-label'),
                dcc.Textarea(
                    id=fid, value=val, className='form-control',
                    style={'height': '120px', 'fontFamily': 'monospace'}
                ),
                html.Small(help_text, style={'color': '#8890a0', 'marginTop': '4px', 'display': 'block'})
            ]
        )

    return html.Div([
        dcc.Store(id='settings-save-status', data=0),

        html.Div(
            className='page-header',
            children=[
                html.Div([
                    html.H1("System Settings", className='page-title'),
                    html.P("Configure white-labeling, brand colors, stages, and access lists.", className='page-subtitle'),
                ]),
                html.Button("💾 Save Configuration", id='save-settings-btn', className='btn-primary')
            ]
        ),

        # Alert banner for save confirmation
        html.Div(id='settings-alert-container'),

        html.Div(
            className='row',
            children=[
                # Column 1: Config Fields
                html.Div([
                    # White-label details
                    html.Div(
                        className='settings-section',
                        children=[
                            html.Div("Agency & Branding White-Labeling", className='settings-section-header'),
                            html.Div(
                                className='settings-section-body',
                                children=[
                                    form_input("Agency Name", "s-agency-name", cfg.get('agency_name', '')),
                                    form_input("Logo Image CDN URL", "s-logo-url", cfg.get('logo_url', '')),
                                    form_input("Currency Symbol", "s-currency", cfg.get('currency_symbol', '$')),
                                    form_input("Follow-up Warning threshold (days)", "s-warning-days", cfg.get('follow_up_warning_days', 3), typ='number'),
                                ]
                            )
                        ]
                    ),
                    
                    # Colors Configuration
                    html.Div(
                        className='settings-section',
                        children=[
                            html.Div("Brand Theme Colors (HEX)", className='settings-section-header'),
                            html.Div(
                                className='settings-section-body',
                                children=[
                                    html.Div([
                                        html.Div(form_input("Primary Red (accent/CTAs)", "s-c-primary", cfg.get('color_primary', '')), style={'flex': 1}),
                                        html.Div(form_input("Primary Hover Color", "s-c-primary-hover", cfg.get('color_primary_hover', '')), style={'flex': 1}),
                                    ], style={'display': 'flex', 'gap': '12px'}),
                                    html.Div([
                                        html.Div(form_input("Primary Deep Color", "s-c-primary-deep", cfg.get('color_primary_deep', '')), style={'flex': 1}),
                                        html.Div(form_input("Sidebar Background", "s-c-bg-dark", cfg.get('color_bg_dark', '')), style={'flex': 1}),
                                    ], style={'display': 'flex', 'gap': '12px'}),
                                    html.Div([
                                        html.Div(form_input("Body Text Color", "s-c-text-body", cfg.get('color_text_body', '')), style={'flex': 1}),
                                        html.Div(form_input("Light Panel Backgrounds", "s-c-text-light", cfg.get('color_text_light', '')), style={'flex': 1}),
                                    ], style={'display': 'flex', 'gap': '12px'}),
                                ]
                            )
                        ]
                    ),

                    # Whitelist Auth
                    html.Div(
                        className='settings-section',
                        children=[
                            html.Div("Authentication Whitelist", className='settings-section-header'),
                            html.Div(
                                className='settings-section-body',
                                children=[
                                    form_textarea("Allowed Email Whitelist", "s-emails", emails_str, "One email per line. Users must have their email in this list to login.")
                                ]
                            )
                        ]
                    )
                ], className='col-lg-7 col-12'),

                # Column 2: Lists config & Live Preview
                html.Div([
                    # Live Preview
                    html.Div(
                        className='settings-section mb-4',
                        children=[
                            html.Div("Live Brand Theme Preview", className='settings-section-header'),
                            html.Div(
                                className='settings-section-body',
                                children=[
                                    html.Div([
                                        # Fake Sidebar Preview
                                        html.Div(
                                            id='p-sidebar',
                                            children=[
                                                html.Div(cfg.get('agency_name', 'Agency'), id='p-sidebar-text', style={'color': '#fff', 'fontWeight': 'bold', 'padding': '12px', 'borderBottom': '1px solid rgba(255,255,255,0.1)'}),
                                                html.Div("📊 Dashboard", id='p-sidebar-link', style={'padding': '10px 12px', 'fontSize': '12.5px', 'color': '#fff', 'marginTop': '10px'})
                                            ],
                                            style={'width': '140px', 'height': '140px', 'backgroundColor': cfg.get('color_bg_dark'), 'borderRadius': '6px', 'overflow': 'hidden', 'float': 'left', 'marginRight': '20px'}
                                        ),
                                        # Fake Content area
                                        html.Div([
                                            html.Button("Primary CTA", id='p-btn', className='btn-primary', style={'backgroundColor': cfg.get('color_primary'), 'border': 'none', 'color': '#fff'}),
                                            html.Br(), html.Br(),
                                            html.Span("Demo Tag Badge", id='p-tag', className='tag', style={'backgroundColor': '#fee2e2', 'color': cfg.get('color_primary')})
                                        ], style={'overflow': 'hidden'})
                                    ], style={'display': 'flex', 'alignItems': 'center'})
                                ]
                            )
                        ]
                    ),

                    # Custom Lists configuration
                    html.Div(
                        className='settings-section',
                        children=[
                            html.Div("System List Values", className='settings-section-header'),
                            html.Div(
                                className='settings-section-body',
                                children=[
                                    form_textarea("Deal Stages", "s-stages", stages_str, "One stage per line. Changing these does not rename stages on existing deals."),
                                    form_textarea("Service Types", "s-services", services_str, "One type per line."),
                                    form_textarea("Lead Sources", "s-sources", sources_str, "One source per line.")
                                ]
                            )
                        ]
                    )
                ], className='col-lg-5 col-12')
            ],
            style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px'}
        )
    ])


# ── Callbacks ─────────────────────────────────────────────────────────────────

# Live updates to preview panel when color pickers / inputs change
@callback(
    Output('p-sidebar', 'style'),
    Output('p-sidebar-link', 'style'),
    Output('p-sidebar-text', 'innerHTML'),
    Output('p-btn', 'style'),
    Output('p-tag', 'style'),
    Input('s-agency-name', 'value'),
    Input('s-c-primary', 'value'),
    Input('s-c-bg-dark', 'value'),
    prevent_initial_call=True
)
def update_branding_preview(agency, primary, bg_dark):
    sidebar_style = {'width': '140px', 'height': '140px', 'backgroundColor': bg_dark or '#370E08', 'borderRadius': '6px', 'overflow': 'hidden', 'float': 'left', 'marginRight': '20px'}
    sidebar_link_style = {'padding': '10px 12px', 'fontSize': '12.5px', 'backgroundColor': primary or '#FF120A', 'color': '#fff', 'marginTop': '10px'}
    btn_style = {'backgroundColor': primary or '#FF120A', 'border': 'none', 'color': '#fff'}
    tag_style = {'backgroundColor': '#fee2e2', 'color': primary or '#FF120A'}
    
    return sidebar_style, sidebar_link_style, agency or 'Agency', btn_style, tag_style


# Save configuration values back to config.yaml file
@callback(
    Output('settings-alert-container', 'children'),
    Input('save-settings-btn', 'n_clicks'),
    State('s-agency-name', 'value'),
    State('s-logo-url', 'value'),
    State('s-currency', 'value'),
    State('s-warning-days', 'value'),
    State('s-c-primary', 'value'),
    State('s-c-primary-hover', 'value'),
    State('s-c-primary-deep', 'value'),
    State('s-c-bg-dark', 'value'),
    State('s-c-text-body', 'value'),
    State('s-c-text-light', 'value'),
    State('s-emails', 'value'),
    State('s-stages', 'value'),
    State('s-services', 'value'),
    State('s-sources', 'value'),
    prevent_initial_call=True
)
def save_settings(n_clicks, agency, logo, currency, warning, primary, hover, deep, bg_dark, text_body, text_light, emails, stages, services, sources):
    if not n_clicks:
        return no_update
        
    try:
        # Load active config first
        cfg = load_config()
        
        # Parse textareas back into lists
        emails_list = [e.strip() for e in emails.split("\n") if e.strip()]
        stages_list = [s.strip() for s in stages.split("\n") if s.strip()]
        services_list = [s.strip() for s in services.split("\n") if s.strip()]
        sources_list = [s.strip() for s in sources.split("\n") if s.strip()]
        
        cfg['agency_name'] = agency
        cfg['logo_url'] = logo
        cfg['currency_symbol'] = currency
        cfg['follow_up_warning_days'] = int(warning)
        cfg['color_primary'] = primary
        cfg['color_primary_hover'] = hover
        cfg['color_primary_deep'] = deep
        cfg['color_bg_dark'] = bg_dark
        cfg['color_text_body'] = text_body
        cfg['color_text_light'] = text_light
        cfg['allowed_emails'] = emails_list
        cfg['deal_stages'] = stages_list
        cfg['service_types'] = services_list
        cfg['lead_sources'] = sources_list
        
        # Save back to config.yaml
        save_config(cfg)
        
        return html.Div(
            className='alert-banner success',
            children="✓ Settings saved successfully. Changes will take effect on next reload / page click."
        )
        
    except Exception as e:
        return html.Div(
            className='alert-banner danger',
            children=f"Error saving config file: {str(e)}"
        )
