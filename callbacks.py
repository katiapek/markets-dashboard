# callbacks.py

from dash import Input, Output, State, ctx, callback_context
import plotly.subplots as sp
from layout_definitions import format_market_name
from data_fetchers import (
    CorrelationDataFetcher,
    fetch_ohlc_data_cached,
    fetch_active_subplot_data,
    fetch_seasonal_data_cached
)
from dotenv import load_dotenv
import os
from callback_helpers import *
from scripts.config import COLORS, market_tickers, TRACE_CONFIG


# Load environment variables from .env file
load_dotenv()
user_tier = os.getenv("USER_TIER", "free")

# Create a dictionary to map market names to the first part of their ticker
# Special handling for cases like 'DX-Y.NYB' and '^VIX'
ticker_prefixes = {}
for name, ticker in market_tickers.items():
    if ticker == 'DX-Y.NYB':
        ticker_prefixes[name] = 'DXY'
    elif ticker == '^VIX':
        ticker_prefixes[name] = 'VIX'
    else:
        ticker_prefixes[name] = ticker.split('=')[0]


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
         Input('current-year', 'data'),
         Input('combined-chart', 'relayoutData'),
         ],
        prevent_initial_call=False
    )
    def update_graph(active_subplots, selected_years, ohlc_visibility, stored_market, current_year, relayout_data):
        num_rows = 1 + len(active_subplots)
        specs = [[{'secondary_y': True}]] + [[{'secondary_y': False}] for _ in range(len(active_subplots))]

        # Calculate row heights dynamically
        initial_height = 800  # initial total height when only the OHLC/Seasonality chart is shown
        total_height = initial_height

        # Allocate more height to the first row initially
        row_heights = [0.6] + [0.4 / len(active_subplots) for _ in range(len(active_subplots))]

        fig = sp.make_subplots(rows=num_rows, cols=1, shared_xaxes=True, vertical_spacing=0.0, specs=specs,
                               row_heights=row_heights)

        start_date_str = f"{current_year}-01-01"
        end_date_str = f"{current_year}-12-31"
        ohlc_df = fetch_ohlc_data_cached(stored_market, start_date_str, end_date_str)

        if ohlc_df.empty:
            fig.update_layout(
                plot_bgcolor="#1e1e1e",
                paper_bgcolor="#1e1e1e",
                xaxis=dict(visible=False),  # Hide x-axis
                yaxis=dict(visible=False),  # Hide y-axis
                font=dict(
                    family="'Press Start 2P', monospace",
                    size=10,
                    color='white'),
            )
            fig.add_annotation(
                text=f"No data available for {stored_market} year {current_year}.",
                x=0.5,  # Center horizontally
                y=0.5,  # Center vertically
                xref="paper",  # Use paper coordinates (relative to the canvas)
                yref="paper",  # Use paper coordinates (relative to the canvas)
                showarrow=False,  # No arrow for the annotation
                font=dict(size=20, color="white"),  # Customize font size and color
                align="center"  # Center the text alignment
            )
            return fig

        # Initial Range Configuration
        initial_x_range = [ohlc_df['date'].iloc[0], ohlc_df['date'].iloc[-1]]
        initial_y_range = [ohlc_df["low"].min(), ohlc_df["high"].max()]

        # Determine if reset is needed (via year change)
        ctx_graph_reset = callback_context
        triggered_prop = ctx_graph_reset.triggered[0]['prop_id'] if ctx_graph_reset.triggered else None
        reset_required = triggered_prop in ['current-year.data']

        # Default Ranges
        x_range = initial_x_range
        y_range = initial_y_range

        # Check for User Interactions and Adjust Ranges
        if relayout_data and not reset_required:
            if "xaxis.range[0]" in relayout_data and "xaxis.range[1]" in relayout_data:
                # Convert relayoutData x-range to Timestamps
                x_range_start = pd.Timestamp(relayout_data["xaxis.range[0]"])
                x_range_end = pd.Timestamp(relayout_data["xaxis.range[1]"])

                # Clamp the range to prevent excessive zooming out or in
                x_range = [
                    max(initial_x_range[0], x_range_start),
                    min(initial_x_range[1], x_range_end)
                ]

            if "yaxis.autorange" in relayout_data or "xaxis.range[0]" in relayout_data:
                # Dynamically adjust Y-axis to fit the data within the selected X-axis range
                filtered_data = ohlc_df[(ohlc_df['date'] >= x_range[0]) & (ohlc_df['date'] <= x_range[1])]
                y_range = [
                    max(initial_y_range[0], filtered_data["low"].min()),
                    min(initial_y_range[1], filtered_data["high"].max())
                ]

        # Add OHLC chart
        if 'OHLC' in ohlc_visibility:
            if not ohlc_df.empty:
                add_candlestick_trace(
                    fig,
                    ohlc_df['date'],
                    ohlc_df['open'],
                    ohlc_df['high'],
                    ohlc_df['low'],
                    ohlc_df['close'],
                    f'OHLC {current_year}',
                    row=1,
                    col=1,
                    secondary_y=False
                )

                # Build a complete timeline and identify missing dates for OHLC chart
                dt_all = pd.date_range(start=ohlc_df['date'].min(), end=ohlc_df['date'].max())
                dt_obs = ohlc_df['date'].dt.strftime("%Y-%m-%d").tolist()
                dt_breaks = [d for d in dt_all.strftime("%Y-%m-%d").tolist() if d not in dt_obs]

                # Apply rangebreaks only for the OHLC chart
                fig.update_xaxes(rangebreaks=[dict(values=dt_breaks)], row=1, col=1)

        if user_tier == 'premium':
            # Add Seasonality chart
            for years in selected_years:
                df = fetch_seasonal_data_cached(format_market_name(stored_market), years, current_year)
                if not df.empty:
                    add_trace(
                        fig,
                        df['date'],
                        df['indexed_cumulative_percent_change'],
                        f'{years} Years',
                        row=1,
                        col=1,
                        opacity=0.8,
                        line_color=COLORS['seasonality_colors'][years],  # Use corresponding color
                        secondary_y=True,
                        hide_yaxis_ticks=True,
                        show_legend=False,
                        disable_hover=False
                    )

        row_index = 2
        for subplot, table_suffix, report_type in active_subplots:
            df = fetch_active_subplot_data(stored_market, current_year, subplot, table_suffix, report_type)
            df = df.apply(pd.to_numeric, errors='coerce')

            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])

                filtered_data = df[(df['date'] >= x_range[0]) & (df['date'] <= x_range[1])]

                config = TRACE_CONFIG.get(subplot, {}).get(report_type, None)

                if config:
                    for column, participant_name, color in zip(config['columns'], config['names'], config['colors']):
                        add_trace(
                            fig,
                            filtered_data['date'],
                            filtered_data[column],
                            f"{participant_name}",
                            row=row_index,
                            col=1,
                            line_color=COLORS[color]
                        )
                    filtered_y_range = [filtered_data.iloc[:, 1:].min(), filtered_data.iloc[:, 1:].max()]
                    fig.update_yaxes(range=filtered_y_range, row=row_index, col=1, fixedrange=True)

            if subplot == 'Positions Change':
                filtered_data = df[(df['date'] >= x_range[0]) & (df['date'] <= x_range[1])]

                if report_type == 'legacy':

                    set_bar_width = 70000000
                    add_trace(fig, filtered_data['date'], filtered_data['pct_change_noncomm_long'],
                              f'% Change Non-Commercials Long', row=row_index, col=1,
                              line_color=COLORS['noncomm_long'], chart_type='bar', bar_width=set_bar_width,
                              bar_offset=0)
                    add_trace(fig, filtered_data['date'], filtered_data['pct_change_noncomm_short'],
                              f'% Change Non-Commercials Short', row=row_index, col=1,
                              line_color=COLORS['noncomm_short'], chart_type='bar', bar_width=set_bar_width,
                              bar_offset=1 * set_bar_width)
                    add_trace(fig, filtered_data['date'], filtered_data['pct_change_comm_long'],
                              f'% Change Commercials Long', row=row_index, col=1,
                              line_color=COLORS['comm_long'], chart_type='bar', bar_width=set_bar_width,
                              bar_offset=2 * set_bar_width)
                    add_trace(fig, filtered_data['date'], filtered_data['pct_change_comm_short'],
                              f'% Change Commercials Short', row=row_index, col=1,
                              line_color=COLORS['comm_short'], chart_type='bar', bar_width=set_bar_width,
                              bar_offset=3 * set_bar_width)
                    # fig.update_yaxes(fixedrange=True)

                elif report_type == 'disaggregated':
                    set_bar_width = 60000000
                    add_trace(fig, filtered_data['date'], filtered_data['pct_change_m_money_long'],
                              f'% Change Managed Money Long', row=row_index, col=1,
                              line_color=COLORS['noncomm_long'], chart_type='bar', bar_width=set_bar_width,
                              bar_offset=0)
                    add_trace(fig, filtered_data['date'], filtered_data['pct_change_m_money_short'],
                              f'% Change Managed Money Short', row=row_index, col=1,
                              line_color=COLORS['noncomm_short'], chart_type='bar', bar_width=set_bar_width,
                              bar_offset=1 * set_bar_width)
                    add_trace(fig, filtered_data['date'], filtered_data['pct_change_prod_merc_long'],
                              f'% Change Producers / Merchants Long', row=row_index, col=1,
                              line_color=COLORS['comm_long'], chart_type='bar', bar_width=set_bar_width,
                              bar_offset=2 * set_bar_width)
                    add_trace(fig, filtered_data['date'], filtered_data['pct_change_prod_merc_short'],
                              f'% Change Producers / Merchants Short', row=row_index, col=1,
                              line_color=COLORS['comm_short'], chart_type='bar', bar_width=set_bar_width,
                              bar_offset=3 * set_bar_width)
                    add_trace(fig, filtered_data['date'], filtered_data['pct_change_swap_long'],
                              f'% Change Swap Dealers Long', row=row_index, col=1,
                              line_color=COLORS['other_long'], chart_type='bar', bar_width=set_bar_width,
                              bar_offset=4 * set_bar_width)
                    add_trace(fig, filtered_data['date'], filtered_data['pct_change_swap_short'],
                              f'% Change Swap Dealers Short', row=row_index, col=1,
                              line_color=COLORS['other_short'], chart_type='bar', bar_width=set_bar_width,
                              bar_offset=5 * set_bar_width)
                    # fig.update_yaxes(fixedrange=True)

                elif report_type == 'tff':
                    set_bar_width = 60000000
                    add_trace(fig, filtered_data['date'], filtered_data['pct_change_lev_money_long'],
                              f'% Change Managed Money Long', row=row_index, col=1,
                              line_color=COLORS['noncomm_long'], chart_type='bar', bar_width=set_bar_width,
                              bar_offset=0)
                    add_trace(fig, filtered_data['date'], filtered_data['pct_change_lev_money_short'],
                              f'% Change Managed Money Short', row=row_index, col=1,
                              line_color=COLORS['noncomm_short'], chart_type='bar', bar_width=set_bar_width,
                              bar_offset=1 * set_bar_width)
                    add_trace(fig, filtered_data['date'], filtered_data['pct_change_asset_mgr_long'],
                              f'% Change Asset Mgrs Long', row=row_index, col=1,
                              line_color=COLORS['comm_long'], chart_type='bar', bar_width=set_bar_width,
                              bar_offset=2 * set_bar_width)
                    add_trace(fig, filtered_data['date'], filtered_data['pct_change_asset_mgr_short'],
                              f'% Change Asset Mgrs Short', row=row_index, col=1,
                              line_color=COLORS['comm_short'], chart_type='bar', bar_width=set_bar_width,
                              bar_offset=3 * set_bar_width)
                    add_trace(fig, filtered_data['date'], filtered_data['pct_change_dealer_long'],
                              f'% Change Swap Dealers Long', row=row_index, col=1,
                              line_color=COLORS['other_long'], chart_type='bar', bar_width=set_bar_width,
                              bar_offset=4 * set_bar_width)
                    add_trace(fig, filtered_data['date'], filtered_data['pct_change_dealer_short'],
                              f'% Change Swap Dealers Short', row=row_index, col=1,
                              line_color=COLORS['other_short'], chart_type='bar', bar_width=set_bar_width,
                              bar_offset=5 * set_bar_width)
                    # fig.update_yaxes(fixedrange=True)

            elif subplot == 'Net Positions Change':

                filtered_data = df[(df['date'] >= x_range[0]) & (df['date'] <= x_range[1])]

                if report_type == 'legacy':
                    set_bar_width = 70000000
                    add_trace(fig, filtered_data['date'],
                              filtered_data['pct_change_noncomm_net_positions'],
                              f'% Change Net Positions Non-Commercials', row=row_index, col=1,
                              line_color=COLORS['noncomm_long'], chart_type='bar', bar_width=set_bar_width,
                              bar_offset=0 * set_bar_width)
                    add_trace(fig, filtered_data['date'],
                              filtered_data['pct_change_comm_net_positions'],
                              f'% Change Net Positions Commercials', row=row_index, col=1,
                              line_color=COLORS['comm_long'], chart_type='bar', bar_width=set_bar_width,
                              bar_offset=1 * set_bar_width)
                    # fig.update_yaxes(fixedrange=True)

                elif report_type == 'disaggregated':
                    set_bar_width = 60000000
                    add_trace(fig, filtered_data['date'],
                              filtered_data['pct_change_m_money_net_positions'],
                              f'% Change Net Positions Managed Money', row=row_index, col=1,
                              line_color=COLORS['noncomm_long'], chart_type='bar', bar_width=set_bar_width,
                              bar_offset=0 * set_bar_width)
                    add_trace(fig, filtered_data['date'],
                              filtered_data['pct_change_prod_merc_net_positions'],
                              f'% Change Net Positions Producers / Merchants', row=row_index, col=1,
                              line_color=COLORS['comm_long'], chart_type='bar', bar_width=set_bar_width,
                              bar_offset=1 * set_bar_width)
                    add_trace(fig, filtered_data['date'],
                              filtered_data['pct_change_swap_net_positions'],
                              f'% Change Net Positions Swap Dealers', row=row_index, col=1,
                              line_color=COLORS['other_long'], chart_type='bar', bar_width=set_bar_width,
                              bar_offset=2 * set_bar_width)
                    # fig.update_yaxes(fixedrange=True)

                elif report_type == 'tff':
                    set_bar_width = 60000000

                    add_trace(fig, filtered_data['date'],
                              filtered_data['pct_change_lev_money_net_positions'],
                              f'% Change Net Positions Managed Money', row=row_index, col=1,
                              line_color=COLORS['noncomm_long'], chart_type='bar', bar_width=set_bar_width,
                              bar_offset=0 * set_bar_width)
                    add_trace(fig, filtered_data['date'],
                              filtered_data['pct_change_asset_mgr_net_positions'],
                              f'% Change Net Positions Asset Mgrs', row=row_index, col=1,
                              line_color=COLORS['comm_long'], chart_type='bar', bar_width=set_bar_width,
                              bar_offset=1 * set_bar_width)
                    add_trace(fig, filtered_data['date'],
                              filtered_data['pct_change_dealer_net_positions'],
                              f'% Change Net Positions Dealers', row=row_index, col=1,
                              line_color=COLORS['other_long'], chart_type='bar', bar_width=set_bar_width,
                              bar_offset=2 * set_bar_width)
                    # fig.update_yaxes(fixedrange=True)

            row_index += 1

        # Hide the range slider for x-axis
        fig.update_xaxes(rangeslider=dict(visible=False), type='date', row=1, col=1)

        fig.update_layout(
            uirevision=stored_market,
            xaxis=dict(range=x_range),
            yaxis=dict(range=y_range, fixedrange=True, autorange=False),
            height=total_height,
            title=f'{stored_market} - Year {current_year}',
            legend=dict(
                orientation="v",
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                # itemwidth = 100,
            ),
            legend_bgcolor="rgba(0,0,0,0) ",
            plot_bgcolor="#1e1e1e",
            paper_bgcolor='#1e1e1e',
            font=dict(
                family="'Press Start 2P', monospace",
                size=10,
                color='white'
            ),
            hoversubplots="axis",
            hovermode="x unified",
            dragmode="pan"
        )

        # Dynamically update axes settings for each subplot
        for i in range(1, num_rows + 1):  # Assuming num_rows is the total number of rows in your subplot
            fig.update_xaxes(
                showgrid=False,  # Hide x-axis grid lines
                zeroline=False,  # Hide x-axis zero line
                # showline=False,  # Hide x-axis line
                # mirror=False,  # Avoid axis line mirroring
                range=x_range, row=i, col=1
            )
            fig.update_yaxes(
                showgrid=False,  # Hide y-axis grid lines
                zeroline=False,  # Hide y-axis zero line
                # showline=False,  # Hide y-axis line
                # mirror=False,  # Avoid axis line mirroring
                row=i, col=1,
                fixedrange=True,
            )

        fig.update_traces(hoverinfo="x+y",
                          xaxis="x1",
                          )
        # If added xaxis="x1" it gives nice vertical line across all subplots but not working for Week 26 Index

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
            new_market = next((m_name for m_name, m_ticker in market_tickers.items() if m_ticker == selected_market),
                              DEFAULT_MARKET)
            return new_market, selected_market  # Return both the updated stored-market and the dropdown value

        # Handle Previous and Next Market button clicks
        elif 'prev-market-button' in triggered_input or 'next-market-button' in triggered_input:
            markets = list(market_tickers.keys())  # Keep the original order from config.py
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
            m_ticker = market_tickers[new_market]  # Get the corresponding ticker for the dropdown

            return new_market, m_ticker  # Update both the stored-market and dropdown value

        # Default return if nothing is triggered
        return current_market, selected_market

    # Callback for Opportunity Analysis section

    if user_tier == 'premium':
        @app.callback(
            [
                Output('yearly-analysis-table', 'data'),
                Output('15-year-summary', 'children'),
                Output('30-year-summary', 'children'),
                Output('distribution-chart-15', 'figure'),
                Output('distribution-chart-optimal-15', 'figure'),
                Output('distribution-chart-30', 'figure'),
                Output('distribution-chart-optimal-30', 'figure'),
                Output('cumulative-return-chart-15', 'figure'),
                Output('cumulative-return-chart-30', 'figure'),
                Output('risk-metrics-summary-15', 'children'),
                Output('risk-metrics-summary-30', 'children'),
                Output('risk-metrics-summary-15-stoploss', 'children'),
                Output('risk-metrics-summary-30-stoploss', 'children'),
                Output('day-trading-stats-table', 'data'),
                Output('day-trading-stats-1-table', 'data'),
                Output('day-trading-stats-weekday-table', 'data'),
                Output('day-trading-stats-1-weekday-table', 'data'),
                Output('dup-open-high-dist', 'figure'),
                Output('dup-open-low-dist', 'figure'),
                Output('dup-open-close-dist', 'figure'),
                Output('dup-open-low-vs-high-scatter', 'figure'),
                Output('dup-open-low-vs-close-scatter', 'figure'),
                Output('dup-low-vs-prev-low-dist', 'figure'),
                Output('dup-high-vs-prev-high-dist', 'figure'),
                Output('ddown-open-high-dist', 'figure'),
                Output('ddown-open-low-dist', 'figure'),
                Output('ddown-open-close-dist', 'figure'),
                Output('ddown-open-low-vs-high-scatter', 'figure'),
                Output('ddown-open-low-vs-close-scatter', 'figure'),
                Output('ddown-low-vs-prev-low-dist', 'figure'),
                Output('ddown-high-vs-prev-high-dist', 'figure'),
                Output('pdh-open-high-dist', 'figure'),
                Output('pdh-open-low-dist', 'figure'),
                Output('pdh-open-close-dist', 'figure'),
                Output('pdh-open-low-vs-high-scatter', 'figure'),
                Output('pdh-open-low-vs-close-scatter', 'figure'),
                Output('pdh-high-vs-prev-high-dist', 'figure'),
                Output('pdl-open-high-dist', 'figure'),
                Output('pdl-open-low-dist', 'figure'),
                Output('pdl-open-close-dist', 'figure'),
                Output('pdl-open-low-vs-high-scatter', 'figure'),
                Output('pdl-open-low-vs-close-scatter', 'figure'),
                Output('pdl-low-vs-prev-low-dist', 'figure'),
                Output('pdhl-open-high-dist', 'figure'),
                Output('pdhl-open-low-dist', 'figure'),
                Output('pdhl-open-close-dist', 'figure'),
                Output('pdhl-open-low-vs-high-scatter', 'figure'),
                Output('pdhl-open-low-vs-close-scatter', 'figure'),
                Output('pdhl-low-vs-prev-low-dist', 'figure'),
                Output('pdhl-high-vs-prev-high-dist', 'figure'),
                Output('pdh-pdl-pdhl-open-high-dist', 'figure'),
                Output('pdh-pdl-pdhl-open-low-dist', 'figure'),
                Output('pdh-pdl-pdhl-open-close-dist', 'figure'),
                Output('pdh-pdl-pdhl-open-low-vs-high-scatter', 'figure'),
                Output('pdh-pdl-pdhl-open-low-vs-close-scatter', 'figure'),
                Output('pdh-pdl-pdhl-low-vs-prev-low-dist', 'figure'),
                Output('pdh-pdl-pdhl-high-vs-prev-high-dist', 'figure')
            ],
            [Input('perform-analysis-button', 'n_clicks'),
             Input('interval-auto-load', 'n_intervals')],
            [State('date-picker-range', 'start_date'),
             State('date-picker-range', 'end_date'),
             State('direction-dropdown', 'value'),
             State('years-checklist', 'value'),
             State('stored-market', 'data')],
            prevent_initial_call=True
        )
        def perform_analysis_and_update_layout(n_clicks, n_intervals, start_date, end_date, direction, years_range,
                                               stored_market):
            start_month, start_day = pd.to_datetime(start_date).month, pd.to_datetime(start_date).day
            end_month, end_day = pd.to_datetime(end_date).month, pd.to_datetime(end_date).day

            ohlc_data_all_years = pd.DataFrame()
            current_year = 2024

            for year_offset in years_range:
                year = current_year - year_offset
                start_date_str = f'{year}-{start_month:02d}-{start_day:02d}'
                end_date_str = f'{current_year}-{end_month:02d}-{end_day:02d}'
                ohlc_data_year = fetch_ohlc_data_cached(stored_market, start_date_str, end_date_str)

                if not ohlc_data_year.empty:
                    ohlc_data_all_years = pd.concat([ohlc_data_all_years, ohlc_data_year], ignore_index=True)

            if ohlc_data_all_years.empty:
                return [], "No data available for 15-Year Summary", "No data available for 30-Year Summary", {}, {}

            # Perform analysis on the fetched OHLC data (Unoptimized results)
            analysis_results = perform_analysis(start_date, end_date, direction, ohlc_data_all_years)

            # Prepare data for the yearly analysis table (Unoptimized)
            yearly_data = analysis_results['yearly_results']

            # Prepare summaries for 15 years and 30 years - No-Stop loss returns per year for Summary table
            summary_15 = analysis_results['15_year_summary']
            summary_30 = analysis_results['30_year_summary']

            # Calculate optimal stop-loss and exit for 15 and 30 years
            optimal_results_15y = analysis_results['optimal_results_15y']
            optimal_results_30y = analysis_results['optimal_results_30y']

            # Simulate trades with optimal S/L and exit for 15 and 30 years
            optimal_trades_results_15y = analysis_results['optimal_trades_results_15y']
            optimal_trades_results_30y = analysis_results['optimal_trades_results_30y']

            # D-UP stats
            dup_distributions = analysis_results['dup_distributions']
            dup_scatters = analysis_results['dup_scatters']
            dup_high_vs_prev_high_dist = analysis_results['dup_high_vs_prev_high_dist']
            dup_low_vs_prev_low_dist = analysis_results['dup_low_vs_prev_low_dist']

            # D-DOWN stats
            ddown_distributions = analysis_results['ddown_distributions']
            ddown_scatters = analysis_results['ddown_scatters']
            ddown_high_vs_prev_high_dist = analysis_results['ddown_high_vs_prev_high_dist']
            ddown_low_vs_prev_low_dist = analysis_results['ddown_low_vs_prev_low_dist']

            # PD-H stats
            pdh_distributions = analysis_results['pdh_distributions']
            pdh_scatters = analysis_results['pdh_scatters']
            pdh_high_vs_prev_high_dist = analysis_results['pdh_high_vs_prev_high_dist']

            # PD-L stats
            pdl_distributions = analysis_results['pdl_distributions']
            pdl_scatters = analysis_results['pdl_scatters']
            pdl_low_vs_prev_low_dist = analysis_results['pdl_low_vs_prev_low_dist']

            # PD-HL stats
            pdhl_distributions = analysis_results['pdhl_distributions']
            pdhl_scatters = analysis_results['pdhl_scatters']
            pdhl_low_vs_prev_low_dist = analysis_results['pdhl_low_vs_prev_low_dist']
            pdhl_high_vs_prev_high_dist = analysis_results['pdhl_high_vs_prev_high_dist']

            # PD-H, PD-L and PD-HL stats
            pdh_pdl_pdhl_distributions = analysis_results['pdh_pdl_pdhl_distributions']
            pdh_pdl_pdhl_scatters = analysis_results['pdh_pdl_pdhl_scatters']
            pdh_pdl_pdhl_low_vs_prev_low_dist = analysis_results['pdh_pdl_pdhl_low_vs_prev_low_dist']
            pdh_pdl_pdhl_high_vs_prev_high_dist = analysis_results['pdh_pdl_pdhl_high_vs_prev_high_dist']

            # Distribution Charts for 15 and 30 years
            distribution_chart_15 = create_distribution_chart(yearly_data[:15], "15-Year Returns")
            optimal_distribution_chart_15 = create_distribution_chart(optimal_trades_results_15y,
                                                                      "15-Year Stop-Loss and Exit Returns")
            distribution_chart_30 = create_distribution_chart(yearly_data[:30], "30-Year Returns ")
            optimal_distribution_chart_30 = create_distribution_chart(optimal_trades_results_30y,
                                                                      "30-Year Stop-Loss and Exit Returns")

            # Cumulative return charts for 15 and 30 years
            (fig_15y, fig_30y, daily_returns_15, daily_returns_30, daily_returns_15_stoploss, daily_returns_30_stoploss,
             cum_returns_no_stop_15, cum_returns_stop_15, cum_returns_no_stop_30, cum_returns_stop_30) = (
                create_cumulative_return_charts(start_month, start_day, end_month, end_day, direction,
                                                ohlc_data_all_years,
                                                optimal_results_15y, optimal_results_30y
                                                ))

            # Calculate risk metrics using cumulative returns
            risk_metrics_15 = calculate_risk_metrics(daily_returns_15, cum_returns_no_stop_15)
            risk_metrics_30 = calculate_risk_metrics(daily_returns_30, cum_returns_no_stop_30)

            # Calculate stop-loss risk metrics
            stop_loss_metrics_15 = calculate_risk_metrics(daily_returns_15_stoploss, cum_returns_stop_15)
            stop_loss_metrics_30 = calculate_risk_metrics(daily_returns_30_stoploss, cum_returns_stop_30)

            # Risk metrics and summaries for both scenarios (with and without stop-loss)
            no_stop_loss_color = 'CornFlowerBlue'
            stop_loss_color = 'Salmon'

            risk_metrics_summary_15 = update_risk_metrics_summary(risk_metrics_15, no_stop_loss_color)
            risk_metrics_summary_30 = update_risk_metrics_summary(risk_metrics_30, no_stop_loss_color)
            stop_loss_metrics_summary_15 = update_risk_metrics_summary(stop_loss_metrics_15, stop_loss_color)
            stop_loss_metrics_summary_30 = update_risk_metrics_summary(stop_loss_metrics_30, stop_loss_color)

            # Compute day trading stats by year
            stats_df = analysis_results['day_trading_stats']
            stats_1_df = analysis_results['day_trading_stats_1']
            stats_weekday_df = analysis_results['day_trading_stats_weekday']
            stats_1_weekday_df = analysis_results['day_trading_stats_1_weekday']

            # Separate the 'Total' row and the numeric years for sorting
            total_row = stats_df[stats_df['year'] == 'Total']
            stats_df = stats_df[stats_df['year'] != 'Total']

            total_1_row = stats_1_df[stats_1_df['year'] == 'Total']
            stats_1_df = stats_1_df[stats_1_df['year'] != 'Total']

            # Ensure the 'year' column is integer type for sorting
            stats_df = stats_df.copy()  # Explicitly create a copy to avoid SettingWithCopyWarning
            stats_df['year'] = stats_df['year'].astype(int)

            stats_1_df = stats_1_df.copy()  # Explicitly create a copy to avoid SettingWithCopyWarning
            stats_1_df['year'] = stats_1_df['year'].astype(int)

            # Convert the dictionary to a DataFrame if it's not already one
            stats_df = pd.DataFrame(stats_df)
            stats_1_df = pd.DataFrame(stats_1_df)

            # Drop duplicates and sort in one line with chaining
            stats_df = stats_df.drop_duplicates(subset=['year']).sort_values(by='year', ascending=False)
            stats_1_df = stats_1_df.drop_duplicates(subset=['year']).sort_values(by='year', ascending=False)

            # Add the 'Total' row back to the end of the DataFrame
            stats_df = pd.concat([stats_df, total_row], ignore_index=True)
            stats_1_df = pd.concat([stats_1_df, total_1_row], ignore_index=True)

            # Convert the DataFrame to a dictionary for Dash DataTable
            day_trading_stats = stats_df.to_dict('records')
            day_trading_stats_1 = stats_1_df.to_dict('records')
            day_trading_stats_weekday = stats_weekday_df.to_dict('records')
            day_trading_stats_1_weekday = stats_1_weekday_df.to_dict('records')

            summary_15_text = (
                f"15-Year Summary:\n"
                f"No stop-loss: Win Rate: "
                f"{summary_15['win_rate']:.2f}%, "
                f"Points Gained: {summary_15['total_points_gained']}, "
                f"% Gained: {summary_15['total_percent_gained']:.2f}% \n"
                f"Stop loss and exit: "
                f"Optimal S/L: {summary_15['optimal_stop_loss']:.2f}%, "
                f"Optimal Exit: {summary_15['optimal_exit']:.2f}%\n"
                f"Optimal Win Rate: {summary_15['optimal_win_rate']:.2f}%, "
                f"Optimal Points Gained: {summary_15['optimal_points_gained']}, "
                f"Optimal % Gained: {summary_15['optimal_percent_gained']:.2f}%"
            )

            summary_30_text = (
                f"30-Year Summary:\n"
                f"Win Rate: {summary_30['win_rate']:.2f}%, "
                f"Points Gained: {summary_30['total_points_gained']},"
                f" % Gained: {summary_30['total_percent_gained']:.2f}% \n"
                f"Stop loss and exit: "
                f"Optimal S/L: {summary_30['optimal_stop_loss']:.2f}%, "
                f"Optimal Exit: {summary_30['optimal_exit']:.2f}%\n"
                f"Optimal Win Rate: {summary_30['optimal_win_rate']:.2f}%, "
                f"Optimal Points Gained: {summary_30['optimal_points_gained']}, "
                f"Optimal % Gained: {summary_30['optimal_percent_gained']:.2f}%"
            )

            return (
                yearly_data,  # Unoptimized data for the yearly analysis table
                summary_15_text,
                summary_30_text,
                distribution_chart_15,  # Unoptimized distribution chart for 15 years
                optimal_distribution_chart_15,  # Optimized distribution chart for 15 years
                distribution_chart_30,  # Unoptimized distribution chart for 30 years
                optimal_distribution_chart_30,  # Optimized distribution chart for 30 years
                fig_15y,  # Cumulative return chart for 15 years
                fig_30y,  # Cumulative return chart for 30 years
                risk_metrics_summary_15,
                risk_metrics_summary_30,
                stop_loss_metrics_summary_15,
                stop_loss_metrics_summary_30,
                day_trading_stats,  # Day trading stats
                day_trading_stats_1,
                day_trading_stats_weekday,  # Day trading stats
                day_trading_stats_1_weekday,
                # D-UP distribution and scatter plots
                dup_distributions.get('open_high', {}),
                dup_distributions.get('open_low', {}),
                dup_distributions.get('open_close', {}),
                dup_scatters.get('scatter_1', {}),  # HERE SCATTERS
                dup_scatters.get('scatter_2', {}),
                dup_low_vs_prev_low_dist,
                dup_high_vs_prev_high_dist,
                # D-DOWN distribution and scatter plots
                ddown_distributions.get('open_high', {}),
                ddown_distributions.get('open_low', {}),
                ddown_distributions.get('open_close', {}),
                ddown_scatters.get('scatter_1', {}),  # HERE SCATTERS
                ddown_scatters.get('scatter_2', {}),
                ddown_low_vs_prev_low_dist,
                ddown_high_vs_prev_high_dist,
                # PD-H distribution and scatter plots
                pdh_distributions.get('open_high', {}),
                pdh_distributions.get('open_low', {}),
                pdh_distributions.get('open_close', {}),
                pdh_scatters.get('scatter_1', {}),  # HERE SCATTERS
                pdh_scatters.get('scatter_2', {}),
                pdh_high_vs_prev_high_dist,
                # PD-L distribution and scatter plots
                pdl_distributions.get('open_high', {}),
                pdl_distributions.get('open_low', {}),
                pdl_distributions.get('open_close', {}),
                pdl_scatters.get('scatter_1', {}),
                pdl_scatters.get('scatter_2', {}),
                pdl_low_vs_prev_low_dist,
                # PD-HL distribution and scatter plots
                pdhl_distributions.get('open_high', {}),
                pdhl_distributions.get('open_low', {}),
                pdhl_distributions.get('open_close', {}),
                pdhl_scatters.get('scatter_1', {}),
                pdhl_scatters.get('scatter_2', {}),
                pdhl_low_vs_prev_low_dist,
                pdhl_high_vs_prev_high_dist,
                # PD-H, PD-L, PD-HL distribution and scatter plots
                pdh_pdl_pdhl_distributions.get('open_high', {}),
                pdh_pdl_pdhl_distributions.get('open_low', {}),
                pdh_pdl_pdhl_distributions.get('open_close', {}),
                pdh_pdl_pdhl_scatters.get('scatter_1', {}),
                pdh_pdl_pdhl_scatters.get('scatter_2', {}),
                pdh_pdl_pdhl_low_vs_prev_low_dist,
                pdh_pdl_pdhl_high_vs_prev_high_dist,
            )

    @app.callback(
        [
            Output('correlation-180-days-table', 'data'),
            Output('correlation-180-days-table', 'columns'),
            Output('correlation-15-years-table', 'data'),
            Output('correlation-15-years-table', 'columns'),
        ],
        [Input('interval-auto-load', 'n_intervals')]
    )
    def update_correlation_tables(n_intervals):
        # Fetch the 180-day and 15-year correlation data
        correlation_180d = CorrelationDataFetcher.fetch_correlation_data("correlation_180_days")
        correlation_15y = CorrelationDataFetcher.fetch_correlation_data("correlation_15_years")

        def apply_ticker_prefix(df):
            if not df.empty:
                df['MKT'] = df['market_1'].map(ticker_prefixes)
                df['market_2'] = df['market_2'].map(ticker_prefixes)
                df = df.groupby(['MKT', 'market_2'], as_index=False).agg({'correlation': 'mean'})
                df = df.pivot(index='MKT', columns='market_2', values='correlation').round(2) * 100
                df = df.astype(int)
                df.reset_index(inplace=True)
                df.columns.name = None
            return df

        correlation_180d = apply_ticker_prefix(correlation_180d)
        correlation_15y = apply_ticker_prefix(correlation_15y)

        correlation_180d_data = correlation_180d.to_dict('records') if not correlation_180d.empty else []
        correlation_15y_data = correlation_15y.to_dict('records') if not correlation_15y.empty else []

        # Dynamically define columns
        correlation_180d_columns = [{'name': col, 'id': col} for col in correlation_180d.columns]
        correlation_15y_columns = [{'name': col, 'id': col} for col in correlation_15y.columns]

        return correlation_180d_data, correlation_180d_columns, correlation_15y_data, correlation_15y_columns
