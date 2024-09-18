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
    'comm_long': 'red',
    'comm_short': 'pink',
    'noncomm_long': 'blue',
    'noncomm_short': 'lightblue',
    'other_long': 'green',
    'other_short': 'lightgreen',
}

def add_trace(fig, x, y, name, row, col, mode='lines', line_color=None, secondary_y=False, chart_type='line', opacity=1):
    """
    Adds a trace to the figure. Handles both line and bar charts.

    Args:
        fig: The figure object.
        x: X-axis data.
        y: Y-axis data.
        name: Name of the trace.
        row: Row position of the trace in the figure.
        col: Column position of the trace in the figure.
        mode: The drawing mode for line charts ('lines', 'markers', etc.).
        line_color: Color of the line or bar.
        secondary_y: Boolean to use the secondary y-axis.
        chart_type: Type of chart ('line' or 'bar').
    """
    if chart_type == 'line':
        trace = go.Scatter(x=x, y=y, mode=mode, name=name, line=dict(color=line_color), showlegend=False, opacity=opacity, connectgaps=True)
    elif chart_type == 'bar':
        trace = go.Bar(x=x, y=y, name=name, marker=dict(color=line_color), showlegend=False, opacity=opacity)

    fig.add_trace(trace, row=row, col=col, secondary_y=secondary_y)


def add_candlestick_trace(fig, x, open, high, low, close, name, row, col, secondary_y=False):
    trace = go.Candlestick(x=x, open=open, high=high, low=low, close=close, name=name,
                           yaxis='y2', hoverinfo='text', showlegend=False, increasing_line_color="white", decreasing_line_color="white",
                           increasing_fillcolor="white", decreasing_fillcolor="black")
    fig.add_trace(trace, row=row, col=col, secondary_y=secondary_y)
    # Ensure the y-axis is fixed
    fig.update_yaxes(
        fixedrange=True,  # Disable y-axis zoom
        row=row,
        col=col
    )

def update_yaxis(fig, row, col, title, y_min=None, y_max=None, secondary_y=False):
    fig.update_yaxes(title_text=title, row=row, col=col, range=[y_min, y_max], secondary_y=secondary_y)

def add_shape(fig, x0, x1, y0, y1, row, col, color='gray', dash='dash'):
    fig.add_shape(type='line', x0=x0, x1=x1, y0=y0, y1=y1, line=dict(color=color, dash=dash), row=row, col=col)

