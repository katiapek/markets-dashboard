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
        trace = go.Scatter(x=x, y=y, mode=mode, name=name, line=dict(color=line_color), showlegend=False, opacity=opacity)
    elif chart_type == 'bar':
        trace = go.Bar(x=x, y=y, name=name, marker=dict(color=line_color), showlegend=False, opacity=opacity)

    fig.add_trace(trace, row=row, col=col, secondary_y=secondary_y)


def add_candlestick_trace(fig, x, open, high, low, close, name, row, col, secondary_y=False):
    trace = go.Candlestick(x=x, open=open, high=high, low=low, close=close, name=name,
                           yaxis='y2', hoverinfo='text', showlegend=False, increasing_line_color="green", decreasing_line_color="black")
    fig.add_trace(trace, row=row, col=col, secondary_y=secondary_y)

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

        # Calculate row heights dynamically
        initial_height = 800  # initial total height when only the OHLC/Seasonality chart is shown
        # additional_height_per_subplot = 100  # additional height for each subplot
        total_height = initial_height # + additional_height_per_subplot * len(active_subplots)

        # Allocate more height to the first row initially
        row_heights = [0.6] + [0.4 / len(active_subplots) for _ in range(len(active_subplots))]

        fig = sp.make_subplots(rows=num_rows, cols=1, shared_xaxes=True, vertical_spacing=0.0, specs=specs, row_heights=row_heights)

        # Add Seasonality chart
        for years in selected_years:
            df = SeasonalDataFetcher.fetch_seasonal_data(format_market_name(stored_market), years)
            if not df.empty:
                df = df.apply(pd.to_numeric, errors='coerce')
                add_trace(fig, df['Day_of_Year'], df['Indexed_Cumulative_Percent_Change'], f'{years} Years', row=1,
                          col=1, opacity=0.6)

        # Add OHLC chart
        if 'OHLC' in ohlc_visibility:
            ohlc_df = OHLCDataFetcher.fetch_ohlc_data(stored_market, current_year)
            if not ohlc_df.empty:
                ohlc_df = ohlc_df.apply(pd.to_numeric, errors='coerce')
                add_candlestick_trace(fig, ohlc_df['Day_of_Year'], ohlc_df['Open'], ohlc_df['High'], ohlc_df['Low'],
                                      ohlc_df['Close'], f'OHLC {current_year}', row=1, col=1, secondary_y=True)
                # update_yaxis(fig, row=1, col=1, title='OHLC Prices', )

        row_index = 2
        for subplot, table_suffix, report_type in active_subplots:
            if subplot == 'Open Interest':
                df = OpenInterestDataFetcher.fetch_open_interest_data(stored_market, current_year, table_suffix,
                                                                      report_type)

                if not df.empty:
                    # print(f"Drawing from {table_suffix} table and {report_type} report")
                    df = df.apply(pd.to_numeric, errors='coerce')
                    add_trace(fig, df['Day_of_Year'], df['open_interest_all'], f'Open Interest ({table_suffix})',
                              row=row_index, col=1,
                              line_color=COLORS['open_interest'])
                    update_yaxis(fig, row=row_index, col=1, title='Open Interest')

            elif subplot == 'OI Percentages':
                df = OpenInterestPercentagesFetcher.fetch_open_interest_percentages(
                    stored_market, current_year, table_suffix, report_type
                )

                if not df.empty:
                    if report_type == 'legacy':
                        # Add traces for Legacy report
                        add_trace(fig, df['Day_of_Year'], df['pct_of_oi_noncomm_long_all'],
                                  f'% of OI Non-Commercials Long ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'])
                        add_trace(fig, df['Day_of_Year'], df['pct_of_oi_noncomm_short_all'],
                                  f'% of OI Non-Commercials Short ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_short'])
                        add_trace(fig, df['Day_of_Year'], df['pct_of_oi_comm_long_all'],
                                  f'% of OI Commercials Long ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_long'])
                        add_trace(fig, df['Day_of_Year'], df['pct_of_oi_comm_short_all'],
                                  f'% of OI Commercials Short ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_short'])
                        update_yaxis(fig, row=row_index, col=1, title='% of Open Interest')

                    elif report_type == 'disaggregated':
                        # Add traces for Disaggregated report
                        add_trace(fig, df['Day_of_Year'], df['pct_of_oi_m_money_long_all'],
                                  f'% of OI Managed Money Long ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'])
                        add_trace(fig, df['Day_of_Year'], df['pct_of_oi_m_money_short_all'],
                                  f'% of OI Managed Money Short ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_short'])
                        add_trace(fig, df['Day_of_Year'], df['pct_of_oi_prod_merc_long'],
                                  f'% of OI Producers/Merchants Long ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_long'])
                        add_trace(fig, df['Day_of_Year'], df['pct_of_oi_prod_merc_short'],
                                  f'% of OI Producers/Merchants Short ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_short'])
                        add_trace(fig, df['Day_of_Year'], df['pct_of_oi_swap_long_all'],
                                  f'% of OI Swap Dealers Long ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['other_long'])
                        add_trace(fig, df['Day_of_Year'], df['pct_of_oi_swap_short_all'],
                                  f'% of OI Swap Dealers Short ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['other_short'])
                        update_yaxis(fig, row=row_index, col=1, title='% of Open Interest')

            elif subplot == 'Positions Change':
                df = PositionsChangeDataFetcher.fetch_positions_change_data(stored_market, current_year, table_suffix,
                                                                            report_type)
                if not df.empty:
                    df = df.apply(pd.to_numeric, errors='coerce')

                    if report_type == 'legacy':

                        add_trace(fig, df['Day_of_Year'], df['pct_change_noncomm_long'],
                                  f'% Change Non-Commercials Long ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'], chart_type='bar')
                        add_trace(fig, df['Day_of_Year'], df['pct_change_noncomm_short'],
                                  f'% Change Non-Commercials Short ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_short'], chart_type='bar')
                        add_trace(fig, df['Day_of_Year'], df['pct_change_comm_long'],
                                  f'% Change Commercials Long ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_long'], chart_type='bar')
                        add_trace(fig, df['Day_of_Year'], df['pct_change_comm_short'],
                                  f'% Change Commercials Short ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_short'], chart_type='bar')
                        update_yaxis(fig, row=row_index, col=1, title='% Change in Positions')

                    elif report_type == 'disaggregated':
                        add_trace(fig, df['Day_of_Year'], df['pct_change_m_money_long'],
                                  f'% Change Managed Money Long ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'], chart_type='bar')
                        add_trace(fig, df['Day_of_Year'], df['pct_change_m_money_short'],
                                  f'% Change Managed Money Short ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_short'], chart_type='bar')
                        add_trace(fig, df['Day_of_Year'], df['pct_change_prod_merc_long'],
                                  f'% Change Producers / Merchants Long ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_long'], chart_type='bar')
                        add_trace(fig, df['Day_of_Year'], df['pct_change_prod_merc_short'],
                                  f'% Change Producers / Merchants Short ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_short'], chart_type='bar')
                        add_trace(fig, df['Day_of_Year'], df['pct_change_swap_long'],
                                  f'% Change Swap Dealers Long ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['other_long'], chart_type='bar')
                        add_trace(fig, df['Day_of_Year'], df['pct_change_swap_short'],
                                  f'% Change Swap Dealers Short ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['other_short'], chart_type='bar')
                        update_yaxis(fig, row=row_index, col=1, title='% Change in Positions')

            elif subplot == 'Net Positions':
                df = NetPositionsDataFetcher.fetch_net_positions_data(stored_market, current_year, table_suffix,
                                                                      report_type)
                if not df.empty:
                    df = df.apply(pd.to_numeric, errors='coerce')
                    if report_type == 'legacy':
                        add_trace(fig, df['Day_of_Year'], df['noncomm_net_positions'],
                                  f'Net Positions Non-Commercials ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'])
                        add_trace(fig, df['Day_of_Year'], df['comm_net_positions'],
                                  f'Net Positions Commercials ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_long'])
                        update_yaxis(fig, row=row_index, col=1, title='Net Positions')
                    elif report_type == 'disaggregated':
                        add_trace(fig, df['Day_of_Year'], df['m_money_net_positions'],
                                  f'Net Positions Managed Money ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'])
                        add_trace(fig, df['Day_of_Year'], df['prod_merc_net_positions'],
                                  f'Net Positions Producers / Merchants ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_long'])
                        add_trace(fig, df['Day_of_Year'], df['swap_net_positions'],
                                  f'Net Positions Swap Dealers ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['other_long'])
                        update_yaxis(fig, row=row_index, col=1, title='Net Positions')

            elif subplot == 'Net Positions Change':
                df = PositionsChangeNetDataFetcher.fetch_positions_change_net_data(stored_market, current_year,
                                                                                   table_suffix, report_type)
                if not df.empty:
                    df = df.apply(pd.to_numeric, errors='coerce')

                    if report_type == 'legacy':
                        add_trace(fig, df['Day_of_Year'],
                                  df['pct_change_noncomm_net_positions'],
                                  f'% Change Net Positions Non-Commercials ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'], chart_type='bar')
                        add_trace(fig, df['Day_of_Year'],
                                  df['pct_change_comm_net_positions'],
                                  f'% Change Net Positions Commercials ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_long'], chart_type='bar')
                        update_yaxis(fig, row=row_index, col=1, title='% Change in Net Positions')
                    elif report_type == 'disaggregated':
                        add_trace(fig, df['Day_of_Year'],
                                  df['pct_change_m_money_net_positions'],
                                  f'% Change Net Positions Managed Money ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'], chart_type='bar')
                        add_trace(fig, df['Day_of_Year'],
                                  df['pct_change_prod_merc_net_positions'],
                                  f'% Change Net Positions Producers / Merchants ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_long'], chart_type='bar')
                        add_trace(fig, df['Day_of_Year'],
                                  df['pct_change_swap_net_positions'],
                                  f'% Change Net Positions Swap Dealers ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['other_long'], chart_type='bar')
                        update_yaxis(fig, row=row_index, col=1, title='% Change in Net Positions')

            elif subplot == '26W Index':
                df = Index26WDataFetcher.fetch_26w_index_data(stored_market, current_year, table_suffix, report_type)
                if not df.empty:
                    df = df.apply(pd.to_numeric, errors='coerce')

                    if report_type == 'legacy':
                        add_trace(fig, df['Day_of_Year'], df['noncomm_26w_index'],
                                  f'Non-Commercials 26W Index ({table_suffix})', row=row_index, col=1, line_color=COLORS['noncomm_long'])
                        add_trace(fig, df['Day_of_Year'], df['comm_26w_index'],
                                  f'Commercials 26W Index ({table_suffix})', row=row_index, col=1, line_color=COLORS['comm_long'])
                        add_shape(fig, df['Day_of_Year'].min(), df['Day_of_Year'].max(), 50, 50, row=row_index, col=1)
                        update_yaxis(fig, row=row_index, col=1, title='26-Week Index')
                    elif report_type == 'disaggregated':
                        add_trace(fig, df['Day_of_Year'], df['m_money_26w_index'],
                                  f'Managed Money 26W Index ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'])
                        add_trace(fig, df['Day_of_Year'], df['prod_merc_26w_index'],
                                  f'Producers / Merchants 26W Index ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['comm_long'])
                        add_trace(fig, df['Day_of_Year'], df['swap_26w_index'],
                                  f'Swap Dealers 26W Index ({table_suffix})', row=row_index, col=1,
                                  line_color=COLORS['other_long'])
                        add_shape(fig, df['Day_of_Year'].min(), df['Day_of_Year'].max(), 50, 50, row=row_index, col=1)
                        update_yaxis(fig, row=row_index, col=1, title='26-Week Index')

            row_index += 1

        # Hide the range slider for x-axis
        fig.update_xaxes(rangeslider=dict(visible=False), row=1, col=1)

        fig.update_layout(
            height=total_height,
            title=f'{stored_market} Data Overview {current_year}',
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.15,
                xanchor="center",
                x=0.5
            ),
            plot_bgcolor="white",
            hoversubplots="axis",
            hovermode="x",
            dragmode="pan",
            #xaxis=dict(),  # type="category"
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
