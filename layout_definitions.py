# layout_definitions.py
import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc  # Correct import
from scripts.config import market_tickers
from dotenv import load_dotenv
import os

# Style Constants
ANALYSIS_SECTION_STYLE = {
    'backgroundColor': '#1e1e1e', 
    'color': 'white',
    'fontFamily': "'Press Start 2P', monospace",
    'fontSize': '10px'
}

SECTION_TITLE_STYLE = {'textAlign': 'center'}

# Table Configuration
def generate_base_columns(id_column):
    """Generate common base columns for trading stats tables"""
    return [
        {'name': id_column.capitalize(), 'id': id_column},
        {'name': 'Total Days', 'id': 'Total Days'},
        *[{'name': col, 'id': col} for col in [
            'D UP', 'D UP %', 'D DN', 'D DN %', 
            'PD-H', 'PD-H %', 'PD-L', 'PD-L %',
            'PD-HL', 'PD-HL %', 'PD-nHL', 'PD-nHL %'
        ]]
    ]

def generate_extended_columns(id_column):
    """Generate extended columns for detailed trading stats tables"""
    return [
        {'name': id_column.capitalize(), 'id': id_column},
        {'name': 'Total Days', 'id': 'Total Days'},
        *[{'name': col, 'id': col} for col in [
            'CaPD-H', 'CaPD-H %', 'CbPD-L', 'CbPD-L %',
            'CaPD-HL', 'CaPD-HL %', 'CbPD-HL', 'CbPD-HL %',
            'BISI', 'BISI %', 'SIBI', 'SIBI %'
        ]]
    ]

TABLE_CONFIGS = {
    'base_analysis': {
        'columns': [],
        'tooltips': {
            "D UP": "Days where the Close was higher than the Open",
            "D UP %": "Percentage of D UP days out of Total Days.\nD UP % + D DN % ≈ 100%",
            "D DN": "Days where the Close was lower than the Open",
            "D DN %": "Percentage of D-DN days out of Total Days.\nD UP % + D DN % ≈ 100%",
            "PD-H": "Days where the High was not lower than the Previous Day's High and the Low was higher than the Previous Day's Low.",
            "PD-H %": "Percentage of PD-H days out of Total Days.\nPD-H % + PD-L % + PD-HL % + PD-nHL ≈ 100%",
            "PD-L": "Days where the Low was not higher than the Previous Day's Low and the High was lower than the Previous Day's High.",
            "PD-L %": "Percentage of PD-L days out of Total Days.\nPD-H % + PD-L % + PD-HL % + PD-nHL ≈ 100%",
            "PD-HL": "Days where the High was not lower than the Previous Day's High, and the Low was not higher than the Previous Day's Low (Outside bar)",
            "PD-HL %": "Percentage of PD-HL days out of Total Days.\nPD-H % + PD-L % + PD-HL % + PD-nHL ≈ 100%",
            "PD-nHL": "Days where the High was lower than the Previous Day's High and the Low was higher than the Previous Day's Low (Inside bar)",
            "PD-nHL %": "Percentage of PD-nHL days out of Total Days.\nPD-H % + PD-L % + PD-HL % + PD-nHL ≈ 100%",
        }
    },
    'day_trading': {
        'base': 'base_analysis',
        'columns': generate_base_columns('year'),
        'tooltips': {
            "D UP": "Days where the Close was higher than the Open",
            "D UP %": "Percentage of D UP days out of Total Days.\nD UP % + D DN % ≈ 100%",
            "D DN": "Days where the Close was lower than the Open",
            "D DN %": "Percentage of D-DN days out of Total Days.\nD UP % + D DN % ≈ 100%",
            "PD-H": "Days where the High was not lower than the Previous Day's High and the Low was higher than the Previous Day's Low.",
            "PD-H %": "Percentage of PD-H days out of Total Days.\nPD-H % + PD-L % + PD-HL % + PD-nHL ≈ 100%",
            "PD-L": "Days where the Low was not higher than the Previous Day's Low and the High was lower than the Previous Day's High.",
            "PD-L %": "Percentage of PD-L days out of Total Days.\nPD-H % + PD-L % + PD-HL % + PD-nHL ≈ 100%",
            "PD-HL": "Days where the High was not lower than the Previous Day's High, and the Low was not higher than the Previous Day's Low (Outside bar)",
            "PD-HL %": "Percentage of PD-HL days out of Total Days.\nPD-H % + PD-L % + PD-HL % + PD-nHL ≈ 100%",
            "PD-nHL": "Days where the High was lower than the Previous Day's High and the Low was higher than the Previous Day's Low (Inside bar)",
            "PD-nHL %": "Percentage of PD-nHL days out of Total Days.\nPD-H % + PD-L % + PD-HL % + PD-nHL ≈ 100%",
        }
    },
    'day_trading_extended': {
        'columns': generate_extended_columns('year'),
        'tooltips': {
                    "CaPD-H": "PD-H Days where Close was above the Previous Day's High.\n(Closed above PD-H)",
                    "CaPD-H %": "Percentage of CaPD-H days out of Total Days.",
                    "CbPD-L": "PD-L Days where Close was below the Previous Day's Low\n(Closed below the PD-L)",
                    "CbPD-L %": "Percentage of CbPD-L days out of Total Days.",
                    "CaPD-HL": "PD-HL Days where the Close was above the Previous Day's High\n(Closed above PD-HL)",
                    "CaPD-HL %": "Percentage of CaPD-HL days out of Total Days.",
                    "CbPD-HL": "PD-HL Days where the Close was below the Previous Day's Low\n(Closed below PD-HL)",
                    "CbPD-HL %": "Percentage of CbPD-HL days out of Total Days.",
                    "BISI": "Days where Previous Day's High is lower than the Next Day's Low\n(Buyside Imbalance Sellside Inefficiency)",
                    "BISI %": "Percentage of BISI days out of Total Days.",
                    "SIBI": "Days where Previous Day's Low is higher than the Next Day's High\n(Sellside Imbalance Buyside Inefficiency)",
                    "SIBI %": "Percentage of SIBI days out of Total Days.",
        }
    },
    'day_trading_weekday': {
        'base': 'base_analysis',
        'columns': generate_base_columns('weekday'),
    },
    'day_trading_extended_weekday': {
        'columns': generate_extended_columns('weekday'),
        'tooltips': {
            "CaPD-H": "PD-H Days where Close was above the Previous Day's High.\n(Closed above PD-H)",
            "CaPD-H %": "Percentage of CaPD-H days out of Total Days.",
            "CbPD-L": "PD-L Days where Close was below the Previous Day's Low\n(Closed below the PD-L)",
            "CbPD-L %": "Percentage of CbPD-L days out of Total Days.",
            "CaPD-HL": "PD-HL Days where the Close was above the Previous Day's High\n(Closed above PD-HL)",
            "CaPD-HL %": "Percentage of CaPD-HL days out of Total Days.",
            "CbPD-HL": "PD-HL Days where the Close was below the Previous Day's Low\n(Closed below PD-HL)",
            "CbPD-HL %": "Percentage of CbPD-HL days out of Total Days.",
            "BISI": "Days where Previous Day's High is lower than the Next Day's Low\n(Buyside Imbalance Sellside Inefficiency)",
            "BISI %": "Percentage of BISI days out of Total Days.",
            "SIBI": "Days where Previous Day's Low is higher than the Next Day's High\n(Sellside Imbalance Buyside Inefficiency)",
            "SIBI %": "Percentage of SIBI days out of Total Days.",
        }
    }
}

