# layout_definitions.py
import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc  # Correct import
from scripts.config import market_tickers
# from data_fetchers import SeasonalDataFetcher

# Define constants for repeated strings, styles, and default values
DEFAULT_MARKET = 'SP 500'
DEFAULT_YEARS = [15, 35]
DEFAULT_DIRECTION = 'Long'

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
INPUT_STYLE = {"margin-right": "10px", "width":"40px"}

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
            # Date range picker for selecting start and end dates
            html.Div(children=[
                html.Label("Select Date Range", style={'margin-bottom': '5px'}),
                dcc.DatePickerRange(
                    id='date-picker-range',
                    start_date_placeholder_text="Start Period",
                    end_date_placeholder_text="End Period",
                    display_format='MMM-DD',
                    month_format='MMMM',
                    min_date_allowed='2024-01-01',
                    max_date_allowed='2024-12-31',
                    start_date='2024-01-01',  # Default to None or a specific start date
                    end_date='2024-12-31',  # Default to None or a specific end date
                    clearable=False,
                    # day_size=20
                )
            ], style={'width': '400px', 'display': 'flex', 'flex-direction': 'column', 'align-items': 'center'}),

            html.Div(children=[
                html.Label("Direction", style={'margin-bottom': '5px'}),
                dcc.Dropdown(
                    id='direction-dropdown',
                    options=[
                        {'label': 'Long', 'value': 'Long'},
                        {'label': 'Short', 'value': 'Short'}
                    ],
                    value=DEFAULT_DIRECTION,  # Default value
                    placeholder=DEFAULT_DIRECTION,
                    style={'background-color': '#333', 'color': 'white', 'border-color': '#555'},
                    clearable=False,
                    className='dropdown-menu-direction',
                    searchable=False,
                ),
            ], style={'width': '200px', 'display': 'flex', 'flex-direction': 'column', 'align-items': 'center'}),

            html.Div(children=[
                dcc.Interval(
                    id='interval-auto-load',
                    interval=1 * 1000,  # 1 second delay
                    n_intervals=0,  # Starts immediately on page load
                    max_intervals=1  # Only fires once
                ),

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

def create_day_trading_stats_section():
    """
    Creates the Day Trading Stats section of the app.
    Returns:
        html.Div: The layout containing the day trading stats table.
    """
    return html.Div(style={'backgroundColor': '#1e1e1e', 'color': 'white',
                           'fontFamily': "'Press Start 2P', monospace", 'fontSize': '10px'},
                    children=[
        html.H3("Day Trading Stats", style={'textAlign': 'center'}),
        dash.dash_table.DataTable(
            id='day-trading-stats-table',
            columns=[
                {'name': 'Year', 'id': 'Year'},
                {'name': 'Total Days', 'id': 'Total Days'},
                {'name': 'D UP', 'id': 'D UP'},
                {'name': 'D UP %', 'id': 'D UP %'},
                {'name': 'D DN', 'id': 'D DN'},
                {'name': 'D DN %', 'id': 'D DN %'},
                {'name': 'PD-H', 'id': 'PD-H'},
                {'name': 'PD-H %', 'id': 'PD-H %'},
                {'name': 'PD-L', 'id': 'PD-L'},
                {'name': 'PD-L %', 'id': 'PD-L %'},
                {'name': 'PD-HL', 'id': 'PD-HL'},
                {'name': 'PD-HL %', 'id': 'PD-HL %'},
                {'name': 'PD-nHL', 'id': 'PD-nHL'},
                {'name': 'PD-nHL %', 'id': 'PD-nHL %'},
            ],
            data=[],
            style_header={
                'backgroundColor': '#333',
                'color': 'white',
                'border': '1px solid white',
                'fontFamily': "'Press Start 2P', monospace",
                'fontSize': '10px'
            },
            style_cell={
                'backgroundColor': '#1e1e1e',
                'color': 'white',
                'border': '1px solid #444',
                'fontFamily': "'Press Start 2P', monospace",
                'fontSize': '10px',
                'textAlign': 'center'
            },
            style_table={'overflowX': 'scroll'}
        )
    ])


def create_day_trading_stats_weekday_section():
    """
    Creates the Day Trading Stats section of the app.
    Returns:
        html.Div: The layout containing the day trading stats table.
    """
    return html.Div(style={'backgroundColor': '#1e1e1e', 'color': 'white',
                           'fontFamily': "'Press Start 2P', monospace", 'fontSize': '10px'},
                    children=[
        html.H3("Day Trading Stats Weekdays", style={'textAlign': 'center'}),
        dash.dash_table.DataTable(
            id='day-trading-stats-weekday-table',
            columns=[
                {'name': 'Weekday', 'id': 'Weekday'},
                {'name': 'Total Days', 'id': 'Total Days'},
                {'name': 'D UP', 'id': 'D UP'},
                {'name': 'D UP %', 'id': 'D UP %'},
                {'name': 'D DN', 'id': 'D DN'},
                {'name': 'D DN %', 'id': 'D DN %'},
                {'name': 'PD-H', 'id': 'PD-H'},
                {'name': 'PD-H %', 'id': 'PD-H %'},
                {'name': 'PD-L', 'id': 'PD-L'},
                {'name': 'PD-L %', 'id': 'PD-L %'},
                {'name': 'PD-HL', 'id': 'PD-HL'},
                {'name': 'PD-HL %', 'id': 'PD-HL %'},
                {'name': 'PD-nHL', 'id': 'PD-nHL'},
                {'name': 'PD-nHL %', 'id': 'PD-nHL %'},
            ],
            data=[],
            style_header={
                'backgroundColor': '#333',
                'color': 'white',
                'border': '1px solid white',
                'fontFamily': "'Press Start 2P', monospace",
                'fontSize': '10px'
            },
            style_cell={
                'backgroundColor': '#1e1e1e',
                'color': 'white',
                'border': '1px solid #444',
                'fontFamily': "'Press Start 2P', monospace",
                'fontSize': '10px',
                'textAlign': 'center'
            },
            style_table={'overflowX': 'scroll'}
        )
    ])


def create_day_trading_stats_1_section():
    """
    Creates the Day Trading Stats section of the app.
    Returns:
        html.Div: The layout containing the day trading stats table.
    """
    return html.Div(style={'backgroundColor': '#1e1e1e', 'color': 'white',
                           'fontFamily': "'Press Start 2P', monospace", 'fontSize': '10px'},
                    children=[
        html.H3("Day Trading Stats - continuation", style={'textAlign': 'center'}),
        dash.dash_table.DataTable(
            id='day-trading-stats-1-table',

            columns=[
                {'name': 'Year', 'id': 'Year'},
                {'name': 'Total Days', 'id': 'Total Days'},
                {'name': 'CaPD-H', 'id': 'CaPD-H'},
                {'name': 'CaPD-H %', 'id': 'CaPD-H %'},
                {'name': 'CbPD-L', 'id': 'CbPD-L'},
                {'name': 'CbPD-L %', 'id': 'CbPD-L %'},
                {'name': 'CaPD-HL', 'id': 'CaPD-HL'},
                {'name': 'CaPD-HL %', 'id': 'CaPD-HL %'},
                {'name': 'CbPD-HL', 'id': 'CbPD-HL'},
                {'name': 'CbPD-HL %', 'id': 'CbPD-HL %'},
                {'name': 'BISI', 'id': 'BISI'},
                {'name': 'BISI %', 'id': 'BISI %'},
                {'name': 'SIBI', 'id': 'SIBI'},
                {'name': 'SIBI %', 'id': 'SIBI %'},
            ],
            data=[],
            style_header={
                'backgroundColor': '#333',
                'color': 'white',
                'border': '1px solid white',
                'fontFamily': "'Press Start 2P', monospace",
                'fontSize': '10px'
            },
            style_cell={
                'backgroundColor': '#1e1e1e',
                'color': 'white',
                'border': '1px solid #444',
                'fontFamily': "'Press Start 2P', monospace",
                'fontSize': '10px',
                'textAlign': 'center'
            },
            style_table={'overflowX': 'scroll'}
        )
    ])


def create_day_trading_stats_1_weekday_section():
    """
    Creates the Day Trading Stats section of the app.
    Returns:
        html.Div: The layout containing the day trading stats table.
    """
    return html.Div(style={'backgroundColor': '#1e1e1e', 'color': 'white',
                           'fontFamily': "'Press Start 2P', monospace", 'fontSize': '10px'},
                    children=[
        html.H3("Day Trading Stats - continuation - Weekday", style={'textAlign': 'center'}),
        dash.dash_table.DataTable(
            id='day-trading-stats-1-weekday-table',

            columns=[
                {'name': 'Weekday', 'id': 'Weekday'},
                {'name': 'Total Days', 'id': 'Total Days'},
                {'name': 'CaPD-H', 'id': 'CaPD-H'},
                {'name': 'CaPD-H %', 'id': 'CaPD-H %'},
                {'name': 'CbPD-L', 'id': 'CbPD-L'},
                {'name': 'CbPD-L %', 'id': 'CbPD-L %'},
                {'name': 'CaPD-HL', 'id': 'CaPD-HL'},
                {'name': 'CaPD-HL %', 'id': 'CaPD-HL %'},
                {'name': 'CbPD-HL', 'id': 'CbPD-HL'},
                {'name': 'CbPD-HL %', 'id': 'CbPD-HL %'},
                {'name': 'BISI', 'id': 'BISI'},
                {'name': 'BISI %', 'id': 'BISI %'},
                {'name': 'SIBI', 'id': 'SIBI'},
                {'name': 'SIBI %', 'id': 'SIBI %'},
            ],
            data=[],
            style_header={
                'backgroundColor': '#333',
                'color': 'white',
                'border': '1px solid white',
                'fontFamily': "'Press Start 2P', monospace",
                'fontSize': '10px'
            },
            style_cell={
                'backgroundColor': '#1e1e1e',
                'color': 'white',
                'border': '1px solid #444',
                'fontFamily': "'Press Start 2P', monospace",
                'fontSize': '10px',
                'textAlign': 'center'
            },
            style_table={'overflowX': 'scroll'}
        )
    ])


def create_pdh_analysis_section():
    """
    Creates a section for PD-H day analysis including distributions and scatter plots.

    Returns:
        html.Div: The layout containing input fields and result placeholders for PD-H day analysis.
    """
    return html.Div(style={'backgroundColor': '#1e1e1e', 'color': 'white',
                           'fontFamily': "'Press Start 2P', monospace", 'fontSize': '10px'},
                    children=[
        html.H3("PD-H Day Analysis", style={'textAlign': 'center'}),

        # Distribution Plots
        html.Div([
            html.Div([
                dcc.Graph(id='pdh-open-high-dist'),
            ], style={'width': '50%', 'display': 'inline-block'}),

            html.Div([
                dcc.Graph(id='pdh-open-low-dist'),
            ], style={'width': '50%', 'display': 'inline-block'}),
        ], style={'display': 'flex'}),

        # High vs Previous High Distribution
        html.Div([
            html.Div([
                dcc.Graph(id='pdh-open-close-dist'),
            ], style={'width': '50%', 'display': 'inline-block'}),

            html.Div([
                dcc.Graph(id='pdh-high-vs-prev-high-dist'),
            ], style={'width': '50%', 'display': 'inline-block'}),

        ]),

        # Scatter Plots
        html.Div([
            html.Div([
                dcc.Graph(id='pdh-open-low-vs-close-scatter'),
            ], style={'width': '50%', 'display': 'inline-block'}),

            html.Div([
                dcc.Graph(id='pdh-open-low-vs-high-scatter'),
            ], style={'width': '50%', 'display': 'inline-block'}),

        ], style={'display': 'flex'}),

    ])

def create_pdl_analysis_section():
    """
    Creates a section for PD-H day analysis including distributions and scatter plots.

    Returns:
        html.Div: The layout containing input fields and result placeholders for PD-H day analysis.
    """
    return html.Div(style={'backgroundColor': '#1e1e1e', 'color': 'white',
                           'fontFamily': "'Press Start 2P', monospace", 'fontSize': '10px'},
                    children=[
        html.H3("PD-L Day Analysis", style={'textAlign': 'center'}),

        # Distribution Plots
        html.Div([
            html.Div([
                dcc.Graph(id='pdl-open-high-dist'),
            ], style={'width': '50%', 'display': 'inline-block'}),

            html.Div([
                dcc.Graph(id='pdl-open-low-dist'),
            ], style={'width': '50%', 'display': 'inline-block'}),
        ], style={'display': 'flex'}),

        # High vs Previous High Distribution
        html.Div([
            html.Div([
                dcc.Graph(id='pdl-open-close-dist'),
            ], style={'width': '50%', 'display': 'inline-block'}),

            html.Div([
                dcc.Graph(id='pdl-low-vs-prev-low-dist'),
            ], style={'width': '50%', 'display': 'inline-block'}),

        ]),

        # Scatter Plots
        html.Div([
            html.Div([
                dcc.Graph(id='pdl-open-low-vs-close-scatter'),
            ], style={'width': '50%', 'display': 'inline-block'}),

            html.Div([
                dcc.Graph(id='pdl-open-low-vs-high-scatter'),
            ], style={'width': '50%', 'display': 'inline-block'}),


        ], style={'display': 'flex'}),

    ])

def create_pdhl_analysis_section():
    """
    Creates a section for PD-H day analysis including distributions and scatter plots.

    Returns:
        html.Div: The layout containing input fields and result placeholders for PD-H day analysis.
    """
    return html.Div(style={'backgroundColor': '#1e1e1e', 'color': 'white',
                           'fontFamily': "'Press Start 2P', monospace", 'fontSize': '10px'},
                    children=[
        html.H3("PD-HL Day Analysis", style={'textAlign': 'center'}),

        # Distribution Plots
        html.Div([
            html.Div([
                dcc.Graph(id='pdhl-open-high-dist'),
            ], style={'width': '50%', 'display': 'inline-block'}),

            html.Div([
                dcc.Graph(id='pdhl-open-low-dist'),
            ], style={'width': '50%', 'display': 'inline-block'}),
        ], style={'display': 'flex'}),

        # Open-Close distribution
        html.Div([
            html.Div([
                dcc.Graph(id='pdhl-open-close-dist'),
            ], style={'width': '50%', 'display': 'block', 'margin': '0 auto'}),
        ]),


        # Low vs Prev Day Low and High vs Prev Day High distribution
        html.Div([
            html.Div([
                dcc.Graph(id='pdhl-low-vs-prev-low-dist'),
            ], style={'width': '50%', 'display': 'inline-block'}),

            html.Div([
                dcc.Graph(id='pdhl-high-vs-prev-high-dist'),
            ], style={'width': '50%', 'display': 'inline-block'}),

        ]),


        # Scatter Plots
        html.Div([
            html.Div([
                dcc.Graph(id='pdhl-open-low-vs-close-scatter'),
            ], style={'width': '50%', 'display': 'inline-block'}),

            html.Div([
                dcc.Graph(id='pdhl-open-low-vs-high-scatter'),
            ], style={'width': '50%', 'display': 'inline-block'}),


        ], style={'display': 'flex'}),

    ])

def create_pdh_pdl_pdhl_analysis_section():
    """
    Creates a section for PD-H day analysis including distributions and scatter plots.

    Returns:
        html.Div: The layout containing input fields and result placeholders for PD-H day analysis.
    """
    return html.Div(style={'backgroundColor': '#1e1e1e', 'color': 'white',
                           'fontFamily': "'Press Start 2P', monospace", 'fontSize': '10px'},
                    children=[
        html.H3("PD-H, PD-L, PD-HL Day Analysis", style={'textAlign': 'center'}),

        # Distribution Plots
        html.Div([
            html.Div([
                dcc.Graph(id='pdh-pdl-pdhl-open-high-dist'),
            ], style={'width': '50%', 'display': 'inline-block'}),

            html.Div([
                dcc.Graph(id='pdh-pdl-pdhl-open-low-dist'),
            ], style={'width': '50%', 'display': 'inline-block'}),
        ], style={'display': 'flex'}),

        # Open-Close distribution
        html.Div([
            html.Div([
                dcc.Graph(id='pdh-pdl-pdhl-open-close-dist'),
            ], style={'width': '50%', 'display': 'block', 'margin': '0 auto'}),
        ]),


        # Low vs Prev Day Low and High vs Prev Day High distribution
        html.Div([
            html.Div([
                dcc.Graph(id='pdh-pdl-pdhl-low-vs-prev-low-dist'),
            ], style={'width': '50%', 'display': 'inline-block'}),

            html.Div([
                dcc.Graph(id='pdh-pdl-pdhl-high-vs-prev-high-dist'),
            ], style={'width': '50%', 'display': 'inline-block'}),

        ]),


        # Scatter Plots
        html.Div([
            html.Div([
                dcc.Graph(id='pdh-pdl-pdhl-open-low-vs-close-scatter'),
            ], style={'width': '50%', 'display': 'inline-block'}),

            html.Div([
                dcc.Graph(id='pdh-pdl-pdhl-open-low-vs-high-scatter'),
            ], style={'width': '50%', 'display': 'inline-block'}),


        ], style={'display': 'flex'}),

    ])


def create_correlation_section():
    """
    Creates a section for displaying correlation tables for 180 days and 15 years with market names vertically.
    """
    return html.Div(children=[
        html.H3("Market Correlation Analysis",
                style={'textAlign': 'center', 'color': 'white', 'fontFamily': "'Press Start 2P', monospace"}),

        # 180 Days Correlation Table
        html.Div([
            html.H4("180-Day Market Correlation",
                    style={'textAlign': 'center', 'color': 'white', 'fontFamily': "'Press Start 2P', monospace"}),
            dash_table.DataTable(
                id='correlation-180-days-table',
                style_table={'width': '100%', 'margin': '0 auto', 'backgroundColor': '#1e1e1e', 'overflowX':'auto'},
                style_data={
                    'backgroundColor': '#1e1e1e',
                    'color': '#4CAF50',  # Green text
                    'fontFamily': "'Press Start 2P', monospace",
                    'textAlign': 'center',
                    'fontSize': '8px',
                },
                style_data_conditional=[
                    {'if': {'column_id': 'market_1'}, 'textAlign': 'left', 'whiteSpace': 'nowrap'},
                ],
                style_header={
                    'backgroundColor': '#4CAF50',
                    'color': 'white',
                    'fontWeight': 'bold',
                    'fontFamily': "'Press Start 2P', monospace",
                    'textAlign': 'center',
                    'fontSize': '8px',
                },

            ),
        ], style={'marginTop': '20px'}),

        # 15 Years Correlation Table
        html.Div([
            html.H4("15-Year Market Correlation",
                    style={'textAlign': 'center', 'color': 'white', 'fontFamily': "'Press Start 2P', monospace"}),
            dash_table.DataTable(
                id='correlation-15-years-table',
                style_table={'width': '100%', 'margin': '0 auto', 'backgroundColor': '#1e1e1e', 'overflowX':'auto'},
                style_data={
                    'backgroundColor': '#1e1e1e',
                    'color': '#4CAF50',  # Green text
                    'fontFamily': "'Press Start 2P', monospace",
                    'textAlign': 'center',
                    'fontSize': '8px',
                },
                style_data_conditional=[
                    {'if': {'column_id': 'market_1'}, 'textAlign': 'left', 'whiteSpace': 'nowrap'},
                ],
                style_header={
                    'backgroundColor': '#4CAF50',
                    'color': 'white',
                    'fontWeight': 'bold',
                    'fontFamily': "'Press Start 2P', monospace",
                    'textAlign': 'center',
                    'fontSize': '8px',
                },
            ),
        ], style={'marginTop': '20px'}),

    ], style={'padding': '20px', 'backgroundColor': '#000000'})


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
                        'doubleClick': 'autosize',
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

                # Day Trading Starts below the analysis section
                html.Div(
                    children=[
                        create_day_trading_stats_section(),
                        dcc.Loading(
                            id='day-trading-stats',
                            children=[html.Div(id='day-trading-stats-output')],
                            type='default'
                        )
                    ],
                    style={'margin-top': '20px'}
                ),

                # Day Trading Starts below the analysis section - Weekday
                html.Div(
                    children=[
                        create_day_trading_stats_weekday_section(),
                        dcc.Loading(
                            id='day-trading-stats-weekday',
                            children=[html.Div(id='day-trading-stats-weekday-output')],
                            type='default'
                        )
                    ],
                    style={'margin-top': '20px'}
                ),


                # Day Trading Extended below the Stats section
                html.Div(
                    children=[
                        create_day_trading_stats_1_section(),
                        dcc.Loading(
                            id='day-trading-stats-1',
                            children=[html.Div(id='day-trading-stats-1-output')],
                            type='default'
                        )
                    ],
                    style={'margin-top': '20px'}
                ),

                # Day Trading Extended below the Stats section - Weekday
                html.Div(
                    children=[
                        create_day_trading_stats_1_weekday_section(),
                        dcc.Loading(
                            id='day-trading-stats-1-weekday',
                            children=[html.Div(id='day-trading-stats-1-weekday-output')],
                            type='default'
                        )
                    ],
                    style={'margin-top': '20px'}
                ),

                # Create PD-H analysis section
                html.Div(
                    children=[
                        create_pdh_analysis_section(),
                        dcc.Loading(
                            id='pdh-analysis-loading',
                            children=[html.Div(id='pdh-analysis-output')],
                            type='default'
                        )
                    ],
                    style={'margin-top': '20px'}
                ),

                # Create PD-L analysis section
                html.Div(
                    children=[
                        create_pdl_analysis_section(),
                        dcc.Loading(
                            id='pdl-analysis-loading',
                            children=[html.Div(id='pdl-analysis-output')],
                            type='default'
                        )
                    ],
                    style={'margin-top': '20px'}
                ),

                # Create PD-HL analysis section
                html.Div(
                    children=[
                        create_pdhl_analysis_section(),
                        dcc.Loading(
                            id='pdhl-analysis-loading',
                            children=[html.Div(id='pdhl-analysis-output')],
                            type='default'
                        )
                    ],
                    style={'margin-top': '20px'}
                ),

                # Create PD-H, PD-L, PD-HL analysis section
                html.Div(
                    children=[
                        create_pdh_pdl_pdhl_analysis_section(),
                        dcc.Loading(
                            id='pdh-pdl-pdhl-analysis-loading',
                            children=[html.Div(id='pdh-pdl-pdhl-analysis-output')],
                            type='default'
                        )
                    ],
                    style={'margin-top': '20px'}
                ),

                # Create Correlation Tables section
                html.Div(
                    children=[
                        create_correlation_section(),
                        dcc.Loading(
                            id='correlation-loading',
                            children=[html.Div(id='correlation-output')],
                            type='default'
                        )
                    ],
                    style={'margin-top': '20px'}
                )

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
