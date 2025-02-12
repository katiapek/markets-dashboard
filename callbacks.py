# callbacks.py

from datetime import datetime
from dash import Input, Output, State, ctx, callback_context, MATCH, ALL
from queues import QueueManager, FetchingQueue, ProcessingQueue, AnalysisQueue, VisualizationQueue
from data_contracts import FetchingContract, ProcessingContract, AnalysisContract, VisualizationContract
from navigation_service import NavigationService
from state_managers import RangeManager, ViewportHandler, InteractionTracker
from data_processor import OHLCProcessor, DataProcessor
from plotly import graph_objects as go
from app.config import CANDLESTICK_CONFIG, SEASONALITY_CONFIG, POSITION_CHANGE_CONFIG, Config
import plotly.subplots as sp
from layout_definitions import format_market_name
from real_data_fetcher import RealDataFetcher, SubplotFetcher, SeasonalityFetcher, OHLCFetcher
from range_filter import RangeFilter
from data_fetchers import (
    fetch_ohlc_data_cached,
    fetch_active_subplot_data
)
from dotenv import load_dotenv
import os
from callback_helpers import *
from app.config import COLORS, market_tickers, TRACE_CONFIG
import re


# Load environment variables from .env file
load_dotenv()
user_tier = os.getenv("USER_TIER", "free")

# Initialize navigation service
navigation_service = NavigationService(market_tickers)

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


class PositionChangeVisuals:
    """Handles position change bar chart rendering with configurable options."""
    
    def __init__(self, position_data, config):
        """
        Args:
            position_data (pd.DataFrame): Position change data
            config (dict): Configuration for rendering (colors, styles, etc.)
        """
        self.data = position_data
        self.config = config

    def render_bars(self, fig, row, col):
        """
        Adds position change bar traces to the figure.
        
        Args:
            fig (plotly.Figure): Figure to add traces to
            row (int): Subplot row number
            col (int): Subplot column number
        """
        if self.data.empty or 'date' not in self.data.columns:
            return
            
        bar_width = self.config.get('bar_width', 70000000)
        
        for i, (column, name, color) in enumerate(self.config['columns']):
            if column in self.data.columns:
                fig.add_trace(go.Bar(
                    x=self.data['date'],
                    y=self.data[column],
                    name=name,
                    marker_color=self.config['colors'][color],
                    width=bar_width,
                    offset=i * bar_width,
                    hoverinfo='x+y+name',
                    showlegend=True
                ), row=row, col=col)

class CandlestickRenderer:
    """Renders OHLC candlestick charts with configurable options."""

    def __init__(self, ohlc_data, config):
        """
        Args:
            ohlc_data (pd.DataFrame): OHLC data with 'date', 'open', 'high', 'low', 'close' columns
            config (dict): Configuration for rendering (colors, styles, etc.)
        """
        self.ohlc_data = ohlc_data
        self.config = config

    def render(self, fig, row, col):
        """
        Adds candlestick trace to the figure.

        Args:
            fig (plotly.Figure): Figure to add the trace to
            row (int): Subplot row number
            col (int): Subplot column number
        """
        fig.add_trace(go.Candlestick(
            x=self.ohlc_data['date'],
            open=self.ohlc_data['open'],
            high=self.ohlc_data['high'],
            low=self.ohlc_data['low'],
            close=self.ohlc_data['close'],
            name='OHLC',
            increasing=dict(line=dict(color=self.config.get('increasing_color', 'green'))),
            decreasing=dict(line=dict(color=self.config.get('decreasing_color', 'red')))
        ), row=row, col=col)

    def apply_rangebreaks(self, fig, row, col):
        """
        Applies rangebreaks to the x-axis to hide non-trading periods.

        Args:
            fig (plotly.Figure): Figure to modify
            row (int): Subplot row number
            col (int): Subplot column number
        """
        processor = OHLCProcessor(self.ohlc_data)
        fig.update_xaxes(
            rangebreaks=processor.get_rangebreaks(),
            row=row,
            col=col
        )