def create_stats_table_factory(table_id, table_type):
    """Factory for creating standardized stats tables"""
    config = TABLE_CONFIGS[table_type]
    base_config = TABLE_CONFIGS.get(config.get('base', ''), {})
    
    return dash.dash_table.DataTable(
        id=table_id,
        editable=False,
        cell_selectable=False,
        columns=config['columns'],
        data=[],
        tooltip_header=config.get('tooltips', base_config.get('tooltips', {})),
        style_header=TABLE_HEADER_STYLE,
        style_cell=TABLE_CELL_STYLE,
        css=[TABLE_TOOLTIP_STYLE],
        tooltip_delay=300,
        tooltip_duration=400000000,
        style_table=TABLE_CONTAINER_STYLE,
        style_data_conditional=[
            {
                'if': {'column_id': config['columns'][0]['id']},
                'backgroundColor': '#333',
                'color': 'white',
                'fontWeight': 'bold'
            }
        ]
    )
FLEX_CONTAINER_STYLE = {'display': 'flex'}
HALF_WIDTH = {'width': '50%', 'display': 'inline-block'}
CENTERED_HALF_WIDTH = {'width': '50%', 'display': 'block', 'margin': '0 auto'}

TABLE_HEADER_STYLE = {
    'backgroundColor': '#333',
    'color': 'white',
    'border': '1px solid white',
    'fontFamily': "'Press Start 2P', monospace",
    'fontSize': '10px'
}

TABLE_CELL_STYLE = {
    'backgroundColor': '#1e1e1e',
    'color': 'white',
    'border': '1px solid #444',
    'fontFamily': "'Press Start 2P', monospace",
    'fontSize': '10px',
    'textAlign': 'center'
}

TABLE_TOOLTIP_STYLE = {
    'selector': '.dash-table-tooltip',
    'rule': '''
        background-color: #1e1e1e;
        font-family: monospace;
        color: white;
        white-space: pre-line;
    '''
}

TABLE_CONTAINER_STYLE = {'overflowX': 'scroll'}

# COT Section Factory
def create_cot_section(cot_type, section_name, toggle_id):
    """Factory for creating COT checklist sections"""
    return html.Div([
        html.Button(
            f'{cot_type} - {section_name.replace("-", " ").title()}',
            id=toggle_id,
            n_clicks=0,
            style={'width': '100%', 'textAlign': 'left'}
        ),
        dbc.Collapse(
            children=[
                dcc.Checklist(
                    id=f'{"26w-index" if key == "index_26w" else key.replace("_", "-")}-{cot_type.lower()}-{section_name.lower().replace(" ", "-")}-checklist',
                    options=CHECKLIST_OPTIONS[key],
                    value=[],
                    inputStyle=INPUT_STYLE
                ) for key in [
                    'open_interest', 'oi_percentages', 'positions_change',
                    'net_positions', 'net_positions_change', 'index_26w'
                ]
            ],
            id=f'{cot_type.lower()}-{section_name.lower().replace(" ", "-")}-collapse',
            is_open=False
        )
    ])

