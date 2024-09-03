# callbacks.py
from dash import Input, Output, State, ctx
import dash
import plotly.graph_objs as go
import plotly.subplots as sp
import pandas as pd  # Import pandas for data manipulation
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
    trace = go.Scatter(x=x, y=y, mode=mode, name=name, line=dict(color=line_color))
    fig.add_trace(trace, row=row, col=col, secondary_y=secondary_y)

def add_candlestick_trace(fig, x, open, high, low, close, name, row, col):
    trace = go.Candlestick(x=x, open=open, high=high, low=low, close=close, name=name,
                           yaxis='y2', hoverinfo='text')
    fig.add_trace(trace, row=row, col=col, secondary_y=True)

def update_yaxis(fig, row, col, title, y_min=None, y_max=None, secondary_y=False):
    fig.update_yaxes(title_text=title, row=row, col=col, range=[y_min, y_max], secondary_y=secondary_y)

def add_shape(fig, x0, x1, y0, y1, row, col, color='gray', dash='dash'):
    fig.add_shape(type='line', x0=x0, x1=x1, y0=y0, y1=y1, line=dict(color=color, dash=dash), row=row, col=col)

def register_callbacks(app):

    # Callback to toggle the foldable menu for "Legacy - Combined"
    @app.callback(
        Output('legacy-combined-collapse', 'is_open'),
        [Input('legacy-combined-toggle', 'n_clicks')],
        [State('legacy-combined-collapse', 'is_open')]
    )
    def toggle_legacy_combined(n_clicks, is_open):
        """
        Toggle the visibility of the 'Legacy - Combined' section.

        Args:
            n_clicks (int): Number of clicks on the toggle button.
            is_open (bool): Current state of the collapse (open/closed).

        Returns:
            bool: Updated state of the collapse.
        """
        if n_clicks:
            return not is_open
        return is_open

    @app.callback(
        Output('legacy-futures-only-collapse', 'is_open'),
        [Input('legacy-futures-only-toggle', 'n_clicks')],
        [State('legacy-futures-only-collapse', 'is_open')]
    )
    def toggle_legacy_futures_only(n_clicks, is_open):
        """
        Toggle the visibility of the 'Legacy - Futures Only' section.

        Args:
            n_clicks (int): Number of clicks on the toggle button.
            is_open (bool): Current state of the collapse (open/closed).

        Returns:
            bool: Updated state of the collapse.
        """
        if n_clicks:
            return not is_open
        return is_open

    @app.callback(
        Output('active-subplots', 'data'),
        [Input('open-interest-legacy-combined-checklist', 'value'),
         Input('oi-percentages-legacy-combined-checklist', 'value'),
         Input('positions-change-legacy-combined-checklist', 'value'),
         Input('net-positions-legacy-combined-checklist', 'value'),
         Input('net-positions-change-legacy-combined-checklist', 'value'),
         Input('26w-index-legacy-combined-checklist', 'value'),
         Input('open-interest-legacy-futures-only-checklist', 'value'),
         Input('oi-percentages-legacy-futures-only-checklist', 'value'),
         Input('positions-change-legacy-futures-only-checklist', 'value'),
         Input('net-positions-legacy-futures-only-checklist', 'value'),
         Input('net-positions-change-legacy-futures-only-checklist', 'value'),
         Input('26w-index-legacy-futures-only-checklist', 'value')],
        prevent_initial_call=True
    )
    def update_active_subplots(*values):
        active_subplots = []
        # For COT Legacy Combined
        if 'Open Interest' in values[0]:
            active_subplots.append(('Open Interest', '_cot_legacy_combined'))
        if 'OI Percentages' in values[1]:
            active_subplots.append(('OI Percentages', '_cot_legacy_combined'))
        if 'Positions Change' in values[2]:
            active_subplots.append(('Positions Change', '_cot_legacy_combined'))
        if 'Net Positions' in values[3]:
            active_subplots.append(('Net Positions', '_cot_legacy_combined'))
        if 'Net Positions Change' in values[4]:
            active_subplots.append(('Net Positions Change', '_cot_legacy_combined'))
        if '26W Index' in values[5]:
            active_subplots.append(('26W Index', '_cot_legacy_combined'))
        # For COT Legacy Futures Only
        if 'Open Interest' in values[6]:
            active_subplots.append(('Open Interest', '_cot_legacy_futures_only'))
        if 'OI Percentages' in values[7]:
            active_subplots.append(('OI Percentages', '_cot_legacy_futures_only'))
        if 'Positions Change' in values[8]:
            active_subplots.append(('Positions Change', '_cot_legacy_futures_only'))
        if 'Net Positions' in values[9]:
            active_subplots.append(('Net Positions', '_cot_legacy_futures_only'))
        if 'Net Positions Change' in values[10]:
            active_subplots.append(('Net Positions Change', '_cot_legacy_futures_only'))
        if '26W Index' in values[11]:
            active_subplots.append(('26W Index', '_cot_legacy_futures_only'))
        return active_subplots

    @app.callback(
        Output('combined-chart', 'figure'),
        [Input('active-subplots', 'data'),
         Input('years-checklist', 'value'),
         Input('ohlc-checklist', 'value'),
         Input('stored-market', 'data'),
         Input('current-year', 'data')],
        prevent_initial_call=False  # Ensure the callback runs initially
    )
    def update_graph(active_subplots, selected_years, ohlc_visibility, stored_market, current_year):
        num_rows = 1 + len(active_subplots)
        specs = [[{'secondary_y': True}]] + [[{'secondary_y': False}] for _ in range(len(active_subplots))]
        fig = sp.make_subplots(rows=num_rows, cols=1, shared_xaxes=True, vertical_spacing=0.1, specs=specs)

        # Add Seasonality chart
        for years in selected_years:
            df = SeasonalDataFetcher.fetch_seasonal_data(format_market_name(stored_market), years)
            if not df.empty:
                df = df.apply(pd.to_numeric, errors='coerce')
                add_trace(fig, df['Day_of_Year'], df['Indexed_Cumulative_Percent_Change'], f'{years} Years', row=1,
                          col=1)

        # Add OHLC chart
        if 'OHLC' in ohlc_visibility:
            ohlc_df = OHLCDataFetcher.fetch_ohlc_data(stored_market, current_year)
            if not ohlc_df.empty:
                ohlc_df = ohlc_df.apply(pd.to_numeric, errors='coerce')
                add_candlestick_trace(fig, ohlc_df['Day_of_Year'], ohlc_df['Open'], ohlc_df['High'], ohlc_df['Low'],
                                      ohlc_df['Close'], f'OHLC {current_year}', row=1, col=1)
                update_yaxis(fig, row=1, col=1, title='OHLC Prices', secondary_y=True)

        row_index = 2
        for subplot, table_suffix in active_subplots:
            if subplot == 'Open Interest':
                df = OpenInterestDataFetcher.fetch_open_interest_data(stored_market, current_year, table_suffix)
                if not df.empty:
                    df = df.apply(pd.to_numeric, errors='coerce')
                    add_trace(fig, df['Day_of_Year'], df['open_interest_all'], f'Open Interest ({table_suffix})',
                              row=row_index, col=1,
                              line_color=COLORS['open_interest'])
                    update_yaxis(fig, row=row_index, col=1, title='Open Interest')

            elif subplot == 'OI Percentages':
                df = OpenInterestPercentagesFetcher.fetch_open_interest_percentages(stored_market, current_year,
                                                                                    table_suffix)
                if not df.empty:
                    df = df.apply(pd.to_numeric, errors='coerce')
                    add_trace(fig, df['Day_of_Year'], df['pct_of_oi_noncomm_long_all'],
                              f'% of OI Non-Commercials Long ({table_suffix})', row=row_index, col=1,
                              line_color=COLORS['oi_percentages_long'])
                    add_trace(fig, df['Day_of_Year'], df['pct_of_oi_noncomm_short_all'],
                              f'% of OI Non-Commercials Short ({table_suffix})', row=row_index, col=1,
                              line_color=COLORS['oi_percentages_short'])
                    add_trace(fig, df['Day_of_Year'], df['pct_of_oi_comm_long_all'],
                              f'% of OI Commercials Long ({table_suffix})', row=row_index, col=1,
                              line_color=COLORS['oi_percentages_long'])
                    add_trace(fig, df['Day_of_Year'], df['pct_of_oi_comm_short_all'],
                              f'% of OI Commercials Short ({table_suffix})', row=row_index, col=1,
                              line_color=COLORS['oi_percentages_short'])
                    update_yaxis(fig, row=row_index, col=1, title='% of Open Interest')

            # Continue adding cases for other subplots with the dynamic `table_suffix`

            elif subplot == 'Positions Change':
                df = PositionsChangeDataFetcher.fetch_positions_change_data(stored_market, current_year, table_suffix)
                if not df.empty:
                    df = df.apply(pd.to_numeric, errors='coerce')
                    add_trace(fig, df['Day_of_Year'], df['pct_change_noncomm_long'],
                              f'% Change Non-Commercials Long ({table_suffix})', row=row_index, col=1,
                              line_color=COLORS['positions_change_long'])
                    add_trace(fig, df['Day_of_Year'], df['pct_change_noncomm_short'],
                              f'% Change Non-Commercials Short ({table_suffix})', row=row_index, col=1,
                              line_color=COLORS['positions_change_short'])
                    add_trace(fig, df['Day_of_Year'], df['pct_change_comm_long'],
                              f'% Change Commercials Long ({table_suffix})', row=row_index, col=1,
                              line_color=COLORS['positions_change_long'])
                    add_trace(fig, df['Day_of_Year'], df['pct_change_comm_short'],
                              f'% Change Commercials Short ({table_suffix})', row=row_index, col=1,
                              line_color=COLORS['positions_change_short'])
                    update_yaxis(fig, row=row_index, col=1, title='% Change in Positions')

            elif subplot == 'Net Positions':
                df = NetPositionsDataFetcher.fetch_net_positions_data(stored_market, current_year, table_suffix)
                if not df.empty:
                    df = df.apply(pd.to_numeric, errors='coerce')
                    add_trace(fig, df['Day_of_Year'], df['noncomm_net_positions'],
                              f'Net Positions Non-Commercials ({table_suffix})', row=row_index, col=1,
                              line_color=COLORS['net_positions_long'])
                    add_trace(fig, df['Day_of_Year'], df['comm_net_positions'],
                              f'Net Positions Commercials ({table_suffix})', row=row_index, col=1,
                              line_color=COLORS['net_positions_short'])
                    update_yaxis(fig, row=row_index, col=1, title='Net Positions')

            elif subplot == 'Net Positions Change':
                df = PositionsChangeNetDataFetcher.fetch_positions_change_net_data(stored_market, current_year, table_suffix)
                if not df.empty:
                    df = df.apply(pd.to_numeric, errors='coerce')
                    add_trace(fig, df['Day_of_Year'],
                              df['pct_change_noncomm_net_positions'],
                              f'% Change Net Positions Non-Commercials ({table_suffix})', row=row_index, col=1,
                              line_color=COLORS['net_positions_change_long'])
                    add_trace(fig, df['Day_of_Year'],
                              df['pct_change_comm_net_positions'],
                              f'% Change Net Positions Commercials ({table_suffix})', row=row_index, col=1,
                              line_color=COLORS['net_positions_change_short'])
                    update_yaxis(fig, row=row_index, col=1, title='% Change in Net Positions')

            elif subplot == '26W Index':
                df = Index26WDataFetcher.fetch_26w_index_data(stored_market, current_year, table_suffix)
                if not df.empty:
                    df = df.apply(pd.to_numeric, errors='coerce')
                    add_trace(fig, df['Day_of_Year'], df['noncomm_26w_index'],
                              f'Non-Commercials 26W Index ({table_suffix})', row=row_index, col=1, line_color=COLORS['index_26w_noncomm'])
                    add_trace(fig, df['Day_of_Year'], df['comm_26w_index'],
                              f'Commercials 26W Index ({table_suffix})', row=row_index, col=1, line_color=COLORS['index_26w_comm'])
                    add_shape(fig, df['Day_of_Year'].min(), df['Day_of_Year'].max(), 50, 50, row=row_index, col=1)
                    update_yaxis(fig, row=row_index, col=1, title='26-Week Index')

            row_index += 1

        # Hide the range slider for x-axis
        fig.update_xaxes(rangeslider=dict(visible=False), row=1, col=1)

        fig.update_layout(height=300 + 200 * len(active_subplots), title=f'{stored_market} Data Overview')
        return fig

    @app.callback(
        Output('right-panel', 'className'),
        Input('toggle-button', 'n_clicks'),
        State('right-panel', 'className')
    )
    def toggle_panel(n_clicks, class_name):
        if n_clicks == 0:
            return ''
        return 'collapsed' if n_clicks % 2 == 1 else ''

    @app.callback(
        Output('stored-market', 'data'),
        [Input({'type': 'market-link', 'index': dash.dependencies.ALL}, 'n_clicks')]
    )
    def update_stored_market(n_clicks):
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
        if ctx.triggered:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            if 'prev-year-button' in button_id:
                return max(1994, current_year - 1)
            elif 'next-year-button' in button_id:
                return min(2024, current_year + 1)
        return current_year
