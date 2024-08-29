# layout.py
import dash
from dash import dcc, html, Input, Output, State, ctx
import plotly.graph_objs as go
import plotly.subplots as sp
from data_fetchers import (
    SeasonalDataFetcher,
    OHLCDataFetcher,
    OpenInterestDataFetcher,
    OpenInterestPercentagesFetcher,
    PositionsChangeDataFetcher,
    NetPositionsDataFetcher,
    PositionsChangeNetDataFetcher,
    Index26WDataFetcher
)
def format_market_name(market_name):
    """
    Format the market name to match the expected format used in data fetching functions.

    Args:
        market_name (str): The original market name.

    Returns:
        str: The formatted market name.
    """
    # Example: Convert the market name to uppercase and replace spaces with underscores
    formatted_name = market_name.upper().replace(' ', '_')
    return formatted_name

app = dash.Dash(__name__)

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        {%config%}
        {%scripts%}
        {%renderer%}
        <script src="/assets/scripts.js"></script>
    </body>
</html>
'''

# Create market links using market_tickers
from scripts.config import market_tickers

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


@app.callback(
    Output('right-panel', 'className'),
    Input('toggle-button', 'n_clicks'),
    State('right-panel', 'className')
)
def toggle_panel(n_clicks, class_name):
    if n_clicks == 0:
        return ''
    if n_clicks % 2 == 1:
        return 'collapsed'
    else:
        return ''


@app.callback(
    Output('stored-market', 'data'),
    [Input({'type': 'market-link', 'index': dash.dependencies.ALL}, 'n_clicks')]
)
def update_stored_market(n_clicks):
    if ctx.triggered:
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if 'market-link' in triggered_id:
            triggered_ticker = eval(triggered_id).get('index')
            selected_market = next((name for name, ticker in market_tickers.items() if ticker == triggered_ticker),
                                   default_market)
            return selected_market
    return default_market


@app.callback(
    Output('current-year', 'data'),
    [Input('prev-year-button', 'n_clicks'),
     Input('next-year-button', 'n_clicks')],
    [State('current-year', 'data')]
)
def update_year(n_clicks_prev, n_clicks_next, current_year):
    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if 'prev-year-button' in button_id:
            new_year = max(1994, current_year - 1)
        elif 'next-year-button' in button_id:
            new_year = min(2024, current_year + 1)
        else:
            new_year = current_year
        return new_year
    return current_year

@app.callback(
    Output('combined-chart', 'figure'),
    [Input({'type': 'market-link', 'index': dash.dependencies.ALL}, 'n_clicks'),
     Input('years-checklist', 'value'),
     Input('ohlc-checklist', 'value'),
     Input('open-interest-checklist', 'value'),
     Input('oi-percentages-checklist', 'value'),
     Input('positions-change-checklist', 'value'),
     Input('net-positions-checklist', 'value'),
     Input('net-positions-change-checklist', 'value'),
     Input('26w-index-checklist', 'value'),
     Input('stored-market', 'data'),
     Input('current-year', 'data')]
)
def update_charts(n_clicks, selected_years, ohlc_visibility, open_interest_visibility, oi_percentages_visibility,
                  positions_change_visibility, net_positions_visibility, net_positions_change_visibility,
                  index_26w_visibility, stored_market, current_year):
    # Determine the selected market based on the trigger
    if ctx.triggered:
        triggered = ctx.triggered[0]['prop_id'].split('.')[0]
        if 'market-link' in triggered:
            triggered_ticker = eval(triggered).get('index')
            stored_market = next((name for name, ticker in market_tickers.items() if ticker == triggered_ticker),
                                 default_market)

    if not stored_market:
        return go.Figure()  # Return empty figure if no market is selected

    formatted_market_name = format_market_name(stored_market)

    # Initialize figure
    fig = sp.make_subplots(
        rows=7,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=(
            f'{stored_market} OHLC/Seasonality', 'Open Interest', 'Open Interest Percentages',
            '% Change in Positions', 'Net Positions', '% Change in NET Positions', '26-Week Index'
        ),
        specs=[
            [{'secondary_y': True}],
            [{'secondary_y': False}],
            [{'secondary_y': False}],
            [{'secondary_y': False}],
            [{'secondary_y': False}],
            [{'secondary_y': False}],
            [{'secondary_y': False}]
        ]
    )

    # Seasonal Chart
    figure_data = []
    shapes = []
    x_axis_ticks = []
    x_axis_tick_labels = []

    for years in selected_years:
        df = SeasonalDataFetcher.fetch_seasonal_data(formatted_market_name, years)
        if not df.empty:
            figure_data.append(
                go.Scatter(
                    x=df['Day_of_Year'],
                    y=df['Indexed_Cumulative_Percent_Change'],
                    mode='lines',
                    name=f'{years} Years',
                    hoverinfo='none'
                )
            )

    # Add Seasonality data
    for trace in figure_data:
        fig.add_trace(trace, row=1, col=1)

    # Add OHLC data if visible
    if 'OHLC' in ohlc_visibility:
        ohlc_df = OHLCDataFetcher.fetch_ohlc_data(stored_market, current_year)
        if not ohlc_df.empty:
            fig.add_trace(
                go.Candlestick(
                    x=ohlc_df['Day_of_Year'],
                    open=ohlc_df['Open'].astype(float),
                    high=ohlc_df['High'].astype(float),
                    low=ohlc_df['Low'].astype(float),
                    close=ohlc_df['Close'].astype(float),
                    name=f'OHLC {current_year}',
                    yaxis='y2',
                    hovertext=ohlc_df.apply(
                        lambda row: f'Date: {row["Date"].strftime("%Y-%m-%d")}<br>Open: {row["Open"]}<br>High: {row["High"]}<br>Low: {row["Low"]}<br>Close: {row["Close"]}',
                        axis=1
                    ),
                    hoverinfo='text'
                ),
                row=1, col=1, secondary_y=True
            )
            fig.update_yaxes(title_text='OHLC Prices', row=1, col=1, secondary_y=True)

    # Add Open Interest data if visible
    if 'Open Interest' in open_interest_visibility:
        open_interest_df = OpenInterestDataFetcher.fetch_open_interest_data(stored_market, current_year)
        if not open_interest_df.empty:
            open_interest_df['open_interest_all'] = open_interest_df['open_interest_all'].astype(float)

            fig.add_trace(
                go.Scatter(
                    x=open_interest_df['Day_of_Year'],
                    y=open_interest_df['open_interest_all'],
                    mode='lines',
                    name='Open Interest',
                    line=dict(color='orange')
                ),
                row=2,
                col=1
            )

            y_min = open_interest_df['open_interest_all'].min()
            y_max = open_interest_df['open_interest_all'].max()
            fig.update_yaxes(title_text='Open Interest', row=2, col=1, range=[y_min, y_max])

    # Add Open Interest Percentages data if visible
    if 'OI Percentages' in oi_percentages_visibility:
        percentages_df = OpenInterestPercentagesFetcher.fetch_open_interest_percentages(stored_market, current_year)
        if not percentages_df.empty:
            fig.add_trace(
                go.Scatter(
                    x=percentages_df['Day_of_Year'],
                    y=percentages_df['pct_of_oi_noncomm_long_all'],
                    mode='lines',
                    name='% of OI Non-Commercials Long',
                    line=dict(color='blue')
                ),
                row=3,
                col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=percentages_df['Day_of_Year'],
                    y=percentages_df['pct_of_oi_noncomm_short_all'],
                    mode='lines',
                    name='% of OI Non-Commercials Short',
                    line=dict(color='red')
                ),
                row=3,
                col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=percentages_df['Day_of_Year'],
                    y=percentages_df['pct_of_oi_comm_long_all'],
                    mode='lines',
                    name='% of OI Commercials Long',
                    line=dict(color='green')
                ),
                row=3,
                col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=percentages_df['Day_of_Year'],
                    y=percentages_df['pct_of_oi_comm_short_all'],
                    mode='lines',
                    name='% of OI Commercials Short',
                    line=dict(color='purple')
                ),
                row=3,
                col=1
            )
            fig.update_yaxes(title_text='% of Open Interest', row=3, col=1)

    # Add Positions Change data if visible
    if 'Positions Change' in positions_change_visibility:
        positions_change_df = PositionsChangeDataFetcher.fetch_positions_change_data(stored_market, current_year)
        if not positions_change_df.empty:
            fig.add_trace(
                go.Scatter(
                    x=positions_change_df['Day_of_Year'],
                    y=positions_change_df['pct_change_noncomm_long'],
                    mode='lines',
                    name='% Change Non-Commercials Long',
                    line=dict(color='blue')
                ),
                row=4,
                col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=positions_change_df['Day_of_Year'],
                    y=positions_change_df['pct_change_noncomm_short'],
                    mode='lines',
                    name='% Change Non-Commercials Short',
                    line=dict(color='red')
                ),
                row=4,
                col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=positions_change_df['Day_of_Year'],
                    y=positions_change_df['pct_change_comm_long'],
                    mode='lines',
                    name='% Change Commercials Long',
                    line=dict(color='green')
                ),
                row=4,
                col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=positions_change_df['Day_of_Year'],
                    y=positions_change_df['pct_change_comm_short'],
                    mode='lines',
                    name='% Change Commercials Short',
                    line=dict(color='purple')
                ),
                row=4,
                col=1
            )
            fig.update_yaxes(title_text='Positions Change', row=4, col=1)

    # Add Net Positions data if visible
    if 'Net Positions' in net_positions_visibility:
        net_positions_df = NetPositionsDataFetcher.fetch_net_positions_data(stored_market, current_year)
        if not net_positions_df.empty:
            fig.add_trace(
                go.Scatter(
                    x=net_positions_df['Day_of_Year'],
                    y=net_positions_df['noncomm_net_positions'],
                    mode='lines',
                    name='Net Positions Non-Commercials',
                    line=dict(color='blue')
                ),
                row=5,
                col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=net_positions_df['Day_of_Year'],
                    y=net_positions_df['comm_net_positions'],
                    mode='lines',
                    name='Net Positions Commercials',
                    line=dict(color='red')
                ),
                row=5,
                col=1
            )
            fig.update_yaxes(title_text='Net Positions', row=5, col=1)

    # Add % Change in Net Positions data if visible
    if 'Net Positions Change' in net_positions_change_visibility:
        net_positions_change_df = PositionsChangeNetDataFetcher.fetch_positions_change_net_data(stored_market, current_year)
        if not net_positions_change_df.empty:
            fig.add_trace(
                go.Scatter(
                    x=net_positions_change_df['Day_of_Year'],
                    y=net_positions_change_df['pct_change_noncomm_net_positions'],
                    mode='lines',
                    name='% Change Non-Commercial Net Positions',
                    line=dict(color='orange')
                ),
                row=6,
                col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=net_positions_change_df['Day_of_Year'],
                    y=net_positions_change_df['pct_change_comm_net_positions'],
                    mode='lines',
                    name='% Change Commercial Net Positions',
                    line=dict(color='red')
                ),
                row=6,
                col=1
            )
            y_min = min(net_positions_change_df['pct_change_noncomm_net_positions'].min(),
                        net_positions_change_df['pct_change_comm_net_positions'].min())
            y_max = max(net_positions_change_df['pct_change_noncomm_net_positions'].max(),
                        net_positions_change_df['pct_change_comm_net_positions'].max())
            fig.update_yaxes(title_text='% Change in Net Positions', row=6, col=1, range=[y_min, y_max])

    # Add 26-Week Index data if visible
    if '26W Index' in index_26w_visibility:
        index_26w_df = Index26WDataFetcher.fetch_26w_index_data(stored_market, current_year)
        if not index_26w_df.empty:
            fig.add_trace(
                go.Scatter(
                    x=index_26w_df['Day_of_Year'],
                    y=index_26w_df['noncomm_26w_index'],
                    mode='lines',
                    name='Non-Commercials 26W Index',
                    line=dict(color='red')
                ),
                row=7,
                col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=index_26w_df['Day_of_Year'],
                    y=index_26w_df['comm_26w_index'],
                    mode='lines',
                    name='Commercials 26W Index',
                    line=dict(color='blue')
                ),
                row=7,
                col=1
            )
            fig.add_shape(
                dict(
                    type='line',
                    x0=index_26w_df['Day_of_Year'].min(),
                    x1=index_26w_df['Day_of_Year'].max(),
                    y0=50,
                    y1=50,
                    line=dict(color='gray', dash='dash')
                ),
                row=7,
                col=1
            )
            fig.update_yaxes(title_text='26-Week Index', row=7, col=1)

    # Update layout
    fig.update_layout(
        xaxis=dict(tickmode='array', tickvals=x_axis_ticks, ticktext=x_axis_tick_labels),
        shapes=shapes,
        xaxis_title='Day of Year',
        title=f'{stored_market} Data Overview'
    )

    # Hide the range slider for x-axis
    fig.update_xaxes(rangeslider=dict(visible=False), row=1, col=1)

    return fig