def register_callbacks(app):

    # Callback to toggle the foldable menu for "Legacy - Combined"
    @app.callback(
        Output('ohlc-cycles-collapse', 'is_open'),
        [Input('ohlc-cycles-toggle', 'n_clicks')],
        [State('ohlc-cycles-collapse', 'is_open')]
    )
    def toggle_ohlc_cycles(n_clicks, is_open):
        if n_clicks:
            return not is_open
        return is_open

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
        Output('disaggregated-combined-collapse', 'is_open'),
        [Input('disaggregated-combined-toggle', 'n_clicks')],
        [State('disaggregated-combined-collapse', 'is_open')]
    )
    def toggle_disaggregated_combined(n_clicks, is_open):
        if n_clicks:
            return not is_open
        return is_open

    @app.callback(
        Output('disaggregated-futures-only-collapse', 'is_open'),
        [Input('disaggregated-futures-only-toggle', 'n_clicks')],
        [State('disaggregated-futures-only-collapse', 'is_open')]
    )
    def toggle_disaggregated_futures_only(n_clicks, is_open):
        if n_clicks:
            return not is_open
        return is_open

    @app.callback(
        Output('tff-combined-collapse', 'is_open'),
        [Input('tff-combined-toggle', 'n_clicks')],
        [State('tff-combined-collapse', 'is_open')]
    )
    def toggle_disaggregated_combined(n_clicks, is_open):
        if n_clicks:
            return not is_open
        return is_open

    @app.callback(
        Output('tff-futures-only-collapse', 'is_open'),
        [Input('tff-futures-only-toggle', 'n_clicks')],
        [State('tff-futures-only-collapse', 'is_open')]
    )
    def toggle_disaggregated_futures_only(n_clicks, is_open):
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
         Input('26w-index-legacy-futures-only-checklist', 'value'),
         Input('open-interest-disaggregated-combined-checklist', 'value'),
         Input('oi-percentages-disaggregated-combined-checklist', 'value'),
         Input('positions-change-disaggregated-combined-checklist', 'value'),
         Input('net-positions-disaggregated-combined-checklist', 'value'),
         Input('net-positions-change-disaggregated-combined-checklist', 'value'),
         Input('26w-index-disaggregated-combined-checklist', 'value'),
         Input('open-interest-disaggregated-futures-only-checklist', 'value'),
         Input('oi-percentages-disaggregated-futures-only-checklist', 'value'),
         Input('positions-change-disaggregated-futures-only-checklist', 'value'),
         Input('net-positions-disaggregated-futures-only-checklist', 'value'),
         Input('net-positions-change-disaggregated-futures-only-checklist', 'value'),
         Input('26w-index-disaggregated-futures-only-checklist', 'value'),
         Input('open-interest-tff-combined-checklist', 'value'),
         Input('oi-percentages-tff-combined-checklist', 'value'),
         Input('positions-change-tff-combined-checklist', 'value'),
         Input('net-positions-tff-combined-checklist', 'value'),
         Input('net-positions-change-tff-combined-checklist', 'value'),
         Input('26w-index-tff-combined-checklist', 'value'),
         Input('open-interest-tff-futures-only-checklist', 'value'),
         Input('oi-percentages-tff-futures-only-checklist', 'value'),
         Input('positions-change-tff-futures-only-checklist', 'value'),
         Input('net-positions-tff-futures-only-checklist', 'value'),
         Input('net-positions-change-tff-futures-only-checklist', 'value'),
         Input('26w-index-tff-futures-only-checklist', 'value'),
         ],

        prevent_initial_call=True
    )
    def update_active_subplots(*values):
        active_subplots = []
        # For COT Legacy Combined
        if 'Open Interest' in values[0]:
            active_subplots.append(('Open Interest', '_cot_legacy_combined', 'legacy'))
        if 'OI Percentages' in values[1]:
            active_subplots.append(('OI Percentages', '_cot_legacy_combined', 'legacy'))
        if 'Positions Change' in values[2]:
            active_subplots.append(('Positions Change', '_cot_legacy_combined', 'legacy'))
        if 'Net Positions' in values[3]:
            active_subplots.append(('Net Positions', '_cot_legacy_combined', 'legacy'))
        if 'Net Positions Change' in values[4]:
            active_subplots.append(('Net Positions Change', '_cot_legacy_combined', 'legacy'))
        if '26W Index' in values[5]:
            active_subplots.append(('26W Index', '_cot_legacy_combined', 'legacy'))
        # For COT Legacy Futures Only
        if 'Open Interest' in values[6]:
            active_subplots.append(('Open Interest', '_cot_legacy_futures_only', 'legacy'))
        if 'OI Percentages' in values[7]:
            active_subplots.append(('OI Percentages', '_cot_legacy_futures_only', 'legacy'))
        if 'Positions Change' in values[8]:
            active_subplots.append(('Positions Change', '_cot_legacy_futures_only', 'legacy'))
        if 'Net Positions' in values[9]:
            active_subplots.append(('Net Positions', '_cot_legacy_futures_only', 'legacy'))
        if 'Net Positions Change' in values[10]:
            active_subplots.append(('Net Positions Change', '_cot_legacy_futures_only', 'legacy'))
        if '26W Index' in values[11]:
            active_subplots.append(('26W Index', '_cot_legacy_futures_only', 'legacy'))
        # For COT Disaggregated Combined
        if 'Open Interest' in values[12]:
            active_subplots.append(('Open Interest', '_cot_disaggregated_combined', 'disaggregated'))
        if 'OI Percentages' in values[13]:
            active_subplots.append(('OI Percentages', '_cot_disaggregated_combined', 'disaggregated'))
        if 'Positions Change' in values[14]:
            active_subplots.append(('Positions Change', '_cot_disaggregated_combined', 'disaggregated'))
        if 'Net Positions' in values[15]:
            active_subplots.append(('Net Positions', '_cot_disaggregated_combined', 'disaggregated'))
        if 'Net Positions Change' in values[16]:
            active_subplots.append(('Net Positions Change', '_cot_disaggregated_combined', 'disaggregated'))
        if '26W Index' in values[17]:
            active_subplots.append(('26W Index', '_cot_disaggregated_combined', 'disaggregated'))
        # For COT Disaggregated Futures Only
        if 'Open Interest' in values[18]:
            active_subplots.append(('Open Interest', '_cot_disaggregated_futures_only', 'disaggregated'))
        if 'OI Percentages' in values[19]:
            active_subplots.append(('OI Percentages', '_cot_disaggregated_futures_only', 'disaggregated'))
        if 'Positions Change' in values[20]:
            active_subplots.append(('Positions Change', '_cot_disaggregated_futures_only', 'disaggregated'))
        if 'Net Positions' in values[21]:
            active_subplots.append(('Net Positions', '_cot_disaggregated_futures_only', 'disaggregated'))
        if 'Net Positions Change' in values[22]:
            active_subplots.append(('Net Positions Change', '_cot_disaggregated_futures_only', 'disaggregated'))
        if '26W Index' in values[23]:
            active_subplots.append(('26W Index', '_cot_disaggregated_futures_only', 'disaggregated'))

        # For COT TFF Combined
        if 'Open Interest' in values[24]:
            active_subplots.append(('Open Interest', '_cot_tff_combined', 'tff'))
        if 'OI Percentages' in values[25]:
            active_subplots.append(('OI Percentages', '_cot_tff_combined', 'tff'))
        if 'Positions Change' in values[26]:
            active_subplots.append(('Positions Change', '_cot_tff_combined', 'tff'))
        if 'Net Positions' in values[27]:
            active_subplots.append(('Net Positions', '_cot_tff_combined', 'tff'))
        if 'Net Positions Change' in values[28]:
            active_subplots.append(('Net Positions Change', '_cot_tff_combined', 'tff'))
        if '26W Index' in values[29]:
            active_subplots.append(('26W Index', '_cot_tff_combined', 'tff'))
        # For COT TFF Futures Only
        if 'Open Interest' in values[30]:
            active_subplots.append(('Open Interest', '_cot_tff_futures_only', 'tff'))
        if 'OI Percentages' in values[31]:
            active_subplots.append(('OI Percentages', '_cot_tff_futures_only', 'tff'))
        if 'Positions Change' in values[32]:
            active_subplots.append(('Positions Change', '_cot_tff_futures_only', 'tff'))
        if 'Net Positions' in values[33]:
            active_subplots.append(('Net Positions', '_cot_tff_futures_only', 'tff'))
        if 'Net Positions Change' in values[34]:
            active_subplots.append(('Net Positions Change', '_cot_tff_futures_only', 'tff'))
        if '26W Index' in values[35]:
            active_subplots.append(('26W Index', '_cot_tff_futures_only', 'tff'))
        return active_subplots

    @app.callback(
        Output('combined-chart', 'figure'),
        [Input('active-subplots', 'data'),
         Input('years-checklist', 'value'),
         Input('ohlc-checklist', 'value'),
         Input('stored-market', 'data'),
         Input('current-year', 'data')],
        prevent_initial_call=False
    )
    def update_graph(active_subplots, selected_years, ohlc_visibility, stored_market, current_year):
        num_rows = 1 + len(active_subplots)
        specs = [[{'secondary_y': True}]] + [[{'secondary_y': False}] for _ in range(len(active_subplots))]

        # Calculate row heights dynamically
        initial_height = 800  # initial total height when only the OHLC/Seasonality chart is shown
        total_height = initial_height

        # Allocate more height to the first row initially
        row_heights = [0.6] + [0.4 / len(active_subplots) for _ in range(len(active_subplots))]

        fig = sp.make_subplots(rows=num_rows, cols=1, shared_xaxes=True, vertical_spacing=0.0, specs=specs,
                               row_heights=row_heights)

        # Add OHLC chart
        if 'OHLC' in ohlc_visibility:
            ohlc_df = OHLCDataFetcher.fetch_ohlc_data(stored_market, current_year)
            if not ohlc_df.empty:
                # Use the correctly formatted 'Date' column for the x-axis
                add_candlestick_trace(fig, ohlc_df['Date'], ohlc_df['Open'], ohlc_df['High'], ohlc_df['Low'],
                                      ohlc_df['Close'], f'OHLC {current_year}', row=1, col=1, secondary_y=False)

                # Build a complete timeline and identify missing dates for OHLC chart
                dt_all = pd.date_range(start=ohlc_df['Date'].min(), end=ohlc_df['Date'].max())
                dt_obs = ohlc_df['Date'].dt.strftime("%Y-%m-%d").tolist()
                dt_breaks = [d for d in dt_all.strftime("%Y-%m-%d").tolist() if d not in dt_obs]

                # Apply rangebreaks only for the OHLC chart
                fig.update_xaxes(rangebreaks=[dict(values=dt_breaks)], row=1, col=1)

        # Add Seasonality chart
        for years in selected_years:
            df = SeasonalDataFetcher.fetch_seasonal_data(format_market_name(stored_market), years, current_year)
            if not df.empty:
                # Connect the lines even if there are missing dates
                add_trace(fig, df['Date'], df['Indexed_Cumulative_Percent_Change'], f'{years} Years', row=1,
                          col=1, opacity=0.6, secondary_y=True)

        row_index = 2
        for subplot, table_suffix, report_type in active_subplots:
            if subplot == 'Open Interest':
                df = OpenInterestDataFetcher.fetch_open_interest_data(stored_market, current_year, table_suffix,
                                                                      report_type)

                if not df.empty:
                    if not df.empty:

                        df = df.apply(pd.to_numeric, errors='coerce')
                        df['Date'] = pd.to_datetime(df['Date'])  # Convert to datetime format if needed
                        add_trace(fig, df['Date'], df['open_interest_all'], f'Open Interest ({table_suffix})',
                                  row=row_index, col=1, line_color=COLORS['open_interest'])
                        update_yaxis(fig, row=row_index, col=1, title='Open Interest')

            elif subplot == 'OI Percentages':
                df = OpenInterestPercentagesFetcher.fetch_open_interest_percentages(
                    stored_market, current_year, table_suffix, report_type
                )

                if not df.empty:
                    if report_type == 'legacy':
                        # Add traces for Legacy report
                        add_trace(fig, df['Date'], df['pct_of_oi_noncomm_long_all'],
                                  f'% of OI Non-Commercials Long ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'])
                        add_trace(fig, df['Date'], df['pct_of_oi_noncomm_short_all'],
                                  f'% of OI Non-Commercials Short ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_short'])
                        add_trace(fig, df['Date'], df['pct_of_oi_comm_long_all'],
                                  f'% of OI Commercials Long ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_long'])
                        add_trace(fig, df['Date'], df['pct_of_oi_comm_short_all'],
                                  f'% of OI Commercials Short ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_short'])
                        update_yaxis(fig, row=row_index, col=1, title='% of Open Interest')

                    elif report_type == 'disaggregated':
                        # Add traces for Disaggregated report
                        add_trace(fig, df['Date'], df['pct_of_oi_m_money_long_all'],
                                  f'% of OI Managed Money Long ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'])
                        add_trace(fig, df['Date'], df['pct_of_oi_m_money_short_all'],
                                  f'% of OI Managed Money Short ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_short'])
                        add_trace(fig, df['Date'], df['pct_of_oi_prod_merc_long'],
                                  f'% of OI Producers/Merchants Long ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_long'])
                        add_trace(fig, df['Date'], df['pct_of_oi_prod_merc_short'],
                                  f'% of OI Producers/Merchants Short ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_short'])
                        add_trace(fig, df['Date'], df['pct_of_oi_swap_long_all'],
                                  f'% of OI Swap Dealers Long ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['other_long'])
                        add_trace(fig, df['Date'], df['pct_of_oi_swap_short_all'],
                                  f'% of OI Swap Dealers Short ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['other_short'])
                        update_yaxis(fig, row=row_index, col=1, title='% of Open Interest')

                    elif report_type == 'tff':
                        # Add traces for TFF report
                        add_trace(fig, df['Date'], df['pct_of_oi_lev_money_long'],
                                  f'% of OI Managed Money Long ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'])
                        add_trace(fig, df['Date'], df['pct_of_oi_lev_money_short'],
                                  f'% of OI Managed Money Short ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_short'])
                        add_trace(fig, df['Date'], df['pct_of_oi_asset_mgr_long'],
                                  f'% of OI Producers/Merchants Long ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_long'])
                        add_trace(fig, df['Date'], df['pct_of_oi_asset_mgr_short'],
                                  f'% of OI Producers/Merchants Short ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_short'])
                        add_trace(fig, df['Date'], df['pct_of_oi_dealer_long_all'],
                                  f'% of OI Swap Dealers Long ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['other_long'])
                        add_trace(fig, df['Date'], df['pct_of_oi_dealer_short_all'],
                                  f'% of OI Swap Dealers Short ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['other_short'])
                        update_yaxis(fig, row=row_index, col=1, title='% of Open Interest')

            elif subplot == 'Positions Change':
                df = PositionsChangeDataFetcher.fetch_positions_change_data(stored_market, current_year, table_suffix,
                                                                            report_type)
                if not df.empty:
                    df = df.apply(pd.to_numeric, errors='coerce')
                    df['Date'] = pd.to_datetime(df['Date'])

                    if report_type == 'legacy':

                        add_trace(fig, df['Date'], df['pct_change_noncomm_long'],
                                  f'% Change Non-Commercials Long ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'], chart_type='bar')
                        add_trace(fig, df['Date'], df['pct_change_noncomm_short'],
                                  f'% Change Non-Commercials Short ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_short'], chart_type='bar')
                        add_trace(fig, df['Date'], df['pct_change_comm_long'],
                                  f'% Change Commercials Long ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_long'], chart_type='bar')
                        add_trace(fig, df['Date'], df['pct_change_comm_short'],
                                  f'% Change Commercials Short ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_short'], chart_type='bar')
                        update_yaxis(fig, row=row_index, col=1, title='% Change in Positions')

                    elif report_type == 'disaggregated':
                        add_trace(fig, df['Date'], df['pct_change_m_money_long'],
                                  f'% Change Managed Money Long ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'], chart_type='bar')
                        add_trace(fig, df['Date'], df['pct_change_m_money_short'],
                                  f'% Change Managed Money Short ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_short'], chart_type='bar')
                        add_trace(fig, df['Date'], df['pct_change_prod_merc_long'],
                                  f'% Change Producers / Merchants Long ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_long'], chart_type='bar')
                        add_trace(fig, df['Date'], df['pct_change_prod_merc_short'],
                                  f'% Change Producers / Merchants Short ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_short'], chart_type='bar')
                        add_trace(fig, df['Date'], df['pct_change_swap_long'],
                                  f'% Change Swap Dealers Long ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['other_long'], chart_type='bar')
                        add_trace(fig, df['Date'], df['pct_change_swap_short'],
                                  f'% Change Swap Dealers Short ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['other_short'], chart_type='bar')
                        update_yaxis(fig, row=row_index, col=1, title='% Change in Positions')

                    elif report_type == 'tff':
                        add_trace(fig, df['Date'], df['pct_change_lev_money_long'],
                                  f'% Change Managed Money Long ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'], chart_type='bar')
                        add_trace(fig, df['Date'], df['pct_change_lev_money_short'],
                                  f'% Change Managed Money Short ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_short'], chart_type='bar')
                        add_trace(fig, df['Date'], df['pct_change_asset_mgr_long'],
                                  f'% Change Producers / Merchants Long ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_long'], chart_type='bar')
                        add_trace(fig, df['Date'], df['pct_change_asset_mgr_short'],
                                  f'% Change Producers / Merchants Short ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_short'], chart_type='bar')
                        add_trace(fig, df['Date'], df['pct_change_dealer_long'],
                                  f'% Change Swap Dealers Long ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['other_long'], chart_type='bar')
                        add_trace(fig, df['Date'], df['pct_change_dealer_short'],
                                  f'% Change Swap Dealers Short ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['other_short'], chart_type='bar')
                        update_yaxis(fig, row=row_index, col=1, title='% Change in Positions')

            elif subplot == 'Net Positions':
                df = NetPositionsDataFetcher.fetch_net_positions_data(stored_market, current_year, table_suffix,
                                                                      report_type)
                if not df.empty:
                    df = df.apply(pd.to_numeric, errors='coerce')
                    df['Date'] = pd.to_datetime(df['Date'])

                    if report_type == 'legacy':
                        add_trace(fig, df['Date'], df['noncomm_net_positions'],
                                  f'Net Positions Non-Commercials ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'])
                        add_trace(fig, df['Date'], df['comm_net_positions'],
                                  f'Net Positions Commercials ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_long'])
                        update_yaxis(fig, row=row_index, col=1, title='Net Positions')

                    elif report_type == 'disaggregated':
                        add_trace(fig, df['Date'], df['m_money_net_positions'],
                                  f'Net Positions Managed Money ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'])
                        add_trace(fig, df['Date'], df['prod_merc_net_positions'],
                                  f'Net Positions Producers / Merchants ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_long'])
                        add_trace(fig, df['Date'], df['swap_net_positions'],
                                  f'Net Positions Swap Dealers ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['other_long'])
                        update_yaxis(fig, row=row_index, col=1, title='Net Positions')

                    elif report_type == 'tff':
                        add_trace(fig, df['Date'], df['lev_money_net_positions'],
                                  f'Net Positions Managed Money ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'])
                        add_trace(fig, df['Date'], df['asset_mgr_net_positions'],
                                  f'Net Positions Producers / Merchants ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_long'])
                        add_trace(fig, df['Date'], df['dealer_net_positions'],
                                  f'Net Positions Swap Dealers ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['other_long'])
                        update_yaxis(fig, row=row_index, col=1, title='Net Positions')

            elif subplot == 'Net Positions Change':
                df = PositionsChangeNetDataFetcher.fetch_positions_change_net_data(stored_market, current_year,
                                                                                   table_suffix, report_type)
                if not df.empty:
                    df = df.apply(pd.to_numeric, errors='coerce')
                    df['Date'] = pd.to_datetime(df['Date'])

                    if report_type == 'legacy':
                        add_trace(fig, df['Date'],
                                  df['pct_change_noncomm_net_positions'],
                                  f'% Change Net Positions Non-Commercials ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'], chart_type='bar')
                        add_trace(fig, df['Date'],
                                  df['pct_change_comm_net_positions'],
                                  f'% Change Net Positions Commercials ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_long'], chart_type='bar')
                        update_yaxis(fig, row=row_index, col=1, title='% Change in Net Positions')

                    elif report_type == 'disaggregated':
                        add_trace(fig, df['Date'],
                                  df['pct_change_m_money_net_positions'],
                                  f'% Change Net Positions Managed Money ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'], chart_type='bar')
                        add_trace(fig, df['Date'],
                                  df['pct_change_prod_merc_net_positions'],
                                  f'% Change Net Positions Producers / Merchants ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_long'], chart_type='bar')
                        add_trace(fig, df['Date'],
                                  df['pct_change_swap_net_positions'],
                                  f'% Change Net Positions Swap Dealers ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['other_long'], chart_type='bar')
                        update_yaxis(fig, row=row_index, col=1, title='% Change in Net Positions')

                    elif report_type == 'tff':
                        add_trace(fig, df['Date'],
                                  df['pct_change_lev_money_net_positions'],
                                  f'% Change Net Positions Managed Money ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'], chart_type='bar')
                        add_trace(fig, df['Date'],
                                  df['pct_change_asset_mgr_net_positions'],
                                  f'% Change Net Positions Producers / Merchants ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_long'], chart_type='bar')
                        add_trace(fig, df['Date'],
                                  df['pct_change_dealer_net_positions'],
                                  f'% Change Net Positions Swap Dealers ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['other_long'], chart_type='bar')
                        update_yaxis(fig, row=row_index, col=1, title='% Change in Net Positions')

            elif subplot == '26W Index':
                df = Index26WDataFetcher.fetch_26w_index_data(stored_market, current_year, table_suffix, report_type)
                if not df.empty:
                    df = df.apply(pd.to_numeric, errors='coerce')
                    df['Date'] = pd.to_datetime(df['Date'])

                    if report_type == 'legacy':
                        add_trace(fig, df['Date'], df['noncomm_26w_index'],
                                  f'Non-Commercials 26W Index ({table_suffix})', row=row_index, col=1, line_color=COLORS['noncomm_long'])
                        add_trace(fig, df['Date'], df['comm_26w_index'],
                                  f'Commercials 26W Index ({table_suffix})', row=row_index, col=1, line_color=COLORS['comm_long'])
                        add_shape(fig, df['Date'].min(), df['Date'].max(), 50, 50, row=row_index, col=1)
                        update_yaxis(fig, row=row_index, col=1, title='26-Week Index')

                    elif report_type == 'disaggregated':
                        add_trace(fig, df['Date'], df['m_money_26w_index'],
                                  f'Managed Money 26W Index ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'])
                        add_trace(fig, df['Date'], df['prod_merc_26w_index'],
                                  f'Producers / Merchants 26W Index ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_long'])
                        add_trace(fig, df['Date'], df['swap_26w_index'],
                                  f'Swap Dealers 26W Index ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['other_long'])
                        add_shape(fig, df['Date'].min(), df['Date'].max(), 50, 50, row=row_index, col=1)
                        update_yaxis(fig, row=row_index, col=1, title='26-Week Index')

                    elif report_type == 'tff':
                        add_trace(fig, df['Date'], df['lev_money_26w_index'],
                                  f'Managed Money 26W Index ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'])
                        add_trace(fig, df['Date'], df['asset_mgr_26w_index'],
                                  f'Producers / Merchants 26W Index ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_long'])
                        add_trace(fig, df['Date'], df['dealer_26w_index'],
                                  f'Swap Dealers 26W Index ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['other_long'])
                        add_shape(fig, df['Date'].min(), df['Date'].max(), 50, 50, row=row_index, col=1)
                        update_yaxis(fig, row=row_index, col=1, title='26-Week Index')

            row_index += 1

        # Hide the range slider for x-axis
        fig.update_xaxes(rangeslider=dict(visible=False), type='date', row=1, col=1)

        fig.update_layout(
            height=total_height,
            title=f'{stored_market} - Year {current_year}',
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.15,
                xanchor="center",
                x=0.5
            ),
            plot_bgcolor="#1e1e1e",
            paper_bgcolor='#1e1e1e',
            font=dict(
                family="'Press Start 2P', monospace",
                size=10,
                color='white'
            ),
            hoversubplots="axis",
            hovermode="x",
            dragmode="pan"
        )


        """""
        fig.update_layout(
            height=total_height,
            title=f'{stored_market} - Year {current_year}',
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.15,
                xanchor="center",
                x=0.5
            ),
            plot_bgcolor="#1e1e1e",
            paper_bgcolor='#1e1e1e',
            font=dict(
                family="'Press Start 2P', monospace",  # Set the font for the graph
                size=10,  # Adjust size as needed
                color='white'),
            hoversubplots="axis",
            hovermode="x",
            dragmode="pan",
            yaxis=dict(
                showgrid=False,  # Hide x-axis grid lines
                zeroline=False,),
            yaxis2=dict(
                showgrid=False,  # Hide x-axis grid lines
                zeroline=False, )  # Hide x-axis zero line if it exists
            # Hide x-axis zero line if it exists
        )
        """""

        # Dynamically update axes settings for each subplot
        for i in range(1, num_rows + 1):  # Assuming num_rows is the total number of rows in your subplot
            fig.update_xaxes(
                showgrid=False,  # Hide x-axis grid lines
                zeroline=False,  # Hide x-axis zero line
                #showline=False,  # Hide x-axis line
                #mirror=False,  # Avoid axis line mirroring
                row=i, col=1
            )
            fig.update_yaxes(
                showgrid=False,  # Hide y-axis grid lines
                zeroline=False,  # Hide y-axis zero line
                #showline=False,  # Hide y-axis line
                #mirror=False,  # Avoid axis line mirroring
                row=i, col=1
            )

        fig.update_traces(hoverinfo="x+y") # If added xaxis="x1" it gives nice vertical line accross all subplots but not working for Week 26 Index

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

    """""
    @app.callback(
        Output('stored-market', 'data'),
        [Input('market-dropdown', 'value')]
    )
    def update_stored_market(selected_market):
        return next((name for name, ticker in market_tickers.items() if ticker == selected_market), DEFAULT_MARKET)
    """""
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

    # Function to get the market name based on its index
    # Function to get the market name based on its index
    def get_market_by_index(index, market_tickers):
        """
        Retrieve the market name by its index in the sorted list.

        Args:
            index (int): The index of the market.
            market_tickers (dict): The dictionary of market tickers.

        Returns:
            str: The market name corresponding to the given index.
        """
        markets = sorted(market_tickers.keys())
        if 0 <= index < len(markets):
            return markets[index]
        return DEFAULT_MARKET  # Default market if index is out of bounds

    # Combined callback for market updates
    @app.callback(
        [Output('stored-market', 'data'),
         Output('market-dropdown', 'value')],  # Add this Output to update the dropdown's value
        [Input('market-dropdown', 'value'),
         Input('prev-market-button', 'n_clicks'),
         Input('next-market-button', 'n_clicks')],
        [State('stored-market', 'data')]
    )
    def update_stored_market(selected_market, n_clicks_prev, n_clicks_next, current_market):
        # Determine which input triggered the callback
        triggered_input = ctx.triggered[0]['prop_id'].split('.')[0]

        # Handle dropdown selection
        if 'market-dropdown' in triggered_input:
            new_market = next((name for name, ticker in market_tickers.items() if ticker == selected_market),
                              DEFAULT_MARKET)
            return new_market, selected_market  # Return both the updated stored-market and the dropdown value

        # Handle Previous and Next Market button clicks
        elif 'prev-market-button' in triggered_input or 'next-market-button' in triggered_input:
            markets = sorted(market_tickers.keys())
            current_index = markets.index(current_market) if current_market in markets else 0

            if 'prev-market-button' in triggered_input:
                # Move to the previous market
                new_index = (current_index - 1) % len(markets)
            elif 'next-market-button' in triggered_input:
                # Move to the next market
                new_index = (current_index + 1) % len(markets)
            else:
                return current_market, current_market  # Return current market if no button is clicked

            # Get the new market based on the calculated index
            new_market = get_market_by_index(new_index, market_tickers)
            ticker = market_tickers[new_market]  # Get the corresponding ticker for the dropdown

            return new_market, ticker  # Update both the stored-market and dropdown value

        # Default return if nothing is triggered
        return current_market, selected_market
