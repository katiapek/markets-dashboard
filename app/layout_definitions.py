# layout_definitions.py
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc  # Correct import
from scripts.config import market_tickers
# from data_fetchers import SeasonalDataFetcher

# Define constants for repeated strings, styles, and default values
DEFAULT_MARKET = 'SP 500'
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
INPUT_STYLE = {"margin-right": "10px", "width":"80px"}

def format_market_name(market_name):
    """
    Format the market name to match the expected format used in data fetching functions.

    Args:
        market_name (str): The original market name.

    Returns:
        str: The formatted market name.
    """
    return market_name.upper().replace(' ', '_')


def create_analysis_section():
    """
    Creates the section where users input analysis details and view results with a dark theme.
    Returns:
        html.Div: The layout containing input fields and result placeholders.
    """
    return html.Div(style={'backgroundColor': '#1e1e1e', 'color': 'white', 'fontFamily': "'Press Start 2P', monospace",
                           'fontSize': '10px'},
                    children=[
        # Inputs for the analysis
        html.Div(children=[
            html.Div(children=[
                html.Label("Start Month", style={'margin-bottom': '5px'}),
                dcc.Dropdown(id='start-month',
                             options=[{'label': f'{i}', 'value': i} for i in range(1, 13)],
                             value=1,
                             style={'background-color': '#333', 'color': 'white', 'border-color': '#555'},
                             clearable=False,
                             className='dropdown-menu-1'),  # Disable the clearable option
            ], style={'width': '120px', 'display': 'flex', 'flex-direction': 'column', 'align-items': 'center'}),

            html.Div(children=[
                html.Label("Start Day", style={'margin-bottom': '5px'}),
                dcc.Dropdown(id='start-day',
                             options=[{'label': f'{i}', 'value': i} for i in range(1, 32)],
                             value=1,
                             style={'background-color': '#333', 'color': 'white', 'border-color': '#555'},
                             clearable=False,
                             className='dropdown-menu-1'),  # Disable the clearable option
            ], style={'width': '120px', 'display': 'flex', 'flex-direction': 'column', 'align-items': 'center'}),

            html.Div(children=[
                html.Label("End Month", style={'margin-bottom': '5px'}),
                dcc.Dropdown(id='end-month',
                             options=[{'label': f'{i}', 'value': i} for i in range(1, 13)],
                             value=12,
                             style={'background-color': '#333', 'color': 'white', 'border-color': '#555'},
                             clearable=False,
                             className='dropdown-menu-1'),  # Disable the clearable option
            ], style={'width': '120px', 'display': 'flex', 'flex-direction': 'column', 'align-items': 'center'}),

            html.Div(children=[
                html.Label("End Day", style={'margin-bottom': '5px'}),
                dcc.Dropdown(id='end-day',
                             options=[{'label': f'{i}', 'value': i} for i in range(1, 32)],
                             value=31,
                             style={'background-color': '#333', 'color': 'white', 'border-color': '#555'},
                             clearable=False,
                             className='dropdown-menu-1'),  # Disable the clearable option
            ], style={'width': '120px', 'display': 'flex', 'flex-direction': 'column', 'align-items': 'center'}),

            html.Div(children=[
                html.Label("Direction", style={'margin-bottom': '5px'}),
                dcc.Dropdown(id='direction-dropdown',
                             options=[
                                 {'label': 'Long', 'value': 'Long'},
                                 {'label': 'Short', 'value': 'Short'}
                             ],
                             value='Long',
                             style={'background-color': '#333', 'color': 'white', 'border-color': '#555'},
                             clearable=False,
                             className='dropdown-menu-1'),  # Disable the clearable option
            ], style={'width': '200px', 'display': 'flex', 'flex-direction': 'column', 'align-items': 'center'}),

            html.Div(children=[
                html.Button("Perform Analysis", id='perform-analysis-button', style={
                    'height': '40px', 'margin-top': '18px', 'background-color': '#333', 'color': 'white',
                    'border': '1px solid white'}),
            ], style={'display': 'flex', 'align-items': 'center'})
        ], style={'display': 'flex', 'gap': '15px', 'align-items': 'center'}),

        # Table for Year-by-Year Results
        html.Div(children=[
            html.Label("Yearly Analysis", style={'margin-bottom': '5px'}),
            dash.dash_table.DataTable(id='yearly-analysis-table',
                                      columns=[
                                          {'name': 'Year', 'id': 'Year'},
                                          {'name': 'Max Drawdown (Points)', 'id': 'Max Drawdown (Points)'},
                                          {'name': 'Max Drawdown (%)', 'id': 'Max Drawdown (%)'},
                                          {'name': 'Max Gain (Points)', 'id': 'Max Gain (Points)'},
                                          {'name': 'Max Gain (%)', 'id': 'Max Gain (%)'},
                                          {'name': 'Closing Points', 'id': 'Closing Points'},
                                          {'name': 'Closing Percentage', 'id': 'Closing Percentage'},
                                      ],
                                      data=[],
                                      style_header={'backgroundColor': '#333', 'color': 'white', 'border': '1px solid white',
                                                    'fontFamily': "'Press Start 2P', monospace", 'fontSize': '10px'},
                                      style_cell={'backgroundColor': '#1e1e1e', 'color': 'white', 'border': '1px solid #444',
                                                  'fontFamily': "'Press Start 2P', monospace", 'fontSize': '10px'},
                                      style_table={'overflowX': 'scroll'}
                                      )
        ], style={'padding-top': '15px'}),

        # Summary Statistics for 15 and 30 years
        html.Div(id='15-year-summary', children="15-Year Summary: ",
                 style={'margin-top': '20px', 'font-size': '14px', 'background-color': '#333', 'padding': '10px',
                        'border-radius': '5px', 'fontFamily': "'Press Start 2P', monospace", 'fontSize': '10px'}, ),
        html.Div(id='30-year-summary', children="30-Year Summary: ",
                 style={'margin-top': '20px', 'font-size': '14px', 'background-color': '#333', 'padding': '10px',
                        'border-radius': '5px', 'fontFamily': "'Press Start 2P', monospace", 'fontSize': '10px'}),

        # Container for the distribution charts in a row
        html.Div([
            # Regular distribution chart for 15 years
            html.Div([
                dcc.Graph(id='distribution-chart-15', config={'displayModeBar': False}),
            ], style={'width': '50%', 'display': 'inline-block'}),

            # Optimal distribution chart for 15 years
            html.Div([
                dcc.Graph(id='distribution-chart-optimal-15', config={'displayModeBar': False}),
            ], style={'width': '50%', 'display': 'inline-block'}),
        ], style={'display': 'flex', 'justify-content': 'space-between', 'align-items': 'center'}),

        # Same structure for the 30 years below
        html.Div([
            html.Div([
                dcc.Graph(id='distribution-chart-30', config={'displayModeBar': False}),
            ], style={'width': '50%', 'display': 'inline-block'}),

            html.Div([
                dcc.Graph(id='distribution-chart-optimal-30', config={'displayModeBar': False}),
            ], style={'width': '50%', 'display': 'inline-block'}),
        ], style={'display': 'flex', 'justify-content': 'space-between', 'align-items': 'center'}),


        html.Div([
            # 15-year cumulative returns and metrics
            html.Div([
                dcc.Graph(id='cumulative-return-chart-15'),
                html.Div(id='risk-metrics-summary-15'),
                html.Div(id='risk-metrics-summary-15-stoploss'),
            ], style={'display': 'inline-block', 'width': '48%'}),

            # 30-year cumulative returns and metrics
            html.Div([
                dcc.Graph(id='cumulative-return-chart-30'),
                html.Div(id='risk-metrics-summary-30'),
                html.Div(id='risk-metrics-summary-30-stoploss'),
            ], style={'display': 'inline-block', 'width': '48%'}),
        ])
    ])


