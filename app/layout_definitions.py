# layout_definitions.py
import dash
from dash import dcc, html
from scripts.config import market_tickers
from data_fetchers import SeasonalDataFetcher

def format_market_name(market_name):
    """
    Format the market name to match the expected format used in data fetching functions.

    Args:
        market_name (str): The original market name.

    Returns:
        str: The formatted market name.
    """
    formatted_name = market_name.upper().replace(' ', '_')
    return formatted_name

def create_layout(app):
    # Create market links using market_tickers
    market_links = [html.A(name, id={'type': 'market-link', 'index': ticker}, href='#', style={'margin-right': '10px'}) for
                    name, ticker in market_tickers.items()]

    # Define default market and years
    default_market = 'Australian Dollar'
    default_years = [15, 35]

    app.layout = html.Div(style={'display': 'flex'}, children=[
        html.Div(
            children=[
                dcc.Graph(id='combined-chart'),
            ],
            style={'flex': 1, 'padding': '10px', 'overflow': 'hidden'}
        ),
        html.Div(
            id='right-panel',
            children=[
                html.Button('>>', id='toggle-button', n_clicks=0),
                html.Div(
                    className='content',
                    children=[
                        html.Div(
                            children=[html.Div(market_link, style={'margin-bottom': '3px'}) for market_link in
                                      market_links],
                            style={'display': 'flex', 'flexDirection': 'column', 'margin-bottom': '10px'}
                        ),
                        dcc.Checklist(
                            id='years-checklist',
                            options=[
                                {'label': '15 Years', 'value': 15},
                                {'label': '35 Years', 'value': 35}
                            ],
                            value=default_years
                        ),
                        dcc.Checklist(
                            id='ohlc-checklist',
                            options=[
                                {'label': 'Show OHLC', 'value': 'OHLC'}
                            ],
                            value=['OHLC']
                        ),
                        dcc.Checklist(
                            id='open-interest-checklist',
                            options=[
                                {'label': 'Show Open Interest', 'value': 'Open Interest'}
                            ],
                            value=[]  # Default to not show Open Interest
                        ),
                        dcc.Checklist(
                            id='oi-percentages-checklist',
                            options=[
                                {'label': 'Show % of OI', 'value': 'OI Percentages'}
                            ],
                            value=[]  # Default to not show % of OI
                        ),
                        dcc.Checklist(
                            id='positions-change-checklist',
                            options=[
                                {'label': 'Show % Change in Positions', 'value': 'Positions Change'}
                            ],
                            value=[]  # Default to not show % Change in Positions
                        ),
                        dcc.Checklist(
                            id='net-positions-checklist',
                            options=[
                                {'label': 'Show Net Positions', 'value': 'Net Positions'}
                            ],
                            value=[]  # Default to not show Net Positions
                        ),
                        dcc.Checklist(
                            id='net-positions-change-checklist',
                            options=[
                                {'label': 'Show % Change in Net Positions', 'value': 'Net Positions Change'}
                            ],
                            value=[]  # Default to not show % Change in Net Positions
                        ),
                        dcc.Checklist(
                            id='26w-index-checklist',
                            options=[
                                {'label': 'Show 26-Week Index', 'value': '26W Index'}
                            ],
                            value=[]  # Default to not show 26-Week Index
                        ),
                        html.Div([
                            html.Button('Previous Year', id='prev-year-button', n_clicks=0),
                            html.Button('Next Year', id='next-year-button', n_clicks=0)
                        ]),
                        dcc.Store(id='current-year', data=2024),
                        dcc.Store(id='stored-market', data=default_market),
                    ]
                ),
            ],
        )
    ])
