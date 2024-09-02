import dash
from dash import dcc, html
import dash_bootstrap_components as dbc  # Correct import
from scripts.config import market_tickers
from data_fetchers import SeasonalDataFetcher

# Define constants for repeated strings, styles, and default values
DEFAULT_MARKET = 'Australian Dollar'
DEFAULT_YEARS = [15, 35]

CHECKLIST_OPTIONS = {
    'years': [
        {'label': '15 Years', 'value': 15},
        {'label': '35 Years', 'value': 35}
    ],
    'ohlc': [
        {'label': 'Show OHLC', 'value': 'OHLC'}
    ],
    'open_interest': [
        {'label': 'Show Open Interest', 'value': 'Open Interest'}
    ],
    'oi_percentages': [
        {'label': 'Show % of OI', 'value': 'OI Percentages'}
    ],
    'positions_change': [
        {'label': 'Show % Change in Positions', 'value': 'Positions Change'}
    ],
    'net_positions': [
        {'label': 'Show Net Positions', 'value': 'Net Positions'}
    ],
    'net_positions_change': [
        {'label': 'Show % Change in Net Positions', 'value': 'Net Positions Change'}
    ],
    'index_26w': [
        {'label': 'Show 26-Week Index', 'value': '26W Index'}
    ]
}

BUTTON_STYLES = {'margin-bottom': '3px'}
CHECKLIST_STYLES = {'margin-bottom': '10px'}
LAYOUT_STYLES = {'display': 'flex'}
GRAPH_STYLES = {'flex': 1, 'padding': '10px', 'overflow': 'hidden'}

def format_market_name(market_name):
    """
    Format the market name to match the expected format used in data fetching functions.

    Args:
        market_name (str): The original market name.

    Returns:
        str: The formatted market name.
    """
    return market_name.upper().replace(' ', '_')

def create_layout(app):
    """
    Create and set the layout for the Dash application.

    Args:
        app (dash.Dash): The Dash application instance.
    """
    # Create market links using market_tickers
    market_links = [html.A(name, id={'type': 'market-link', 'index': ticker}, href='#', style={'margin-right': '10px'}) for
                    name, ticker in market_tickers.items()]

    app.layout = html.Div(style=LAYOUT_STYLES, children=[
        html.Div(
            children=[
                dcc.Graph(id='combined-chart'),
            ],
            style=GRAPH_STYLES
        ),
        html.Div(
            id='right-panel',
            children=[
                html.Button('<>', id='toggle-button', n_clicks=0),
                html.Div(
                    className='content',
                    children=[
                        html.Div(
                            children=[html.Div(market_link, style=BUTTON_STYLES) for market_link in
                                      market_links],
                            style={'display': 'flex', 'flexDirection': 'column', 'margin-bottom': '10px'}
                        ),
                        dcc.Checklist(
                            id='years-checklist',
                            options=CHECKLIST_OPTIONS['years'],
                            value=DEFAULT_YEARS
                        ),
                        dcc.Checklist(
                            id='ohlc-checklist',
                            options=CHECKLIST_OPTIONS['ohlc'],
                            value=['OHLC']
                        ),
                        # Foldable "Legacy - Combined" section
                        html.Div([
                            html.Button('Legacy - Combined', id='legacy-combined-toggle', n_clicks=0,
                                        style={'width': '100%', 'textAlign': 'left'}),
                            dbc.Collapse(  # Correct use of dbc.Collapse
                                children=[
                                    dcc.Checklist(
                                        id='open-interest-checklist',
                                        options=CHECKLIST_OPTIONS['open_interest'],
                                        value=[]
                                    ),
                                    dcc.Checklist(
                                        id='oi-percentages-checklist',
                                        options=CHECKLIST_OPTIONS['oi_percentages'],
                                        value=[]
                                    ),
                                    dcc.Checklist(
                                        id='positions-change-checklist',
                                        options=CHECKLIST_OPTIONS['positions_change'],
                                        value=[]
                                    ),
                                    dcc.Checklist(
                                        id='net-positions-checklist',
                                        options=CHECKLIST_OPTIONS['net_positions'],
                                        value=[]
                                    ),
                                    dcc.Checklist(
                                        id='net-positions-change-checklist',
                                        options=CHECKLIST_OPTIONS['net_positions_change'],
                                        value=[]
                                    ),
                                    dcc.Checklist(
                                        id='26w-index-checklist',
                                        options=CHECKLIST_OPTIONS['index_26w'],
                                        value=[]
                                    ),
                                ],
                                id='legacy-combined-collapse',  # Correct ID for collapsible content
                                is_open=False  # Initial state is collapsed
                            )
                        ]),
                        html.Div([
                            html.Button('Previous Year', id='prev-year-button', n_clicks=0),
                            html.Button('Next Year', id='next-year-button', n_clicks=0)
                        ]),
                        dcc.Store(id='current-year', data=2024),
                        dcc.Store(id='stored-market', data=DEFAULT_MARKET),
                        dcc.Store(id='active-subplots', data=[]),  # Track active subplots dynamically
                    ]
                ),
            ],
        )
    ])
