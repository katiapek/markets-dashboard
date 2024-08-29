# callbacks.py
from dash import Input, Output, State, ctx
import dash
import plotly.graph_objs as go
import plotly.subplots as sp
from layout_definitions import format_market_name
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
from scripts.config import market_tickers

# Constants for trace colors and default values
DEFAULT_MARKET = 'Australian Dollar'
DEFAULT_YEAR = 2024

COLORS = {
    'open_interest': 'orange',
    'oi_percentages_long': 'blue',
    'oi_percentages_short': 'red',
    'positions_change_long': 'blue',
    'positions_change_short': 'red',
    'net_positions_long': 'blue',
    'net_positions_short': 'red',
    'net_positions_change_long': 'blue',
    'net_positions_change_short': 'red',
    'index_26w_noncomm': 'red',
    'index_26w_comm': 'blue'
}

def add_trace(fig, x, y, name, row, col, mode='lines', line_color=None, secondary_y=False):
    """
    Add a trace to the figure.

    Args:
        fig (plotly.graph_objects.Figure): The figure to which the trace is added.
        x (list or array-like): X data for the trace.
        y (list or array-like): Y data for the trace.
        name (str): The name of the trace.
        row (int): Row index for the subplot.
        col (int): Column index for the subplot.
        mode (str): Mode of the trace (e.g., 'lines', 'markers').
        line_color (str): Color of the trace line.
        secondary_y (bool): Whether the trace should be added to the secondary y-axis.
    """
    trace = go.Scatter(x=x, y=y, mode=mode, name=name, line=dict(color=line_color))
    fig.add_trace(trace, row=row, col=col, secondary_y=secondary_y)

def add_candlestick_trace(fig, x, open, high, low, close, name, row, col):
    """
    Add a candlestick trace to the figure.

    Args:
        fig (plotly.graph_objects.Figure): The figure to which the trace is added.
        x (list or array-like): X data for the trace.
        open (list or array-like): Opening prices.
        high (list or array-like): High prices.
        low (list or array-like): Low prices.
        close (list or array-like): Closing prices.
        name (str): The name of the trace.
        row (int): Row index for the subplot.
        col (int): Column index for the subplot.
    """
    trace = go.Candlestick(x=x, open=open, high=high, low=low, close=close, name=name,
                           yaxis='y2', hoverinfo='text')
    fig.add_trace(trace, row=row, col=col, secondary_y=True)

def update_yaxis(fig, row, col, title, y_min=None, y_max=None, secondary_y=False):
    """
    Update the y-axis properties of a subplot.

    Args:
        fig (plotly.graph_objects.Figure): The figure to which the y-axis is updated.
        row (int): Row index for the subplot.
        col (int): Column index for the subplot.
        title (str): Title of the y-axis.
        y_min (float, optional): Minimum value for the y-axis range.
        y_max (float, optional): Maximum value for the y-axis range.
        secondary_y (bool): Whether the y-axis is secondary.
    """
    fig.update_yaxes(title_text=title, row=row, col=col, range=[y_min, y_max], secondary_y=secondary_y)

def add_shape(fig, x0, x1, y0, y1, row, col, color='gray', dash='dash'):
    """
    Add a shape to the figure.

    Args:
        fig (plotly.graph_objects.Figure): The figure to which the shape is added.
        x0 (float): Starting x-coordinate of the shape.
        x1 (float): Ending x-coordinate of the shape.
        y0 (float): Starting y-coordinate of the shape.
        y1 (float): Ending y-coordinate of the shape.
        row (int): Row index for the subplot.
        col (int): Column index for the subplot.
        color (str): Color of the shape.
        dash (str): Dash style of the shape.
    """
    fig.add_shape(type='line', x0=x0, x1=x1, y0=y0, y1=y1, line=dict(color=color, dash=dash), row=row, col=col)

