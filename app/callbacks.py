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
                                       'Australian Dollar')
                return selected_market
        return 'Australian Dollar'

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
        default_market = 'DefaultMarketName'  # Replace with your actual default market

        # Determine the selected market based on the trigger
        if ctx.triggered:
            triggered = ctx.triggered[0]['prop_id'].split('.')[0]
            if 'market-link' in triggered:
                triggered_ticker = eval(triggered).get('index')
                stored_market = next((name for name, ticker in market_tickers.items() if ticker == triggered_ticker),
                                     default_market)

        if not stored_market:
            stored_market = default_market

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
                          'Open Interest', row=2, col=1, line_color='orange')
                y_min = open_interest_df['open_interest_all'].min()
                y_max = open_interest_df['open_interest_all'].max()
                update_yaxis(fig, row=2, col=1, title='Open Interest', y_min=y_min, y_max=y_max)

        # Add Open Interest Percentages data if visible
        if 'OI Percentages' in oi_percentages_visibility:
            percentages_df = OpenInterestPercentagesFetcher.fetch_open_interest_percentages(stored_market, current_year)
            if not percentages_df.empty:
                add_trace(fig, percentages_df['Day_of_Year'], percentages_df['pct_of_oi_noncomm_long_all'],
                          '% of OI Non-Commercials Long', row=3, col=1, line_color='blue')
                add_trace(fig, percentages_df['Day_of_Year'], percentages_df['pct_of_oi_noncomm_short_all'],
                          '% of OI Non-Commercials Short', row=3, col=1, line_color='red')
                add_trace(fig, percentages_df['Day_of_Year'], percentages_df['pct_of_oi_comm_long_all'],
                          '% of OI Commercials Long', row=3, col=1, line_color='green')
                add_trace(fig, percentages_df['Day_of_Year'], percentages_df['pct_of_oi_comm_short_all'],
                          '% of OI Commercials Short', row=3, col=1, line_color='purple')
                update_yaxis(fig, row=3, col=1, title='% of Open Interest')

        # Add Positions Change data if visible
        if 'Positions Change' in positions_change_visibility:
            positions_change_df = PositionsChangeDataFetcher.fetch_positions_change_data(stored_market, current_year)
            if not positions_change_df.empty:
                add_trace(fig, positions_change_df['Day_of_Year'], positions_change_df['pct_change_noncomm_long'],
                          '% Change Non-Commercials Long', row=4, col=1, line_color='blue')
                add_trace(fig, positions_change_df['Day_of_Year'], positions_change_df['pct_change_noncomm_short'],
                          '% Change Non-Commercials Short', row=4, col=1, line_color='red')
                add_trace(fig, positions_change_df['Day_of_Year'], positions_change_df['pct_change_comm_long'],
                          '% Change Commercials Long', row=4, col=1, line_color='green')
                add_trace(fig, positions_change_df['Day_of_Year'], positions_change_df['pct_change_comm_short'],
                          '% Change Commercials Short', row=4, col=1, line_color='purple')
                update_yaxis(fig, row=4, col=1, title='% Change in Positions')

        # Add Net Positions data if visible
        if 'Net Positions' in net_positions_visibility:
            net_positions_df = NetPositionsDataFetcher.fetch_net_positions_data(stored_market, current_year)
            if not net_positions_df.empty:
                add_trace(fig, net_positions_df['Day_of_Year'], net_positions_df['noncomm_net_positions'],
                          'Net Positions Non-Commercials', row=5, col=1, line_color='blue')
                add_trace(fig, net_positions_df['Day_of_Year'], net_positions_df['comm_net_positions'],
                          'Net Positions Commercials', row=5, col=1, line_color='red')
                update_yaxis(fig, row=5, col=1, title='Net Positions')

        # Add Net Positions Change data if visible
        if 'Net Positions Change' in net_positions_change_visibility:
            net_positions_change_df = PositionsChangeNetDataFetcher.fetch_positions_change_net_data(stored_market,
                                                                                                    current_year)
            if not net_positions_change_df.empty:
                add_trace(fig, net_positions_change_df['Day_of_Year'],
                          net_positions_change_df['pct_change_noncomm_net_positions'],
                          '% Change Net Positions Non-Commercials', row=6, col=1, line_color='blue')
                add_trace(fig, net_positions_change_df['Day_of_Year'],
                          net_positions_change_df['pct_change_comm_net_positions'],
                          '% Change Net Positions Commercials', row=6, col=1, line_color='red')
                update_yaxis(fig, row=6, col=1, title='% Change in Net Positions')

        # Add 26-Week Index data if visible
        if '26W Index' in index_26w_visibility:
            index_26w_df = Index26WDataFetcher.fetch_26w_index_data(stored_market, current_year)
            if not index_26w_df.empty:
                add_trace(fig, index_26w_df['Day_of_Year'], index_26w_df['noncomm_26w_index'],
                          'Non-Commercials 26W Index', row=7, col=1, line_color='red')
                add_trace(fig, index_26w_df['Day_of_Year'], index_26w_df['comm_26w_index'],
                          'Commercials 26W Index', row=7, col=1, line_color='blue')
                add_shape(fig, index_26w_df['Day_of_Year'].min(), index_26w_df['Day_of_Year'].max(), 50, 50, row=7,
                          col=1)
                update_yaxis(fig, row=7, col=1, title='26-Week Index')

        fig.update_layout(title=f'{stored_market} Data Overview', height=2000, showlegend=True)

        return fig