def create_day_analysis_section(section_id, title, comparisons=None):
    """Factory for creating standardized day analysis sections"""
    return html.Div(
        id=f"{section_id}-section",
        style=ANALYSIS_SECTION_STYLE,
        children=[
            html.H3(title, style=SECTION_TITLE_STYLE),
            create_day_analysis_dist_legend(),
            html.Div([
                html.Div(dcc.Graph(id=f"{section_id}-open-low-dist",
                         config={'displayModeBar': False, 'staticPlot': True}), style=HALF_WIDTH),
                html.Div(dcc.Graph(id=f"{section_id}-open-high-dist",
                         config={'displayModeBar': False, 'staticPlot': True}), style=HALF_WIDTH),
            ], style=FLEX_CONTAINER_STYLE),
            html.Div([
                html.Div(dcc.Graph(id=f"{section_id}-open-close-dist",
                         config={'displayModeBar': False, 'staticPlot': True}), style=CENTERED_HALF_WIDTH),
            ]),
            html.Div([
                html.Div(dcc.Graph(id=f"{section_id}-{comp}-dist",
                         config={'displayModeBar': False, 'staticPlot': True}), style=HALF_WIDTH)
                for comp in comparisons or []
            ], style=FLEX_CONTAINER_STYLE),
            create_day_analysis_scatter_legend(),
            html.Div([
                html.Div(dcc.Graph(id=f"{section_id}-open-low-vs-close-scatter",
                         config={'displayModeBar': False, 'staticPlot': True}), style=HALF_WIDTH),
                html.Div(dcc.Graph(id=f"{section_id}-open-low-vs-high-scatter",
                         config={'displayModeBar': False, 'staticPlot': True}), style=HALF_WIDTH),
            ], style=FLEX_CONTAINER_STYLE)
        ]
    )

def create_table_factory(table_id, columns, tooltips):
    """Standardized table creation"""
    return dash.dash_table.DataTable(
        id=table_id,
        editable=False,
        cell_selectable=False,
        columns=columns,
        data=[],
        tooltip_header=tooltips,
        style_header=TABLE_HEADER_STYLE,
        style_cell=TABLE_CELL_STYLE,
        css=[TABLE_TOOLTIP_STYLE],
        tooltip_delay=300,
        tooltip_duration=400000000,
        style_table=TABLE_CONTAINER_STYLE
    )

# Load environment variables from .env file
load_dotenv()
user_tier = os.getenv("USER_TIER", "free")

# Define constants for repeated strings, styles, and default values
DEFAULT_MARKET = 'SP 500'
DEFAULT_YEARS = [15, 35]
DEFAULT_DIRECTION = 'Long'

if user_tier == 'premium':
    CHECKLIST_OPTIONS = {
        'years': [
            {'label': '15 Years', 'value': 15},
            {'label': '35 Years', 'value': 35}
        ],
        'ohlc': [
            {'label': 'OHLC', 'value': 'OHLC'}
        ],
        'open_interest': [
            {'label': 'Open Interest', 'value': 'Open Interest'}
        ],
        'oi_percentages': [
            {'label': '% of OI', 'value': 'OI Percentages'}
        ],
        'positions_change': [
            {'label': '% Change in Positions', 'value': 'Positions Change'}
        ],
        'net_positions': [
            {'label': 'Net Positions', 'value': 'Net Positions'}
        ],
        'net_positions_change': [
            {'label': '% Change in Net Positions', 'value': 'Net Positions Change'}
        ],
        'index_26w': [
            {'label': '26-Week Index', 'value': '26W Index'}
        ]
    }
else:
    CHECKLIST_OPTIONS = {
        'years': [
            {'label': '15 Years (Premium)', 'value': 0},
            {'label': '35 Years (Premium)', 'value': 1}
        ],
        'ohlc': [
            {'label': 'OHLC', 'value': 'OHLC'}
        ],
        'open_interest': [
            {'label': 'Open Interest', 'value': 'Open Interest'}
        ],
        'oi_percentages': [
            {'label': '% of OI', 'value': 'OI Percentages'}
        ],
        'positions_change': [
            {'label': '% Change in Positions', 'value': 'Positions Change'}
        ],
        'net_positions': [
            {'label': 'Net Positions', 'value': 'Net Positions'}
        ],
        'net_positions_change': [
            {'label': '% Change in Net Positions', 'value': 'Net Positions Change'}
        ],
        'index_26w': [
            {'label': '26-Week Index', 'value': '26W Index'}
        ]
    }