def create_layout(app):
    """
    Create and set the layout for the Dash application.

    Args:
        app (dash.Dash): The Dash application instance.
    """
    # Create market links using market_tickers
    market_links = [html.A(name, id={'type': 'market-link', 'index': ticker}, href='#', style={'margin-right': '10px'}) for
                    name, ticker in market_tickers.items()]

    app.layout = html.Div(style={'display': 'flex'}, children=[
        html.Div(
            children=[
                html.Div([
                    html.Button('Prev. Market', id='prev-market-button', n_clicks=0, className='above-chart-button'),
                    html.Button('Next Market', id='next-market-button', n_clicks=0, className='above-chart-button'),
                    html.Button('Prev. Year', id='prev-year-button', n_clicks=0, className='above-chart-button'),
                    html.Button('Next Year', id='next-year-button', n_clicks=0, className='above-chart-button')
                ], style={'display': 'flex', 'justify-content': 'space-between', 'margin-top': '10px', 'gap': '10px'}),

                dcc.Graph(
                    id='combined-chart',
                    config={
                        'scrollZoom': True,
                        'doubleClick': 'reset',
                        'displayModeBar': False,

                    },
                    style={'backgroundColor': '#1e1e1e'}  # Set background color for the graph container
                ),

                # Opportunity analysis section below the main chart
                html.Div(
                    children=[
                        create_analysis_section(),
                        dcc.Loading(
                            id='loading-opportunity',
                            children=[html.Div(id='opportunity-output')],
                            type='default'
                        )
                    ],
                    style={'margin-top': '20px'}
                ),

            ],
            style={'flex': 1, 'padding': '10px', 'overflow': 'hidden'}
        ),



        html.Div(
            id='right-panel',
            children=[
                html.Button('<>', id='toggle-button', n_clicks=0),

                html.Div(
                    className='content',
                    children=[

                        html.Div(
                            children=[
                                dcc.Dropdown(
                                    id='market-dropdown',
                                    options=[{'label': name, 'value': ticker} for name, ticker in
                                             market_tickers.items()],
                                    value=DEFAULT_MARKET,  # Set the default value
                                    placeholder=DEFAULT_MARKET,
                                    clearable=False,  # Optional: prevent clearing
                                    className='dropdown-menu-1',
                                    style={'width': '100%', 'margin-bottom': '10px', 'backgroundColor': '#2b2b2b',
                                           'color': 'white', 'border': 'none'},
                                    searchable=False
                                ),
                                html.Div([
                                    html.Button('Prev. Market', id='prev-market-button', n_clicks=0),
                                    html.Button('Next Market', id='next-market-button', n_clicks=0),
                                ], style={'display': 'flex', 'justify-content': 'space-between', 'margin-top': '10px'}),
                                html.Div([
                                    html.Button('Prev. Year', id='prev-year-button', n_clicks=0),
                                    html.Button('Next Year', id='next-year-button', n_clicks=0)
                                ], style={'display': 'flex', 'justify-content': 'space-between', 'margin-top': '10px'}),
                            ],
                            style={'margin-bottom': '10px'}
                        ),
                        html.Div([
                            html.Button('OHLC & Cycles', id='ohlc-cycles-toggle', n_clicks=0,
                                        style={'width': '100%', 'textAlign': 'left'}),
                            dbc.Collapse(
                                children=[
                                    dcc.Checklist(
                                        id='ohlc-checklist',
                                        options=CHECKLIST_OPTIONS['ohlc'],
                                        value=['OHLC'],
                                        style={'color': '#FFF'},
                                        inputStyle=INPUT_STYLE
                                    ),

                                    dcc.Checklist(
                                        id='years-checklist',
                                        options=CHECKLIST_OPTIONS['years'],
                                        value=DEFAULT_YEARS,
                                        style={'color': '#FFF'},
                                        inputStyle=INPUT_STYLE
                                    ),

                                ],
                                id='ohlc-cycles-collapse',  # Correct ID for collapsible content
                                is_open=True  # Initial state is collapsed
                            )
                        ]),

                        # Foldable "Legacy - Combined" section
                        html.Div([
                            html.Button('Legacy - Combined', id='legacy-combined-toggle', n_clicks=0,
                                        style={'width': '100%', 'textAlign': 'left'}),
                            dbc.Collapse(  # Correct use of dbc.Collapse
                                children=[
                                    dcc.Checklist(
                                        id='open-interest-legacy-combined-checklist',
                                        options=CHECKLIST_OPTIONS['open_interest'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='oi-percentages-legacy-combined-checklist',
                                        options=CHECKLIST_OPTIONS['oi_percentages'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='positions-change-legacy-combined-checklist',
                                        options=CHECKLIST_OPTIONS['positions_change'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='net-positions-legacy-combined-checklist',
                                        options=CHECKLIST_OPTIONS['net_positions'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='net-positions-change-legacy-combined-checklist',
                                        options=CHECKLIST_OPTIONS['net_positions_change'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='26w-index-legacy-combined-checklist',
                                        options=CHECKLIST_OPTIONS['index_26w'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                ],
                                id='legacy-combined-collapse',  # Correct ID for collapsible content
                                is_open=False  # Initial state is collapsed
                            )
                        ]),
                        # Foldable "Legacy - Futures Only" section
                        html.Div([
                            html.Button('Legacy - Futures Only', id='legacy-futures-only-toggle', n_clicks=0,
                                        style={'width': '100%', 'textAlign': 'left'}),
                            dbc.Collapse(  # Correct use of dbc.Collapse
                                children=[
                                    dcc.Checklist(
                                        id='open-interest-legacy-futures-only-checklist',
                                        options=CHECKLIST_OPTIONS['open_interest'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='oi-percentages-legacy-futures-only-checklist',
                                        options=CHECKLIST_OPTIONS['oi_percentages'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='positions-change-legacy-futures-only-checklist',
                                        options=CHECKLIST_OPTIONS['positions_change'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='net-positions-legacy-futures-only-checklist',
                                        options=CHECKLIST_OPTIONS['net_positions'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='net-positions-change-legacy-futures-only-checklist',
                                        options=CHECKLIST_OPTIONS['net_positions_change'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='26w-index-legacy-futures-only-checklist',
                                        options=CHECKLIST_OPTIONS['index_26w'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                ],
                                id='legacy-futures-only-collapse',  # Correct ID for collapsible content
                                is_open=False  # Initial state is collapsed
                            )
                        ]),
                        # Foldable COT Disaggregated Combined
                        html.Div([
                            html.Button('Disaggregated - Combined', id='disaggregated-combined-toggle', n_clicks=0,
                                        style={'width': '100%', 'textAlign': 'left'}),
                            dbc.Collapse(
                                children=[
                                    dcc.Checklist(
                                        id='open-interest-disaggregated-combined-checklist',
                                        options=CHECKLIST_OPTIONS['open_interest'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='oi-percentages-disaggregated-combined-checklist',
                                        options=CHECKLIST_OPTIONS['oi_percentages'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='positions-change-disaggregated-combined-checklist',
                                        options=CHECKLIST_OPTIONS['positions_change'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='net-positions-disaggregated-combined-checklist',
                                        options=CHECKLIST_OPTIONS['net_positions'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='net-positions-change-disaggregated-combined-checklist',
                                        options=CHECKLIST_OPTIONS['net_positions_change'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='26w-index-disaggregated-combined-checklist',
                                        options=CHECKLIST_OPTIONS['index_26w'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),

                                ],
                                id='disaggregated-combined-collapse',
                                is_open=False
                            )
                        ]),
                        # Foldable COT Disaggregated Futures Only
                        html.Div([
                            html.Button('Disaggregated - Futures Only', id='disaggregated-futures-only-toggle', n_clicks=0,
                                        style={'width': '100%', 'textAlign': 'left'}),
                            dbc.Collapse(
                                children=[
                                    dcc.Checklist(
                                        id='open-interest-disaggregated-futures-only-checklist',
                                        options=CHECKLIST_OPTIONS['open_interest'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='oi-percentages-disaggregated-futures-only-checklist',
                                        options=CHECKLIST_OPTIONS['oi_percentages'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='positions-change-disaggregated-futures-only-checklist',
                                        options=CHECKLIST_OPTIONS['positions_change'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='net-positions-disaggregated-futures-only-checklist',
                                        options=CHECKLIST_OPTIONS['net_positions'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='net-positions-change-disaggregated-futures-only-checklist',
                                        options=CHECKLIST_OPTIONS['net_positions_change'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='26w-index-disaggregated-futures-only-checklist',
                                        options=CHECKLIST_OPTIONS['index_26w'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),

                                ],
                                id='disaggregated-futures-only-collapse',
                                is_open=False
                            )
                        ]),
                        # Foldable COT TFF Combined
                        html.Div([
                            html.Button('TFF - Combined', id='tff-combined-toggle', n_clicks=0,
                                        style={'width': '100%', 'textAlign': 'left'}),
                            dbc.Collapse(
                                children=[
                                    dcc.Checklist(
                                        id='open-interest-tff-combined-checklist',
                                        options=CHECKLIST_OPTIONS['open_interest'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='oi-percentages-tff-combined-checklist',
                                        options=CHECKLIST_OPTIONS['oi_percentages'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='positions-change-tff-combined-checklist',
                                        options=CHECKLIST_OPTIONS['positions_change'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='net-positions-tff-combined-checklist',
                                        options=CHECKLIST_OPTIONS['net_positions'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='net-positions-change-tff-combined-checklist',
                                        options=CHECKLIST_OPTIONS['net_positions_change'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='26w-index-tff-combined-checklist',
                                        options=CHECKLIST_OPTIONS['index_26w'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),

                                ],
                                id='tff-combined-collapse',
                                is_open=False
                            )
                        ]),
                        # Foldable COT TFF Futures Only
                        html.Div([
                            html.Button('TFF - Futures Only', id='tff-futures-only-toggle',
                                        n_clicks=0,
                                        style={'width': '100%', 'textAlign': 'left'}),
                            dbc.Collapse(
                                children=[
                                    dcc.Checklist(
                                        id='open-interest-tff-futures-only-checklist',
                                        options=CHECKLIST_OPTIONS['open_interest'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='oi-percentages-tff-futures-only-checklist',
                                        options=CHECKLIST_OPTIONS['oi_percentages'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='positions-change-tff-futures-only-checklist',
                                        options=CHECKLIST_OPTIONS['positions_change'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='net-positions-tff-futures-only-checklist',
                                        options=CHECKLIST_OPTIONS['net_positions'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='net-positions-change-tff-futures-only-checklist',
                                        options=CHECKLIST_OPTIONS['net_positions_change'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),
                                    dcc.Checklist(
                                        id='26w-index-tff-futures-only-checklist',
                                        options=CHECKLIST_OPTIONS['index_26w'],
                                        value=[],
                                        inputStyle=INPUT_STYLE
                                    ),

                                ],
                                id='tff-futures-only-collapse',
                                is_open=False
                            )
                        ]),


                        html.Div([
                            # html.Button('Previous Year', id='prev-year-button', n_clicks=0),
                            # html.Button('Next Year', id='next-year-button', n_clicks=0)
                        ], style={'display': 'flex', 'justify-content': 'space-between', 'margin-top': '10px'}),
                        dcc.Store(id='current-year', data=2024),
                        dcc.Store(id='stored-market', data=DEFAULT_MARKET),
                        dcc.Store(id='stored-market', data=DEFAULT_MARKET),
                        dcc.Store(id='active-subplots', data=[]),  # Track active subplots dynamically
                    ]
                ),

            ],
        ),

    ])