def register_callbacks(app):
    """
    Register all callbacks for the Dash application.

    Args:
        app (dash.Dash): The Dash application instance.
    """
    @app.callback(
        Output('right-panel', 'className'),
        Input('toggle-button', 'n_clicks'),
        State('right-panel', 'className')
    )
    def toggle_panel(n_clicks, class_name):
        """
        Toggle the visibility of the right panel.

        Args:
            n_clicks (int): Number of button clicks.
            class_name (str): Current class name of the right panel.

        Returns:
            str: Updated class name for the right panel.
        """
        if n_clicks == 0:
            return ''
        return 'collapsed' if n_clicks % 2 == 1 else ''

    @app.callback(
        Output('stored-market', 'data'),
        [Input({'type': 'market-link', 'index': dash.dependencies.ALL}, 'n_clicks')]
    )
    def update_stored_market(n_clicks):
        """
        Update the stored market based on user selection.

        Args:
            n_clicks (list): List of click counts for each market link.

        Returns:
            str: The selected market name.
        """
        if ctx.triggered:
            triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
            if 'market-link' in triggered_id:
                triggered_ticker = eval(triggered_id).get('index')
                return next((name for name, ticker in market_tickers.items() if ticker == triggered_ticker),
                            DEFAULT_MARKET)
        return DEFAULT_MARKET

    @app.callback(
        Output('current-year', 'data'),
        [Input('prev-year-button', 'n_clicks'),
         Input('next-year-button', 'n_clicks')],
        [State('current-year', 'data')]
    )
    def update_year(n_clicks_prev, n_clicks_next, current_year):
        """
        Update the current year based on button clicks.

        Args:
            n_clicks_prev (int): Number of clicks on the previous year button.
            n_clicks_next (int): Number of clicks on the next year button.
            current_year (int): Current year.

        Returns:
            int: The updated year.
        """
        if ctx.triggered:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            if 'prev-year-button' in button_id:
                return max(1994, current_year - 1)
            elif 'next-year-button' in button_id:
                return min(2024, current_year + 1)
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
        """
        Update the combined chart based on user inputs.

        Args:
            n_clicks (list): List of click counts for each market link.
            selected_years (list): List of selected years.
            ohlc_visibility (list): List of visible OHLC options.
            open_interest_visibility (list): List of visible Open Interest options.
            oi_percentages_visibility (list): List of visible Open Interest Percentages options.
            positions_change_visibility (list): List of visible Positions Change options.
            net_positions_visibility (list): List of visible Net Positions options.
            net_positions_change_visibility (list): List of visible Net Positions Change options.
            index_26w_visibility (list): List of visible 26-Week Index options.
            stored_market (str): Currently stored market.
            current_year (int): Currently selected year.

        Returns:
            plotly.graph_objects.Figure: The updated figure.
        """
        # Determine the selected market based on the trigger
        if ctx.triggered:
            triggered = ctx.triggered[0]['prop_id'].split('.')[0]
            if 'market-link' in triggered:
                triggered_ticker = eval(triggered).get('index')
                stored_market = next((name for name, ticker in market_tickers.items() if ticker == triggered_ticker),
                                     DEFAULT_MARKET)

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
        for years in selected_years:
            df = SeasonalDataFetcher.fetch_seasonal_data(formatted_market_name, years)
            if not df.empty:
                add_trace(fig, df['Day_of_Year'], df['Indexed_Cumulative_Percent_Change'], f'{years} Years', row=1,
                          col=1)

        # Add OHLC data if visible
        if 'OHLC' in ohlc_visibility:
            ohlc_df = OHLCDataFetcher.fetch_ohlc_data(stored_market, current_year)
            if not ohlc_df.empty:
                add_candlestick_trace(fig, ohlc_df['Day_of_Year'], ohlc_df['Open'].astype(float),
                                      ohlc_df['High'].astype(float), ohlc_df['Low'].astype(float),
                                      ohlc_df['Close'].astype(float), f'OHLC {current_year}', row=1, col=1)
                update_yaxis(fig, row=1, col=1, title='OHLC Prices', secondary_y=True)

        # Add Open Interest data if visible
        if 'Open Interest' in open_interest_visibility:
            open_interest_df = OpenInterestDataFetcher.fetch_open_interest_data(stored_market, current_year)
            if not open_interest_df.empty:
                add_trace(fig, open_interest_df['Day_of_Year'], open_interest_df['open_interest_all'].astype(float),
                          'Open Interest', row=2, col=1, line_color=COLORS['open_interest'])
                y_min = open_interest_df['open_interest_all'].min()
                y_max = open_interest_df['open_interest_all'].max()
                update_yaxis(fig, row=2, col=1, title='Open Interest', y_min=y_min, y_max=y_max)

        # Add Open Interest Percentages data if visible
        if 'OI Percentages' in oi_percentages_visibility:
            percentages_df = OpenInterestPercentagesFetcher.fetch_open_interest_percentages(stored_market, current_year)
            if not percentages_df.empty:
                add_trace(fig, percentages_df['Day_of_Year'], percentages_df['pct_of_oi_noncomm_long_all'],
                          '% of OI Non-Commercials Long', row=3, col=1, line_color=COLORS['oi_percentages_long'])
                add_trace(fig, percentages_df['Day_of_Year'], percentages_df['pct_of_oi_noncomm_short_all'],
                          '% of OI Non-Commercials Short', row=3, col=1, line_color=COLORS['oi_percentages_short'])
                add_trace(fig, percentages_df['Day_of_Year'], percentages_df['pct_of_oi_comm_long_all'],
                          '% of OI Commercials Long', row=3, col=1, line_color=COLORS['oi_percentages_long'])
                add_trace(fig, percentages_df['Day_of_Year'], percentages_df['pct_of_oi_comm_short_all'],
                          '% of OI Commercials Short', row=3, col=1, line_color=COLORS['oi_percentages_short'])
                update_yaxis(fig, row=3, col=1, title='% of Open Interest')

        # Add Positions Change data if visible
        if 'Positions Change' in positions_change_visibility:
            positions_change_df = PositionsChangeDataFetcher.fetch_positions_change_data(stored_market, current_year)
            if not positions_change_df.empty:
                add_trace(fig, positions_change_df['Day_of_Year'], positions_change_df['pct_change_noncomm_long'],
                          '% Change Non-Commercials Long', row=4, col=1, line_color=COLORS['positions_change_long'])
                add_trace(fig, positions_change_df['Day_of_Year'], positions_change_df['pct_change_noncomm_short'],
                          '% Change Non-Commercials Short', row=4, col=1, line_color=COLORS['positions_change_short'])
                add_trace(fig, positions_change_df['Day_of_Year'], positions_change_df['pct_change_comm_long'],
                          '% Change Commercials Long', row=4, col=1, line_color=COLORS['positions_change_long'])
                add_trace(fig, positions_change_df['Day_of_Year'], positions_change_df['pct_change_comm_short'],
                          '% Change Commercials Short', row=4, col=1, line_color=COLORS['positions_change_short'])
                update_yaxis(fig, row=4, col=1, title='% Change in Positions')

        # Add Net Positions data if visible
        if 'Net Positions' in net_positions_visibility:
            net_positions_df = NetPositionsDataFetcher.fetch_net_positions_data(stored_market, current_year)
            if not net_positions_df.empty:
                add_trace(fig, net_positions_df['Day_of_Year'], net_positions_df['noncomm_net_positions'],
                          'Net Positions Non-Commercials', row=5, col=1, line_color=COLORS['net_positions_long'])
                add_trace(fig, net_positions_df['Day_of_Year'], net_positions_df['comm_net_positions'],
                          'Net Positions Commercials', row=5, col=1, line_color=COLORS['net_positions_short'])
                update_yaxis(fig, row=5, col=1, title='Net Positions')

        # Add Net Positions Change data if visible
        if 'Net Positions Change' in net_positions_change_visibility:
            net_positions_change_df = PositionsChangeNetDataFetcher.fetch_positions_change_net_data(stored_market,
                                                                                                    current_year)
            if not net_positions_change_df.empty:
                add_trace(fig, net_positions_change_df['Day_of_Year'],
                          net_positions_change_df['pct_change_noncomm_net_positions'],
                          '% Change Net Positions Non-Commercials', row=6, col=1, line_color=COLORS['net_positions_change_long'])
                add_trace(fig, net_positions_change_df['Day_of_Year'],
                          net_positions_change_df['pct_change_comm_net_positions'],
                          '% Change Net Positions Commercials', row=6, col=1, line_color=COLORS['net_positions_change_short'])
                update_yaxis(fig, row=6, col=1, title='% Change in Net Positions')

        # Add 26-Week Index data if visible
        if '26W Index' in index_26w_visibility:
            index_26w_df = Index26WDataFetcher.fetch_26w_index_data(stored_market, current_year)
            if not index_26w_df.empty:
                add_trace(fig, index_26w_df['Day_of_Year'], index_26w_df['noncomm_26w_index'],
                          'Non-Commercials 26W Index', row=7, col=1, line_color=COLORS['index_26w_noncomm'])
                add_trace(fig, index_26w_df['Day_of_Year'], index_26w_df['comm_26w_index'],
                          'Commercials 26W Index', row=7, col=1, line_color=COLORS['index_26w_comm'])
                add_shape(fig, index_26w_df['Day_of_Year'].min(), index_26w_df['Day_of_Year'].max(), 50, 50, row=7,
                          col=1)
                update_yaxis(fig, row=7, col=1, title='26-Week Index')

        fig.update_layout(title=f'{stored_market} Data Overview', height=2000, showlegend=True)

        return fig