BUTTON_STYLES = {'marginBottom': '3px'}
CHECKLIST_STYLES = {'marginBottom': '10px'}
LAYOUT_STYLES = {'display': 'flex'}
GRAPH_STYLES = {'flex': 1, 'padding': '10px', 'overflow': 'hidden'}
INPUT_STYLE = {"marginRight": "10px", "width": "40px"}


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
                                html.Label("Select Date Range", style={'marginBottom': '5px'}),
                                dcc.DatePickerRange(
                                    id='date-picker-range',
                                    start_date_placeholder_text="Start Period",
                                    end_date_placeholder_text="End Period",
                                    display_format='MMM-DD',
                                    month_format='MMMM',
                                    min_date_allowed='2025-01-01',
                                    max_date_allowed='2025-12-31',
                                    start_date='2025-01-01',  # Default to None or a specific start date
                                    end_date='2025-12-31',  # Default to None or a specific end date
                                    clearable=False,
                                )
                            ], style={'width': '400px', 'display': 'flex', 'flexDirection': 'column',
                                      'alignItems': 'center'}),

                            html.Div(children=[
                                html.Label("Direction", style={'marginBottom': '5px'}),
                                dcc.Dropdown(
                                    id='direction-dropdown',
                                    options=[
                                        {'label': 'Long', 'value': 'Long'},
                                        {'label': 'Short', 'value': 'Short'}
                                    ],
                                    value=DEFAULT_DIRECTION,  # Default value
                                    placeholder=DEFAULT_DIRECTION,
                                    style={'backgroundColor': '#333', 'color': 'white', 'borderColor': '#555'},
                                    clearable=False,
                                    className='dropdown-menu-direction',
                                    searchable=False,
                                ),
                            ], style={'width': '200px', 'display': 'flex', 'flexDirection': 'column',
                                      'alignItems': 'center'}),

                            html.Div(children=[
                                dcc.Interval(
                                    id='interval-auto-load',
                                    interval=1 * 1000,  # 1 second delay
                                    n_intervals=0,  # Starts immediately on page load
                                    max_intervals=1  # Only fires once
                                ),

                                html.Button("Perform Analysis", id='perform-analysis-button', style={
                                    'height': '40px', 'marginTop': '18px', 'backgroundColor': '#333',
                                    'color': 'white',
                                    'border': '1px solid white'}),
                            ], style={'display': 'flex', 'alignItems': 'center'})
                        ], style={'display': 'flex', 'gap': '15px', 'alignItems': 'center'}),

                        # Table for Year-by-Year Results
                        html.Div(children=[
                            html.Label("Yearly Analysis", style={'marginBottom': '5px'}),
                            dash.dash_table.DataTable(id='yearly-analysis-table',
                                                      editable=False,
                                                      cell_selectable=False,
                                                      columns=[
                                                          {'name': 'Year', 'id': 'year'},
                                                          {'name': 'Max Drawdown (Points)',
                                                           'id': 'Max Drawdown (Points)'},
                                                          {'name': 'Max Drawdown (%)', 'id': 'Max Drawdown (%)'},
                                                          {'name': 'Max Gain (Points)', 'id': 'Max Gain (Points)'},
                                                          {'name': 'Max Gain (%)', 'id': 'Max Gain (%)'},
                                                          {'name': 'Closing Points', 'id': 'Closing Points'},
                                                          {'name': 'Closing Percentage', 'id': 'Closing Percentage'},
                                                      ],
                                                      data=[],
                                                      style_header={'backgroundColor': '#333', 'color': 'white',
                                                                    'border': '1px solid white',
                                                                    'fontFamily': "'Press Start 2P', monospace",
                                                                    'fontSize': '10px'},
                                                      style_cell={'backgroundColor': '#1e1e1e', 'color': 'white',
                                                                  'border': '1px solid #444',
                                                                  'fontFamily': "'Press Start 2P', monospace",
                                                                  'fontSize': '10px'},
                                                      style_table={'overflowX': 'scroll'}
                                                      )
                        ], style={'paddingTop': '15px'}),

                        # Summary Statistics for 15 and 30 years
                        html.Div(id='15-year-summary', children="15-Year Summary: ",
                                 style={'marginTop': '20px', 'backgroundColor': '#333',
                                        'padding': '10px',
                                        'borderRadius': '5px', 'fontFamily': "'Press Start 2P', monospace",
                                        'fontSize': '10px', 'whiteSpace': 'pre-line'}, ),
                        html.Div(id='30-year-summary', children="30-Year Summary: ",
                                 style={'marginTop': '20px', 'backgroundColor': '#333',
                                        'padding': '10px',
                                        'borderRadius': '5px', 'fontFamily': "'Press Start 2P', monospace",
                                        'fontSize': '10px', 'whiteSpace': 'pre-line'}),

                        # Container for the distribution charts in a row
                        html.Div([
                            # Regular distribution chart for 15 years
                            html.Div([

                                dcc.Graph(id='distribution-chart-15', config={'displayModeBar': False},
                                          style={'padding': '0', 'margin': '0'}),
                            ], style={'width': '50%', 'display': 'inline-block', 'padding': '10px'}),

                            # Optimal distribution chart for 15 years
                            html.Div([

                                dcc.Graph(id='distribution-chart-optimal-15', config={'displayModeBar': False}),
                            ], style={'width': '50%', 'display': 'inline-block', 'padding': '10px'}),
                        ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}),

                        # Same structure for the 30 years below
                        html.Div([
                            html.Div([

                                dcc.Graph(id='distribution-chart-30', config={'displayModeBar': False}),
                            ], style={'width': '50%', 'display': 'inline-block', 'padding': '10px'}),

                            html.Div([

                                dcc.Graph(id='distribution-chart-optimal-30', config={'displayModeBar': False}),
                            ], style={'width': '50%', 'display': 'inline-block', 'padding': '10px'}),
                        ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'}),

                        html.Div([
                            # 15-year cumulative returns and metrics
                            html.Div([
                                dcc.Graph(id='cumulative-return-chart-15', config={'displayModeBar': False}),
                                html.Div(id='risk-metrics-summary-15'),
                                html.Div(id='risk-metrics-summary-15-stoploss'),
                            ], style={'display': 'inline-block', 'width': '48%'}),

                            # 30-year cumulative returns and metrics
                            html.Div([
                                dcc.Graph(id='cumulative-return-chart-30', config={'displayModeBar': False}),
                                html.Div(id='risk-metrics-summary-30'),
                                html.Div(id='risk-metrics-summary-30-stoploss'),
                            ], style={'display': 'inline-block', 'width': '48%'}),
                        ])
                    ])