def register_callbacks(app):
    # Callback to toggle the foldable menu for "Legacy - Combined"

    @app.callback(
        Output({'type': 'cot-collapse', 'section': MATCH}, 'is_open'),
        Input({'type': 'cot-toggle', 'section': MATCH}, 'n_clicks'),
        State({'type': 'cot-collapse', 'section': MATCH}, 'is_open'),
        prevent_initial_call=True
    )
    def toggle_cot_sections(n_clicks, is_open):
        """Handle toggle state for all COT sections using pattern matching"""
        if n_clicks:
            return not is_open
        return is_open

    @app.callback(
        Output('ohlc-cycles-collapse', 'is_open'),
        Input('ohlc-cycles-toggle', 'n_clicks'),
        State('ohlc-cycles-collapse', 'is_open')
    )
    def toggle_ohlc_cycles(n_clicks, is_open):
        """Toggle OHLC & Cycles section (legacy components)"""
        if n_clicks:
            return not is_open
        return is_open

    @app.callback(
        Output('active-subplots', 'data'),
        [Input({'type': 'cot-checklist', 'report-type': ALL}, 'value')],
        [State({'type': 'cot-checklist', 'report-type': ALL}, 'id')],

        prevent_initial_call=True
    )
    def update_active_subplots(checklist_values, checklist_ids):
        active_subplots = []

        for value, id_dict in zip(checklist_values, checklist_ids):
            if not value or 'report-type' not in id_dict:
                continue
                
            report_type = id_dict['report-type']
            print(f"REPORT TYPE: {report_type}")

            # Correct format: {metric_part}-{cot_type}-{section_name}
            # Use regex to handle hyphenated section names properly
            match = re.match(r'^(.+)-(legacy|disaggregated|tff)-(.+)$', report_type)
            if match:
                metric_part = match.group(1)
                cot_type = match.group(2)
                section_name = match.group(3)
            else:
                print(f"Invalid report type format: {report_type}")
                continue

            # Map metric parts to display names
            metric_map = {
                'open-interest': 'Open Interest',
                'oi-percentages': 'OI Percentages',
                'positions-change': 'Positions Change',
                'net-positions': 'Net Positions',
                'net-positions-change': 'Net Positions Change',
                '26w-index': '26W Index'  # Explicit mapping for 26w index
            }
            display_metric = metric_map.get(metric_part, metric_part.replace('-', ' ').title())

            # Add activated subplots
            if display_metric in value:
                # Check if this is a calculated metric that needs _calc suffix
                calculated_metrics = ['Positions Change', 'Net Positions', 'Net Positions Change', '26W Index']
                section_type = 'combined' if 'combined' in section_name else 'futures_only'
                if display_metric in calculated_metrics and not section_type.endswith('_calc'):
                    section_type += '_calc'
                active_subplots.append((display_metric, section_type, cot_type.lower()))
        print(f"Active Subplots: {active_subplots}")
        return active_subplots

    @app.callback(
        Output('combined-chart', 'figure'),
        [Input('active-subplots', 'data'),
         Input('years-checklist', 'value'),
         Input('ohlc-checklist', 'value'),
         Input('stored-market', 'data'),
         Input('current-year', 'data'),
         Input('combined-chart', 'relayoutData'),
         Input('combined-chart', 'hoverData'),
         Input('combined-chart', 'clickData')],
        prevent_initial_call=False
    )
    def update_graph(active_subplots, selected_years, ohlc_visibility, stored_market, current_year, relayout_data, hover_data, click_data):
        # Phase 1: Debug instrumentation
        print(f"\n=== GRAPH UPDATE START ===\nActive subplots: {active_subplots}")
        assert isinstance(active_subplots, list), "Invalid active_subplots type"
        
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
        # Phase 1: Data pipeline validation
        print(f"Fetching OHLC data for {stored_market} ({current_year})")
        ohlc_fetcher = OHLCFetcher()
        ohlc_df = ohlc_fetcher.fetch_data({
            'market': stored_market,
            'start_date': start_date_str,
            'end_date': end_date_str
        })
        
        if not ohlc_df.empty:
            print(f"Retrieved {len(ohlc_df)} OHLC records | Date range: {ohlc_df['date'].min()} to {ohlc_df['date'].max()}")
        else:
            print("WARNING: Empty OHLC data returned!")

        if ohlc_df.empty:
            # Phase 1: Empty state validation
            print("Rendering empty data state")
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
            annotation_manager = AnnotationManager(fig)
            annotation_manager.add_annotation(
                text=f"No data available for {stored_market} year {current_year}.",
                x=0.5,
                y=0.5,
                font_size=20,
                color="white",
                align="center"
            )
            return fig

        # Initialize interaction and viewport handlers
        range_mgr = RangeManager(ohlc_df)
        viewport_handler = ViewportHandler(range_mgr)
        interaction_tracker = InteractionTracker()
        
        # Configure interactive features and handle events
        fig = interaction_tracker.configure_hover(fig)
        fig = interaction_tracker.configure_trace_hover(fig)
        interaction_tracker.handle_hover(hover_data)
        interaction_tracker.handle_click(click_data)
        
        # Detect year change triggers
        ctx_graph_reset = callback_context
        triggered_prop = ctx_graph_reset.triggered[0]['prop_id'] if ctx_graph_reset.triggered else None
        reset_required = triggered_prop in ['current-year.data']

        # Handle zoom/pan interactions and get validated viewport ranges
        # ViewportHandler manages: initial ranges, user interactions, and resets
        x_range, y_range = viewport_handler.handle_relayout(relayout_data, reset_required)

        # Add OHLC chart
        if 'OHLC' in ohlc_visibility and not ohlc_df.empty:
            renderer = CandlestickRenderer(ohlc_df, CANDLESTICK_CONFIG)
            renderer.render(fig, row=1, col=1)
            renderer.apply_rangebreaks(fig, row=1, col=1)

        if user_tier == 'premium':
            # Add Seasonality chart
            for years in selected_years:
                seasonality_fetcher = SeasonalityFetcher()
                df = seasonality_fetcher.fetch_data({
                    'market': format_market_name(stored_market),
                    'years': years,
                    'base_year': current_year
                })
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

        # Phase 1: Subplot results validation
        row_index = 2
        print(f"Processing {len(active_subplots)} subplots:")
        for i, (subplot, table_suffix, report_type) in enumerate(active_subplots, 1):
            print(f"  [{i}/{len(active_subplots)}] {subplot} | {table_suffix} | {report_type}")
            subplot_fetcher = SubplotFetcher()
            df = subplot_fetcher.fetch_data({
                'market': stored_market,
                'year': current_year,
                'subplot_type': subplot,
                'table_suffix': table_suffix,
                'report_type': report_type
            })
            df = df.apply(pd.to_numeric, errors='coerce')

            if not df.empty:

                df['date'] = pd.to_datetime(df['date'])
                # Create and configure range filter
                range_filter = RangeFilter(df) \
                    .set_date_column('date') \
                    .apply_viewport_filter(x_range)
                filtered_data = range_filter \
                    .subsample_for_performance(max_points=1000) \
                    .get_filtered_data()

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
                    # No manual y_range computation; RangeManager handles it
                    # filtered_y_range = [filtered_data.iloc[:, 1:].min().min(), filtered_data.iloc[:, 1:].max().max()]
                    # y_range is already set earlier
                    
                    # Apply price range constraints
                    range_filter = RangeFilter(filtered_data) \
                        .set_price_columns(['open', 'high', 'low', 'close']) \
                        .apply_price_constraints(y_range)
                        
                    filtered_data = range_filter.get_filtered_data()

                if subplot == 'Positions Change':
                    df['date'] = pd.to_datetime(df['date'])
                    filtered_data = df[(df['date'] >= x_range[0]) & (df['date'] <= x_range[1])]
                    
                    if report_type == 'legacy':
                        config = POSITION_CHANGE_CONFIG.get('legacy')
                        if config:
                            visuals = PositionChangeVisuals(filtered_data, config)
                            visuals.render_bars(fig, row=row_index, col=1)

                    elif report_type == 'disaggregated':
                        config = POSITION_CHANGE_CONFIG.get('disaggregated')
                        if config:
                            visuals = PositionChangeVisuals(filtered_data, config)
                            visuals.render_bars(fig, row=row_index, col=1)

                    elif report_type == 'tff':
                        config = POSITION_CHANGE_CONFIG.get('tff')
                        if config:
                            visuals = PositionChangeVisuals(filtered_data, config)
                            visuals.render_bars(fig, row=row_index, col=1)

                elif subplot == 'Net Positions Change':

                    df['date'] = pd.to_datetime(df['date'])
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
            legend={**Config.LEGEND_PRESETS['top_left'].__dict__, 'y': 0.99, 'x': 0.01},
            legend_bgcolor=Config.LEGEND_PRESETS['top_left'].bgcolor,
            plot_bgcolor="#1e1e1e",
            paper_bgcolor='#1e1e1e',
            font=dict(
                family="'Press Start 2P', monospace",
                size=10,
                color='white'
            ),
            dragmode="pan"
        )

        # Phase 1: Final validation
        print(f"Finalizing layout with {num_rows} rows")
        assert num_rows == 1 + len(active_subplots), "Subplot row count mismatch"
        
        # Apply axis presets to all subplots
        for i in range(1, num_rows + 1):
            print(f"Updating axes for row {i}/{num_rows}")
            fig.update_xaxes({**Config.AXIS_PRESETS['default'].__dict__, 'range': x_range}, row=i, col=1)
            fig.update_yaxes(Config.AXIS_PRESETS['default'].__dict__, row=i, col=1)


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
        [Input('prev-year-button-main', 'n_clicks'),
         Input('next-year-button-main', 'n_clicks'),
         Input('prev-year-button-right-panel', 'n_clicks'),
         Input('next-year-button-right-panel', 'n_clicks'),
         ],
        [State('current-year', 'data')]
    )
    def update_year(n_clicks_main_prev, n_clicks_main_next, n_clicks_right_panel_prev, n_clicks_right_panel_next, current_year):
        if ctx.triggered:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
            if 'prev-year-button-main' in button_id or 'prev-year-button-right-panel' in button_id:
                return max(1994, current_year - 1)
            elif 'next-year-button-main' in button_id or 'next-year-button-right-panel' in button_id:
                return min(2025, current_year + 1)
        return current_year

    # Combined callback for market updates
    @app.callback(
        [Output('stored-market', 'data'),
         Output('market-dropdown', 'value')],  # Add this Output to update the dropdown's value
        [Input('market-dropdown', 'value'),
         Input('prev-market-button-main', 'n_clicks'),
         Input('next-market-button-main', 'n_clicks'),
         Input('prev-market-button-right-panel', 'n_clicks'),
         Input('next-market-button-right-panel', 'n_clicks'),
         ],
        [State('stored-market', 'data')]
    )
    def update_stored_market(selected_market, n_clicks_main_prev, n_clicks_main_next,
                             n_clicks_right_panel_prev, n_clicks_right_panel_next, current_market):

        # Determine which input triggered the callback
        triggered_input = ctx.triggered[0]['prop_id'].split('.')[0]

        # Handle dropdown selection
        if 'market-dropdown' in triggered_input:
            new_market = next((m_name for m_name, m_ticker in market_tickers.items() if m_ticker == selected_market),
                              DEFAULT_MARKET)
            return new_market, selected_market  # Return both the updated stored-market and the dropdown value

        # Handle Previous and Next Market button clicks
        elif ('prev-market-button-main' in triggered_input
              or 'next-market-button-main' in triggered_input
              or 'prev-market-button-right-panel' in triggered_input
              or 'next-market-button-right-panel' in triggered_input):
            markets = list(market_tickers.keys())  # Keep the original order from config.py
            current_index = markets.index(current_market) if current_market in markets else 0

            if 'prev-market-button-main' in triggered_input or 'prev-market-button-right-panel' in triggered_input:
                # Move to the previous market
                new_index = (current_index - 1) % len(markets)
            elif 'next-market-button-main' in triggered_input or 'next-market-button-right-panel' in triggered_input:
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
            [Output('ohlc-data-store', 'data'),
             Output('seasonality-data-store', 'data'),
             Output('subplot-data-store', 'data')],
            [Input('perform-analysis-button', 'n_clicks'),
             Input('interval-auto-load', 'n_intervals')],
            [State('date-picker-range', 'start_date'),
             State('date-picker-range', 'end_date'),
             State('stored-market', 'data'),
             State('years-checklist', 'value')]
        )
        def fetch_all_data(n_clicks, n_intervals, start_date, end_date, stored_market, years_range):
            if not n_clicks and not n_intervals:
                return None, None, None

            # Convert dates
            start_month, start_day = pd.to_datetime(start_date).month, pd.to_datetime(start_date).day
            end_month, end_day = pd.to_datetime(end_date).month, pd.to_datetime(end_date).day

            # Fetch OHLC data
            ohlc_fetcher = OHLCFetcher()
            ohlc_data = ohlc_fetcher.fetch_data({
                'market': stored_market,
                'start_date': start_date,
                'end_date': end_date
            }).to_dict('records')

            # Fetch seasonality data
            seasonality_data = {}
            if user_tier == 'premium':
                seasonality_fetcher = SeasonalityFetcher()
                for years in years_range:
                    seasonality_data[years] = seasonality_fetcher.fetch_data({
                        'market': format_market_name(stored_market),
                        'years': years,
                        'base_year': 2025
                        # Current year
                    }).to_dict('records')

                    # Fetch subplot data
            subplot_data = {}
            subplot_fetcher = SubplotFetcher()
            # Add your subplot data fetching logic here

            return ohlc_data, seasonality_data, subplot_data

        @app.callback(
            Output('processed-data-store', 'data'),
            [Input('ohlc-data-store', 'data'),
             Input('seasonality-data-store', 'data'),
             Input('subplot-data-store', 'data')],
            [State('direction-dropdown', 'value'),
             State('years-checklist', 'value')],
            prevent_initial_call=True
        )
        def process_data(ohlc_data, seasonality_data, subplot_data, direction, years_range):
            # Handle None inputs
            if ohlc_data is None and seasonality_data is None and subplot_data is None:
                return None
            
            # Convert stored data back to DataFrames
            ohlc_df = pd.DataFrame(ohlc_data) if ohlc_data else pd.DataFrame()
            seasonality_dfs = {years: pd.DataFrame(data) for years, data in (seasonality_data or {}).items()}
            subplot_dfs = {key: pd.DataFrame(data) for key, data in (subplot_data or {}).items()}

            # Initialize data processor
            processor = DataProcessor()
        
            # Process OHLC data
            if not ohlc_df.empty:
                ohlc_df = processor.validate_structure(ohlc_df)
                ohlc_df = processor.clean_data(ohlc_df)
                ohlc_df = processor.transform_data(ohlc_df)
        
            # Process seasonality data
            processed_seasonality = {}
            for years, df in seasonality_dfs.items():
                if not df.empty:
                    df = processor.validate_structure(df)
                    df = processor.clean_data(df)
                    df = processor.transform_data(df)
                    processed_seasonality[years] = df.to_dict('records')
        
            # Process subplot data
            processed_subplots = {}
            for key, df in subplot_dfs.items():
                if not df.empty:
                    df = processor.validate_structure(df)
                    df = processor.clean_data(df)
                    df = processor.transform_data(df)
                    processed_subplots[key] = df.to_dict('records')
        
            # Return processed data
            return {
                'ohlc': ohlc_df.to_dict('records'),
                'seasonality': processed_seasonality,
                'subplots': processed_subplots,
                'direction': direction,
                'years_range': years_range
            }

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
                Output('pdh-pdl-pdhl-high-vs-prev-high-dist', 'figure')],
            [Input('processed-data-store', 'data'),
             Input('perform-analysis-button', 'n_clicks'),
             Input('interval-auto-load', 'n_intervals'),
             ],
            [State('date-picker-range', 'start_date'),
             State('date-picker-range', 'end_date'),
             State('direction-dropdown', 'value'),
             State('years-checklist', 'value'),
             State('stored-market', 'data')],
            prevent_initial_call=True
        )
        def perform_analysis_and_update_layout(processed_data, n_clicks, n_intervals,
                                               start_date, end_date, direction, years_range, stored_market):

            # Get processed data
            ohlc_df = pd.DataFrame(processed_data.get('ohlc', []))
            seasonality_dfs = {years: pd.DataFrame(data) for years, data in
                               processed_data.get('seasonality', {}).items()}
            subplot_dfs = {key: pd.DataFrame(data) for key, data in processed_data.get('subplots', {}).items()}

            start_month, start_day = pd.to_datetime(start_date).month, pd.to_datetime(start_date).day
            end_month, end_day = pd.to_datetime(end_date).month, pd.to_datetime(end_date).day

            # Define empty components for error cases
            empty_fig = go.Figure()
            empty_components = [
                [],  # yearly-analysis-table.data
                "No data available",  # 15-year-summary.children
                "No data available",  # 30-year-summary.children
                empty_fig,  # distribution-chart-15.figure
                empty_fig,  # distribution-chart-optimal-15.figure
                empty_fig,  # distribution-chart-30.figure
                empty_fig,  # distribution-chart-optimal-30.figure
                empty_fig,  # cumulative-return-chart-15.figure
                empty_fig,  # cumulative-return-chart-30.figure
                "No data available",  # risk-metrics-summary-15.children
                "No data available",  # risk-metrics-summary-30.children
                "No data available",  # risk-metrics-summary-15-stoploss.children
                "No data available",  # risk-metrics-summary-30-stoploss.children
                [],  # day-trading-stats-table.data
                [],  # day-trading-stats-1-table.data
                [],  # day-trading-stats-weekday-table.data
                [],  # day-trading-stats-1-weekday-table.data
                empty_fig,  # dup-open-high-dist.figure
                empty_fig,  # dup-open-low-dist.figure
                empty_fig,  # dup-open-close-dist.figure
                empty_fig,  # dup-open-low-vs-high-scatter.figure
                empty_fig,  # dup-open-low-vs-close-scatter.figure
                empty_fig,  # dup-low-vs-prev-low-dist.figure
                empty_fig,  # dup-high-vs-prev-high-dist.figure
                empty_fig,  # ddown-open-high-dist.figure
                empty_fig,  # ddown-open-low-dist.figure
                empty_fig,  # ddown-open-close-dist.figure
                empty_fig,  # ddown-open-low-vs-high-scatter.figure
                empty_fig,  # ddown-open-low-vs-close-scatter.figure
                empty_fig,  # ddown-low-vs-prev-low-dist.figure
                empty_fig,  # ddown-high-vs-prev-high-dist.figure
                empty_fig,  # pdh-open-high-dist.figure
                empty_fig,  # pdh-open-low-dist.figure
                empty_fig,  # pdh-open-close-dist.figure
                empty_fig,  # pdh-open-low-vs-high-scatter.figure
                empty_fig,  # pdh-open-low-vs-close-scatter.figure
                empty_fig,  # pdh-high-vs-prev-high-dist.figure
                empty_fig,  # pdl-open-high-dist.figure
                empty_fig,  # pdl-open-low-dist.figure
                empty_fig,  # pdl-open-close-dist.figure
                empty_fig,  # pdl-open-low-vs-high-scatter.figure
                empty_fig,  # pdl-open-low-vs-close-scatter.figure
                empty_fig,  # pdl-low-vs-prev-low-dist.figure
                empty_fig,  # pdhl-open-high-dist.figure
                empty_fig,  # pdhl-open-low-dist.figure
                empty_fig,  # pdhl-open-close-dist.figure
                empty_fig,  # pdhl-open-low-vs-high-scatter.figure
                empty_fig,  # pdhl-open-low-vs-close-scatter.figure
                empty_fig,  # pdhl-low-vs-prev-low-dist.figure
                empty_fig,  # pdhl-high-vs-prev-high-dist.figure
                empty_fig,  # pdh-pdl-pdhl-open-high-dist.figure
                empty_fig,  # pdh-pdl-pdhl-open-low-dist.figure
                empty_fig,  # pdh-pdl-pdhl-open-close-dist.figure
                empty_fig,  # pdh-pdl-pdhl-open-low-vs-high-scatter.figure
                empty_fig,  # pdh-pdl-pdhl-open-low-vs-close-scatter.figure
                empty_fig,  # pdh-pdl-pdhl-low-vs-prev-low-dist.figure
                empty_fig,  # pdh-pdl-pdhl-high-vs-prev-high-dist.figure
            ]

            # Initialize all queues with proper error handling
            try:
                fetching_queue = FetchingQueue()
                processing_queue = ProcessingQueue()
                analysis_queue = AnalysisQueue()
                visualization_queue = VisualizationQueue()
                
                # Log queue initialization status
                print(f"FetchingQueue initialized: {fetching_queue.get_queue_status()}")
                print(f"ProcessingQueue initialized: {processing_queue.get_queue_status()}")
                print(f"AnalysisQueue initialized: {analysis_queue.get_queue_status()}")
                print(f"VisualizationQueue initialized: {visualization_queue.get_queue_status()}")
            except Exception as e:
                print(f"Failed to initialize queues: {e}")
                return tuple(empty_components)
            
            # Create and enqueue fetching contracts
            current_year = 2025
            ohlc_data_all_years = pd.DataFrame()
            
            # Try years in reverse order (most recent first)
            # Handle year offsets with proper boundary checking
            for year_offset in sorted(years_range, reverse=True):
                target_year = current_year - year_offset
                end_date_str = f'{current_year}-{end_month:02d}-{end_day:02d}'
                
                # Try up to 3 previous years if no data found, starting from target year
                for attempt in range(3):
                    try_year = target_year - attempt
                    if try_year < 1990 or try_year > current_year:
                        continue
                        
                    print(f"Attempting year {try_year} (attempt {attempt + 1})")
                    
                    # Fetch data for this year
                    ohlc_data_year = fetch_ohlc_data_cached(
                        stored_market,
                        f'{try_year}-{start_month:02d}-{start_day:02d}',
                        end_date_str
                    )

                    if not ohlc_data_year.empty:
                        # Create contract with string dates
                        contract = FetchingContract(
                            market=stored_market,
                            start_date=f'{try_year}-{start_month:02d}-{start_day:02d}',
                            end_date=end_date_str,
                            raw_data=ohlc_data_year
                        )
                        
                        if fetching_queue.enqueue_fetching_contract(contract):
                            print(f"Successfully enqueued contract for {try_year}")
                            break  # Move to next year offset
                        else:
                            print(f"Failed to enqueue contract for {try_year}")
                    else:
                        print(f"No data found for {stored_market} from {try_year}-{start_month:02d}-{start_day:02d} to {end_date_str}")
                else:
                    print(f"Exhausted all attempts for year offset {year_offset}")

            # Process fetched data through processing queue
            while True:
                contract = fetching_queue.dequeue_fetching_contract()
                if not contract:
                    break
                
                # Fetch data using the contract
                ohlc_data_year = fetch_ohlc_data_cached(
                    contract.market,
                    contract.start_date.strftime('%Y-%m-%d'),
                    contract.end_date.strftime('%Y-%m-%d')
                )
                
                if not ohlc_data_year.empty:
                    # Create processing contract
                    processing_contract = ProcessingContract(
                        raw_data=ohlc_data_year,
                        validation_rules={},
                        cleaning_steps={},
                        transformation_steps={}
                    )
                    
                    # Enqueue for processing
                    if processing_queue.enqueue_processing_contract(processing_contract):
                        print(f"Enqueued processing contract for {contract.market} {contract.start_date}")
                    else:
                        print(f"Failed to enqueue processing contract for {contract.market} {contract.start_date}")
                        continue
                        
                    # Process the data
                    processed_contract = processing_queue.dequeue_processing_contract()
                    if processed_contract:
                        try:
                            # Get the processed data from the contract
                            processed_data = processed_contract.raw_data  # Using raw_data instead of processed_data
                            if processed_data is not None:
                                ohlc_data_all_years = pd.concat([ohlc_data_all_years, processed_data], ignore_index=True)
                                print(f"Successfully processed data for {contract.market} {contract.start_date}")
                            else:
                                print(f"Processed data is None for {contract.market} {contract.start_date}")
                        except Exception as e:
                            print(f"Error processing data for {contract.market} {contract.start_date}: {str(e)}")
                    else:
                        print(f"No processed contract available for {contract.market} {contract.start_date}")

            if ohlc_data_all_years.empty:
                # Create empty figure with consistent styling
                empty_fig.update_layout(
                    plot_bgcolor="#1e1e1e",
                    paper_bgcolor="#1e1e1e",
                    xaxis=dict(visible=False),
                    yaxis=dict(visible=False),
                    font=dict(
                        family="'Press Start 2P', monospace",
                        size=10,
                        color='white'
                    )
                )
                return tuple(empty_components)

            # Log queue statuses
            print(f"FetchingQueue status: {fetching_queue.get_queue_status()}")
            print(f"ProcessingQueue status: {processing_queue.get_queue_status()}")
            print(f"AnalysisQueue status: {analysis_queue.get_queue_status()}")
            print(f"VisualizationQueue status: {visualization_queue.get_queue_status()}")

            # Create and enqueue analysis contract with error handling
            try:
                analysis_contract = AnalysisContract(
                    processed_data=ohlc_data_all_years,
                    analysis_results={},
                    metrics={},
                    optimal_values={},
                    risk_metrics={}
                )
                
                if not analysis_queue.enqueue_analysis_contract(analysis_contract):
                    print("Failed to enqueue analysis contract")
                    return tuple(empty_components)
                    
                # Process analysis through queue with timeout
                analysis_contract = analysis_queue.dequeue_analysis_contract()
                if not analysis_contract:
                    print("Failed to dequeue analysis contract")
                    return tuple(empty_components)
                    
                # Perform analysis on the processed data
                analysis_results = perform_analysis(
                    start_date, 
                    end_date, 
                    direction, 
                    analysis_contract.processed_data
                )
                
                # Update contract with results
                analysis_contract.analysis_results = analysis_results
                
                # Create visualization contract
                visualization_contract = VisualizationContract(
                    analysis_results=analysis_contract.analysis_results,
                    charts={},
                    tables={},
                    summaries={},
                    layout_config={}
                )
                
                # Enqueue visualization contract
                if not visualization_queue.enqueue_visualization_contract(visualization_contract):
                    print("Failed to enqueue visualization contract")
                    return tuple(empty_components)
                    
                # Process visualization through queue
                visualization_contract = visualization_queue.dequeue_visualization_contract()
                if not visualization_contract:
                    print("Failed to dequeue visualization contract")
                    return tuple(empty_components)
                
                # Log successful analysis and visualization
                print(f"Analysis completed successfully for {stored_market} {start_date} to {end_date}")
                print(f"Analysis queue status: {analysis_queue.get_queue_status()}")
                print(f"Visualization queue status: {visualization_queue.get_queue_status()}")
                
            except Exception as e:
                print(f"Error during analysis/visualization: {e}")
                return tuple(empty_components)

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
                                                )
            )

            # Calculate risk metrics using cumulative returns
            risk_metrics_15 = MetricsCalculator.calculate_risk_metrics(daily_returns_15, cum_returns_no_stop_15)
            risk_metrics_30 = MetricsCalculator.calculate_risk_metrics(daily_returns_30, cum_returns_no_stop_30)

            # Calculate stop-loss risk metrics
            stop_loss_metrics_15 = MetricsCalculator.calculate_risk_metrics(daily_returns_15_stoploss, cum_returns_stop_15)
            stop_loss_metrics_30 = MetricsCalculator.calculate_risk_metrics(daily_returns_30_stoploss, cum_returns_stop_30)

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
        ],
        [Input('interval-auto-load', 'n_intervals')]
    )
    def update_correlation_tables(n_intervals):
        # Fetch only 180-day data
        fetcher = RealDataFetcher()
        raw_data = fetcher.fetch_data({'table_name': "correlation_180_days"})
        # Ensure raw_data is list-like
        if not isinstance(raw_data, (list, dict)):
            raw_data = []
        elif isinstance(raw_data, dict):  # Convert single dict to list of dicts for DataFrame
            raw_data = [raw_data]
            
        correlation_180d = pd.DataFrame(raw_data)

        def apply_ticker_prefix(df):
            # Handle case where input isn't a DataFrame
            if not isinstance(df, pd.DataFrame):
                return pd.DataFrame()
                
            # Return empty DF if no data or missing required column
            if df.empty or 'market_1' not in df.columns:
                return pd.DataFrame()

            df['MKT'] = df['market_1'].map(ticker_prefixes)
            df['market_2'] = df['market_2'].map(ticker_prefixes)
            df = df.groupby(['MKT', 'market_2'], as_index=False).agg({'correlation': 'mean'})
            df = df.pivot(index='MKT', columns='market_2', values='correlation').round(2) * 100
            df = df.astype(int)
            df.reset_index(inplace=True)
            df.columns.name = None
            return df

        correlation_180d = apply_ticker_prefix(correlation_180d)

        # Process columns dynamically
        columns = [{'name': 'MKT', 'id': 'MKT'}]
        if not correlation_180d.empty:
            # Get actual market columns from data
            markets = [col for col in correlation_180d.columns if col != 'MKT']
            columns += [{'name': col, 'id': col} for col in markets]
        
        return (
            correlation_180d.to_dict('records') if not correlation_180d.empty else [],
            columns
        )