def create_analysis_table_section(section_id, title, table_type):
    """Generic factory for creating analysis table sections"""
    return html.Div(
        style=ANALYSIS_SECTION_STYLE,
        children=[
            html.H3(title, style=SECTION_TITLE_STYLE),
            create_stats_table_factory(
                table_id=f"{section_id}-table",
                table_type=table_type
            )
        ]
    )

# Create section generators using partial application
from functools import partial

create_day_trading_stats_section = partial(
    create_analysis_table_section,
    section_id='day-trading-stats',
    title='Day Trading Stats',
    table_type='day_trading'
)

create_day_trading_stats_weekday_section = partial(
    create_analysis_table_section,
    section_id='day-trading-stats-weekday',
    title='Day Trading Stats Weekdays', 
    table_type='day_trading_weekday'
)

create_day_trading_stats_1_section = partial(
    create_analysis_table_section,
    section_id='day-trading-stats-1',
    title='Day Trading Stats - continuation',
    table_type='day_trading_extended'
)

create_day_trading_stats_1_weekday_section = partial(
    create_analysis_table_section,
    section_id='day-trading-stats-1-weekday',
    title='Day Trading Stats - continuation - Weekday',
    table_type='day_trading_extended_weekday'
)


def create_day_analysis_dist_legend():
    return html.Div(
        html.P([
            "Distribution Charts Lines Legend: ",
            html.Span("95th percentile", style={'color': 'Salmon'}),
            ", ",
            html.Span("70th percentile", style={'color': 'CornFlowerBlue'}),
        ], style={
            'fontWeight': 'bold',
            'color': 'white',
            'fontFamily': "'Press Start 2P', monospace",
            'fontSize': '12px',
            'backgroundColor': '#1e1e1e',
            'padding': '10px',
            'borderRadius': '5px',
            'marginBottom': '20px',
        })
    )


def create_day_analysis_scatter_legend():
    return html.Div(
        html.P([
            "Scatter Charts Lines Legend: ",
            html.Span("Optimal Stop Loss", style={'color': 'Salmon'}),
            ", ",
            html.Span("Optimal Exit", style={'color': 'CornFlowerBlue'}),
            ", ",
            html.Span("Expected Return", style={'color': 'Aquamarine'}),
        ], style={
            'fontWeight': 'bold',
            'color': 'white',
            'fontFamily': "'Press Start 2P', monospace",
            'fontSize': '12px',
            'backgroundColor': '#1e1e1e',
            'padding': '10px',
            'borderRadius': '5px',
            'marginBottom': '20px',
        })
    )


# Unified section creation using factory pattern
from functools import partial

create_dup_analysis_section = partial(
    create_day_analysis_section,
    section_id="dup",
    title="D-UP Day Analysis",
    comparisons=['low-vs-prev-low', 'high-vs-prev-high']
)

create_ddown_analysis_section = partial(
    create_day_analysis_section,
    section_id="ddown",
    title="D-DN Day Analysis",
    comparisons=['low-vs-prev-low', 'high-vs-prev-high']
)

create_pdh_analysis_section = partial(
    create_day_analysis_section,
    section_id="pdh",
    title="PD-H Day Analysis",
    comparisons=['high-vs-prev-high']
)

create_pdl_analysis_section = partial(
    create_day_analysis_section,
    section_id="pdl",
    title="PD-L Day Analysis",
    comparisons=['low-vs-prev-low']
)

create_pdhl_analysis_section = partial(
    create_day_analysis_section,
    section_id="pdhl",
    title="PD-HL Day Analysis",
    comparisons=['low-vs-prev-low', 'high-vs-prev-high']
)

create_pdh_pdl_pdhl_analysis_section = partial(
    create_day_analysis_section,
    section_id="pdh-pdl-pdhl",
    title="PD-H/PD-L/PD-HL Day Analysis",
    comparisons=['low-vs-prev-low', 'high-vs-prev-high']
)




def create_correlation_section():
    """Create simplified correlation section with only 180-day table"""
    return html.Div(children=[
        html.H3("Market Correlation",
                style={'textAlign': 'center', 'color': 'white', 
                       'fontFamily': "'Press Start 2P', monospace"}),
        
        # Single 180-day table
        html.Div([
            html.H4("180-Day Market Correlation",
                    style={'textAlign': 'center', 'color': 'white', 
                           'fontFamily': "'Press Start 2P', monospace"}),
            dash_table.DataTable(
                id='correlation-180-days-table',
                editable=False,
                cell_selectable=False,
                style_table={'width': '100%', 'margin': '0 auto', 
                            'backgroundColor': '#1e1e1e', 'overflowX': 'auto'},
                style_data={
                    'backgroundColor': '#1e1e1e',
                    'color': '#4CAF50',
                    'fontFamily': "'Press Start 2P', monospace",
                    'textAlign': 'center',
                    'fontSize': '8px',
                },
                style_data_conditional=[{
                    'if': {'column_id': 'MKT'},
                    'backgroundColor': '#4CAF50',
                    'color': 'white',
                    'fontWeight': 'bold',
                    'textAlign': 'left',
                    'whiteSpace': 'nowrap'
                }],
                style_header={
                    'backgroundColor': '#4CAF50',
                    'color': 'white',
                    'fontWeight': 'bold',
                    'fontFamily': "'Press Start 2P', monospace",
                    'textAlign': 'center',
                    'fontSize': '8px',
                },
            )
        ], style={'marginTop': '20px'})
    ], style={'padding': '20px', 'backgroundColor': '#1e1e1e'})


def create_layout(app):
    """
    Create and set the layout for the Dash application.

    Args:
        app (dash.Dash): The Dash application instance.
    """

    if user_tier == 'premium':
        app.layout = html.Div(style={'display': 'flex'}, children=[
            html.Div(
                children=[
                    html.Div([
                        html.Button('Prev. Market', id='prev-market-button-main', n_clicks=0, className='above-chart-button'),
                        html.Button('Next Market', id='next-market-button-main', n_clicks=0, className='above-chart-button'),
                        html.Button('Prev. Year', id='prev-year-button-main', n_clicks=0, className='above-chart-button'),
                        html.Button('Next Year', id='next-year-button-main', n_clicks=0, className='above-chart-button')
                    ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginTop': '10px', 'gap': '10px'}),


                    dcc.Loading(
                        id="loading-combined-chart",
                        type="circle",
                        children=dcc.Graph(
                            id="combined-chart",
                            config={"scrollZoom": True, "doubleClick": "autosize", "displayModeBar": False},
                            style={"backgroundColor": "#1e1e1e"}
                        ),
                    ),

                    dcc.Loading(
                        id='loading-opportunity',
                        children=[create_analysis_section(), html.Div(id='opportunity-output')],
                        type='circle'
                    ),

                    # Day Trading Starts below the analysis section
                    html.Div(
                        children=[
                            create_day_trading_stats_section(),
                            dcc.Loading(
                                id='day-trading-stats',
                                children=[html.Div(id='day-trading-stats-output')],
                                type='circle'
                            )
                        ],
                        style={'marginTop': '20px'}
                    ),

                    # Day Trading Starts below the analysis section - Weekday
                    html.Div(
                        children=[
                            create_day_trading_stats_weekday_section(),
                            dcc.Loading(
                                id='day-trading-stats-weekday',
                                children=[html.Div(id='day-trading-stats-weekday-output')],
                                type='circle'
                            )
                        ],
                        style={'marginTop': '20px'}
                    ),

                    # Day Trading Extended below the Stats section
                    html.Div(
                        children=[
                            create_day_trading_stats_1_section(),
                            dcc.Loading(
                                id='day-trading-stats-1',
                                children=[html.Div(id='day-trading-stats-1-output')],
                                type='circle'
                            )
                        ],
                        style={'marginTop': '20px'}
                    ),

                    # Day Trading Extended below the Stats section - Weekday
                    html.Div(
                        children=[
                            create_day_trading_stats_1_weekday_section(),
                            dcc.Loading(
                                id='day-trading-stats-1-weekday',
                                children=[html.Div(id='day-trading-stats-1-weekday-output')],
                                type='circle'
                            )
                        ],
                        style={'marginTop': '20px'}
                    ),

                    dcc.Loading(
                        id='loading-dup-analysis-output',
                        children=[create_dup_analysis_section(), html.Div(id='dup-analysis-output')],
                        type='circle'
                    ),

                    dcc.Loading(
                        id='loading-ddown-analysis-output',
                        children=[create_ddown_analysis_section(), html.Div(id='ddown-analysis-output')],
                        type='circle'
                    ),

                    dcc.Loading(
                        id='loading-pdh-analysis-output',
                        children=[create_pdh_analysis_section(), html.Div(id='pdh-analysis-output')],
                        type='circle'
                    ),

                    dcc.Loading(
                        id='loading-pdl-analysis-output',
                        children=[create_pdl_analysis_section(), html.Div(id='pdl-analysis-output')],
                        type='circle'
                    ),

                    dcc.Loading(
                        id='loading-pdhl-analysis-output',
                        children=[create_pdhl_analysis_section(), html.Div(id='pdhl-analysis-output')],
                        type='circle'
                    ),

                    dcc.Loading(
                        id='loading-pdh_pdl_pdhl-analysis-output',
                        children=[create_pdh_pdl_pdhl_analysis_section(), html.Div(id='pdh_pdl_pdhl-analysis-output')],
                        type='circle'
                    ),

                    # Create Correlation Tables section
                    html.Div(
                        children=[
                            create_correlation_section(),
                            dcc.Loading(
                                id='correlation-loading',
                                children=[html.Div(id='correlation-output')],
                                type='circle'
                            )
                        ],
                        style={'marginTop': '20px'}
                    ),

                    html.Div(
                        children=[
                            html.P(
                                "Disclaimer: Trading involves substantial risk.",
                                style={"color": "white", "display": "inline", "fontSize": "10px"},
                            ),
                            html.A(
                                "Read Full Disclaimer",
                                href="/disclaimer",  # This is the route for the disclaimer page
                                target="_blank",  # Open in a new tab
                                style={
                                    "color": "#4CAF50",
                                    "textDecoration": "underline",
                                    "fontSize": "10px",
                                    "marginLeft": "5px",
                                },
                            ),
                        ],
                        style={"backgroundColor": "#1e1e1e", "padding": "10px", "textAlign": "center"},
                    )

                ],
                style={'flex': 1, 'padding': '10px', 'overflow': 'hidden'}
            ),

            html.Div(
                id='right-panel',
                children=[
                    html.Button(
                        id='toggle-button',
                        n_clicks=0,
                        children=[
                            html.Span(className='navbar-dark navbar-toggler-icon')  # Bootstrap hamburger icon
                        ],
                        style={
                            'border': 'none',
                            'color': 'white',  # Ensures text/icon visibility
                            'fontSize': '10px',  # Adjusts icon size
                            'padding': '10px',  # Ensures clickable space
                            'zIndex': '1000',  # Brings button to the front

                        }
                    ),

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
                                        style={'width': '100%', 'marginBottom': '10px', 'backgroundColor': '#2b2b2b',
                                               'color': 'white', 'border': 'none'},
                                        searchable=False
                                    ),
                                    html.Div([
                                        html.Button('Prev. Market', id='prev-market-button-right-panel', n_clicks=0),
                                        html.Button('Next Market', id='next-market-button-right-panel', n_clicks=0),
                                    ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginTop': '10px'}),
                                    html.Div([
                                        html.Button('Prev. Year', id='prev-year-button-right-panel', n_clicks=0),
                                        html.Button('Next Year', id='next-year-button-right-panel', n_clicks=0)
                                    ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginTop': '10px'}),
                                ],
                                style={'marginBottom': '10px'}
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
                                    id='ohlc-cycles-collapse',
                                    is_open=False  # Start collapsed by default
                                )
                            ]),

                            # Generate COT sections using factory function
                            create_cot_section('Legacy', 'Combined', 'legacy-combined-toggle'),
                            create_cot_section('Legacy', 'Futures-Only', 'legacy-futures-only-toggle'),
                            create_cot_section('Disaggregated', 'Combined', 'disaggregated-combined-toggle'),
                            create_cot_section('Disaggregated', 'Futures-Only', 'disaggregated-futures-only-toggle'),
                            create_cot_section('TFF', 'Combined', 'tff-combined-toggle'),
                            create_cot_section('TFF', 'Futures-Only', 'tff-futures-only-toggle'),

                            # Links to Twitter and YouTube
                            html.Div([
                                html.P(
                                    "See tutorials and more!",
                                    style={'fontWeight': 'bold', 'textAlign': 'center', 'color': 'white',
                                           'marginTop': '20px'}
                                ),
                                html.Div([
                                    # Twitter link
                                    html.A(
                                        html.Img(
                                            src="https://upload.wikimedia.org/wikipedia/commons/9/95/Twitter_new_X_logo.png",
                                            style={'height': '30px', 'width': '30px', 'marginRight': '10px'}
                                        ),
                                        href="https://x.com/ClockTrades",  # Replace with your Twitter link
                                        target="_blank"
                                    ),
                                    # YouTube link
                                    html.A(
                                        html.Img(
                                            src="https://upload.wikimedia.org/wikipedia/commons/d/d0/YouTube_full-color_icon_%282017%29.webp",
                                            style={'height': '30px', 'width': '45px'}
                                        ),
                                        href="https://youtube.com/@ClockTrades",  # Replace with your YouTube link
                                        target="_blank"
                                    ),
                                ], style={'display': 'flex', 'justifyContent': 'center'})
                            ]),

                            html.Div([
                                # html.Button('Previous Year', id='prev-year-button', n_clicks=0),
                                # html.Button('Next Year', id='next-year-button', n_clicks=0)
                            ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginTop': '10px'}),
                            dcc.Store(id='current-year', data=2025),
                            dcc.Store(id='stored-market', data=DEFAULT_MARKET),
                            dcc.Store(id='active-subplots', data=[]),  # Track active subplots dynamically
                        ]
                    ),

                ],
            ),
        ])
    else:
        app.layout = html.Div(style={'display': 'flex'}, children=[
            html.Div(
                children=[
                    html.Div([
                        html.Button('Prev. Market', id='prev-market-button-main', n_clicks=0,
                                    className='above-chart-button'),
                        html.Button('Next Market', id='next-market-button-main', n_clicks=0, className='above-chart-button'),
                        html.Button('Prev. Year', id='prev-year-button-main', n_clicks=0, className='above-chart-button'),
                        html.Button('Next Year', id='next-year-button-main', n_clicks=0, className='above-chart-button')
                    ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginTop': '10px',
                              'gap': '10px'}),

                    dcc.Graph(
                        id='combined-chart',
                        config={
                            'scrollZoom': True,
                            'doubleClick': 'autosize',
                            'displayModeBar': False,

                        },
                        style={'backgroundColor': '#1e1e1e'}  # Set background color for the graph container
                    ),

                    html.Div(children=[
                        dcc.Interval(
                            id='interval-auto-load',
                            interval=1 * 1000,  # 1 second delay
                            n_intervals=0,  # Starts immediately on page load
                            max_intervals=1  # Only fires once
                        ),
                        ]
                    ),

                    html.Div(children=[
                        html.P(
                            "Enjoy the Power of FREE version Now – Full Features Coming Soon!",
                            style={'fontWeight': 'bold', 'textAlign': 'center', 'color': 'white',
                                   'marginTop': '20px'}
                        ),
                        html.P(
                            [
                                "Follow us on ",
                                html.A(
                                    "X for Updates!",
                                    href="https://x.com/ClockTrades",
                                    target="_blank",  # Opens the link in a new tab
                                    style={'color': 'CornflowerBlue', 'textDecoration': 'none', 'fontWeight': 'bold'}
                                )
                            ],
                            style={'fontWeight': 'bold', 'textAlign': 'center', 'color': 'white', 'marginTop': '20px'}
                        ),
                    ]),

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
                        style={'marginTop': '20px'}
                    ),

                    html.Div(
                        children=[
                            html.P(
                                "Disclaimer: Trading involves substantial risk.",
                                style={"color": "white", "display": "inline", "fontSize": "10px"},
                            ),
                            html.A(
                                "Read Full Disclaimer",
                                href="/disclaimer",  # This is the route for the disclaimer page
                                target="_blank",  # Open in a new tab
                                style={
                                    "color": "#4CAF50",
                                    "textDecoration": "underline",
                                    "fontSize": "10px",
                                    "marginLeft": "5px",
                                },
                            ),
                        ],
                        style={"backgroundColor": "#1e1e1e", "padding": "10px", "textAlign": "center"},
                    )

                ],
                style={'flex': 1, 'padding': '10px', 'overflow': 'hidden'}
            ),

            html.Div(
                id='right-panel',
                children=[
                    html.Button(
                        id='toggle-button',
                        n_clicks=0,
                        children=[
                            html.Span(className='navbar-dark navbar-toggler-icon')  # Bootstrap hamburger icon
                        ],
                        style={
                            'border': 'none',
                            'color': 'white',  # Ensures text/icon visibility
                            'fontSize': '10px',  # Adjusts icon size
                            'padding': '10px',  # Ensures clickable space
                            'zIndex': '1000',  # Brings button to the front

                        }
                    ),

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
                                        style={'width': '100%', 'marginBottom': '10px', 'backgroundColor': '#2b2b2b',
                                               'color': 'white', 'border': 'none'},
                                        searchable=False,
                                    ),
                                    html.Div([
                                        html.Button('Prev. Market', id='prev-market-button-right-panel', n_clicks=0),
                                        html.Button('Next Market', id='next-market-button-right-panel', n_clicks=0),
                                    ], style={'display': 'flex', 'justifyContent': 'space-between',
                                              'marginTop': '10px'}),
                                    html.Div([
                                        html.Button('Prev. Year', id='prev-year-button-right-panel', n_clicks=0),
                                        html.Button('Next Year', id='next-year-button-right-panel', n_clicks=0)
                                    ], style={'display': 'flex', 'justifyContent': 'space-between',
                                              'marginTop': '10px'}),
                                ],
                                style={'marginBottom': '10px'}
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

                            create_cot_section('Legacy', 'Combined', 'legacy-combined-toggle'),
                            create_cot_section('Legacy', 'Futures-Only', 'legacy-futures-only-toggle'),
                            create_cot_section('Disaggregated', 'Combined', 'disaggregated-combined-toggle'),
                            create_cot_section('Disaggregated', 'Futures-Only', 'disaggregated-futures-only-toggle'),
                            create_cot_section('TFF', 'Combined', 'tff-combined-toggle'),
                            create_cot_section('TFF', 'Futures-Only', 'tff-futures-only-toggle'),

                            # Links to Twitter and YouTube
                            html.Div([
                                html.P(
                                    "See tutorials and more!",
                                    style={'fontWeight': 'bold', 'textAlign': 'center', 'color': 'white',
                                           'marginTop': '20px'}
                                ),
                                html.Div([
                                    # Twitter link
                                    html.A(
                                        html.Img(
                                            src="https://upload.wikimedia.org/wikipedia/commons/9/95/Twitter_new_X_logo.png",
                                            style={'height': '30px', 'width': '30px', 'marginRight': '10px'}
                                        ),
                                        href="https://x.com/ClockTrades",  # Replace with your Twitter link
                                        target="_blank"
                                    ),
                                    # YouTube link
                                    html.A(
                                        html.Img(
                                            src="https://upload.wikimedia.org/wikipedia/commons/d/d0/YouTube_full-color_icon_%282017%29.webp",
                                            style={'height': '30px', 'width': '45px'}
                                        ),
                                        href="https://youtube.com/@ClockTrades",  # Replace with your YouTube link
                                        target="_blank"
                                    ),
                                ], style={'display': 'flex', 'justifyContent': 'center'}),

                            ]),

                            html.Div([
                                # html.Button('Previous Year', id='prev-year-button', n_clicks=0),
                                # html.Button('Next Year', id='next-year-button', n_clicks=0)
                            ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginTop': '10px'}),
                            dcc.Store(id='current-year', data=2025),
                            dcc.Store(id='stored-market', data=DEFAULT_MARKET),
                            dcc.Store(id='active-subplots', data=[]),  # Track active subplots dynamically
                        ]
                    ),

                ],
            ),
        ])
