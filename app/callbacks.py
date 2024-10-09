# callbacks.py
from dash import Input, Output, State, ctx, html, dcc
# from dash.dash_table.Format import Format, FormatTemplate
import dash
import numpy as np
from datetime import timedelta
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
import matplotlib.pyplot as plt
# from scipy.stats import norm

# Constants for trace colors and default values
DEFAULT_MARKET = 'SP 500'
DEFAULT_YEAR = 2024

COLORS = {
    'open_interest': 'orange',
    'comm_long': 'red',
    'comm_short': 'pink',
    'noncomm_long': 'blue',
    'noncomm_short': 'lightblue',
    'other_long': 'green',
    'other_short': 'lightgreen',
    'seasonality_15y': '#ff7e67',
    'seasonality_35y': '#347474',
}


def add_trace(fig, x, y, name, row, col, mode='lines', line_color=None, secondary_y=False, chart_type='line',
              opacity=1, hide_yaxis_ticks=False, bar_width = None, bar_offset = None, show_legend=True, disable_hover=False):
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
        hide_yaxis_ticks: Boolean to indicate whether to hide the y-axis ticks for this trace.
    """
    if chart_type == 'line':
        trace = go.Scatter(x=x, y=y, mode=mode, name=name, line=dict(color=line_color), showlegend=show_legend,
                           opacity=opacity, connectgaps=True, hoverinfo='skip' if disable_hover else 'x+y')
    elif chart_type == 'bar':
        trace = go.Bar(x=x, y=y, name=name, marker=dict(color=line_color), showlegend=show_legend, opacity=opacity,
                       width=bar_width, offset=bar_offset, hovertemplate='%{y}<extra></extra>')

    fig.add_trace(trace, row=row, col=col, secondary_y=secondary_y)
    fig.update_layout(bargap=0.2)


    # If hide_yaxis_ticks is True, hide the y-axis tick labels
    if hide_yaxis_ticks:
        fig.update_yaxes(showticklabels=False, row=row, col=col, secondary_y=secondary_y)


def add_candlestick_trace(fig, x, open, high, low, close, name, row, col, secondary_y=False):
    trace = go.Candlestick(x=x, open=open, high=high, low=low, close=close, name=name,
                           yaxis='y2', hoverinfo='x+y', showlegend=False, increasing_line_color="white", decreasing_line_color="white",
                           increasing_fillcolor="white", decreasing_fillcolor="black")
    fig.add_trace(trace, row=row, col=col, secondary_y=secondary_y)
    # Ensure the y-axis is fixed
    fig.update_yaxes(
        fixedrange=False,  # Disable y-axis zoom
        row=row,
        col=col
    )

def update_yaxis(fig, row, col, title, y_min=None, y_max=None, secondary_y=False):
    fig.update_yaxes(title_text=title, row=row, col=col, range=[y_min, y_max], secondary_y=secondary_y)

def add_shape(fig, x0, x1, y0, y1, row, col, color='gray', dash='dash'):
    fig.add_shape(type='line', x0=x0, x1=x1, y0=y0, y1=y1, line=dict(color=color, dash=dash), row=row, col=col)



def compare_portfolios(start_month, start_day, end_month, end_day, direction, ohlc_data, number_of_years_to_combine):
    """
    Function to compare no stop-loss vs stop-loss and optimal exit portfolios over a 15 or 30 year period.
    Parameters:
        - start_month: int, start month for the trade window
        - start_day: int, start day for the trade window
        - end_month: int, end month for the trade window
        - end_day: int, end day for the trade window
        - direction: str, 'Long' or 'Short'
        - ohlc_data: pd.DataFrame, historical OHLC data
        - number_of_years_to_combine: int, number of years (15 or 30)
    Returns:
        - two line charts comparing daily gain/loss % with and without stop-loss/optimal exit
        - risk metrics for comparison
    """
    combined_no_stop_loss = pd.DataFrame()
    combined_with_stop_loss = pd.DataFrame()

    # Get unique years
    unique_years = sorted(ohlc_data['Date'].dt.year.unique())[-number_of_years_to_combine:]

    for year in unique_years:
        # Slice OHLC data for the year
        yearly_data = ohlc_data[ohlc_data['Date'].dt.year == year]
        start_data = find_nearest_date(yearly_data, f"{year}-{start_month:02d}-{start_day:02d}")
        end_data = find_nearest_date(yearly_data, f"{year}-{end_month:02d}-{end_day:02d}")

        if start_data is None or end_data is None:
            continue

        # Get the sliced data for this year between start and end dates
        sliced_year_data = yearly_data[
            (yearly_data['Date'] >= start_data['Date']) & (yearly_data['Date'] <= end_data['Date'])]

        # Append sliced data to combined data for no stop loss
        combined_no_stop_loss = pd.concat([combined_no_stop_loss, sliced_year_data], ignore_index=True)

        # Simulate stop loss and optimal exit for this slice
        points_change, percentage_change = simulate_optimal_trades(sliced_year_data, direction)

        # Combine with stop-loss data
        sliced_year_data['Gain/Loss (%)'] = percentage_change
        combined_with_stop_loss = pd.concat([combined_with_stop_loss, sliced_year_data], ignore_index=True)

    # Sort by Date to create a continuous portfolio
    combined_no_stop_loss.sort_values(by='Date', inplace=True)
    combined_with_stop_loss.sort_values(by='Date', inplace=True)

    # Calculate daily returns for both portfolios
    combined_no_stop_loss['Daily Return (%)'] = combined_no_stop_loss['Close'].pct_change() * 100
    combined_with_stop_loss['Daily Return (%)'] = combined_with_stop_loss['Gain/Loss (%)']

    # Calculate cumulative returns
    combined_no_stop_loss['Cumulative Return'] = (1 + combined_no_stop_loss['Daily Return (%)'] / 100).cumprod() - 1
    combined_with_stop_loss['Cumulative Return'] = (1 + combined_with_stop_loss['Daily Return (%)'] / 100).cumprod() - 1

    # Calculate Sharpe ratio
    sharpe_no_stop_loss = calculate_sharpe_ratio(combined_no_stop_loss['Daily Return (%)'])
    sharpe_with_stop_loss = calculate_sharpe_ratio(combined_with_stop_loss['Daily Return (%)'])

    # Plotting the results
    plt.figure(figsize=(12, 6))

    plt.subplot(1, 2, 1)
    plt.plot(combined_no_stop_loss['Date'], combined_no_stop_loss['Cumulative Return'], label="No Stop Loss",
             color='blue')
    plt.plot(combined_with_stop_loss['Date'], combined_with_stop_loss['Cumulative Return'], label="With Stop Loss",
             color='green')
    plt.title(f"Cumulative Returns over {number_of_years_to_combine} years")
    plt.legend()

    plt.subplot(1, 2, 2)
    plt.plot(combined_no_stop_loss['Date'], combined_no_stop_loss['Daily Return (%)'], label="No Stop Loss",
             color='blue')
    plt.plot(combined_with_stop_loss['Date'], combined_with_stop_loss['Daily Return (%)'], label="With Stop Loss",
             color='green')
    plt.title(f"Daily Returns over {number_of_years_to_combine} years")
    plt.legend()

    plt.show()

    # Return risk metrics
    return {
        "Sharpe Ratio (No Stop Loss)": sharpe_no_stop_loss,
        "Sharpe Ratio (With Stop Loss)": sharpe_with_stop_loss
    }


def calculate_sharpe_ratio(daily_returns):
    """
    Function to calculate Sharpe ratio.
    Parameters:
        - daily_returns: pd.Series, daily return percentages
    Returns:
        - sharpe_ratio: float, calculated Sharpe ratio
    """
    mean_return = daily_returns.mean()
    std_dev = daily_returns.std()
    sharpe_ratio = mean_return / std_dev * np.sqrt(252)  # Assuming 252 trading days per year
    return sharpe_ratio

def calculate_sortino_ratio(daily_returns, risk_free_rate=0):
    """
    Function to calculate Sortino ratio.
    Parameters:
        - daily_returns: pd.Series, daily return percentages
        - risk_free_rate: float, assumed risk-free rate (default is 0)
    Returns:
        - sortino_ratio: float, calculated Sortino ratio
    """
    negative_returns = daily_returns[daily_returns < risk_free_rate]
    mean_return = daily_returns.mean()
    downside_std_dev = negative_returns.std()
    sortino_ratio = (mean_return - risk_free_rate) / downside_std_dev * np.sqrt(252)  # Annualize using 252 trading days
    return sortino_ratio


def calculate_maximum_drawdown(cumulative_returns):
    """
    Function to calculate Maximum Drawdown as the largest peak-to-trough decline in percentage points.
    It tracks peaks as they occur, and calculates the drawdown at each step, simulating Excel's
    MIN((A1-MAX($A$1:A1)),0) approach.

    Parameters:
        - cumulative_returns: pd.Series, cumulative returns over time (in percentage points).

    Returns:
        - max_drawdown: float, calculated Maximum Drawdown in percentage points.
    """
    # Step 1: Calculate the rolling maximum (the peak up to that point)
    cumulative_returns.to_csv('cumulative_returns.csv', index=True)

    cumulative_max = cumulative_returns.cummax()

    # Step 2: Calculate the drawdown as the difference between the peak and the current value
    drawdown = cumulative_returns - cumulative_max

    # Step 3: Find the maximum drawdown (i.e., the largest negative value in the drawdown series)
    max_drawdown = drawdown.min()  # This returns the most negative value, which represents the max drawdown

    drawdown.to_csv('drawdown.csv', index=False)

    # Step 4: Return the absolute value of max drawdown, as we want the magnitude of the drawdown
    return abs(max_drawdown)



def calculate_calmar_ratio(daily_returns, max_drawdown):
    # Calculate the Calmar ratio using annualized returns and max drawdown
    annualized_return = daily_returns.mean() * 252  # Assuming 252 trading days per year
    calmar_ratio = annualized_return / abs(max_drawdown)
    return calmar_ratio


def calculate_volatility(daily_returns):
    """
    Function to calculate Volatility.
    Parameters:
        - daily_returns: pd.Series, daily return percentages
    Returns:
        - volatility: float, calculated annualized volatility.
    """
    # No need to multiply by 100 as daily_returns are already in percentage format
    volatility = daily_returns.std() * np.sqrt(252)
    return volatility



def find_nearest_date(data, target_date, max_delta=3):
    """
    Find the nearest available date within a range of ±max_delta days from the target date.

    Args:
        data (pd.DataFrame): The OHLC data with a 'Date' column.
        target_date (str): The target date in "YYYY-MM-DD" format.
        max_delta (int): The maximum number of days to search before or after the target date.

    Returns:
        pd.Series or None: The row with the nearest date found, or None if no data is found within the range.
    """
    target_date = pd.to_datetime(target_date)

    # Search within the given range (±max_delta days)
    for delta in range(max_delta + 1):
        # Try going backward and forward from the target date
        for sign in [-1, 1]:
            search_date = target_date + timedelta(days=sign * delta)
            nearest_data = data[data['Date'] == search_date]

            if not nearest_data.empty:
                return nearest_data.iloc[0]  # Return the first matching row

    return None  # No matching data found within the range


def simulate_optimal_trades(yearly_data, ohlc_data, start_month, start_day, end_month, end_day, optimal_results):
    optimal_trades_results = []
    for result in yearly_data:
        start_data = find_nearest_date(ohlc_data[ohlc_data['Date'].dt.year == result['Year']],
                                       f"{result['Year']}-{start_month:02d}-{start_day:02d}")
        end_data = find_nearest_date(ohlc_data[ohlc_data['Date'].dt.year == result['Year']],
                                     f"{result['Year']}-{end_month:02d}-{end_day:02d}")

        if start_data is None or end_data is None:
            continue

        open_price = pd.to_numeric(start_data['Open'], errors='coerce')
        close_price = pd.to_numeric(end_data['Close'], errors='coerce')

        max_drawdown = result['Max Drawdown (%)']
        max_gain = result['Max Gain (%)']

        if max_drawdown >= optimal_results['optimal_stop_loss']:
            percentage_change = -optimal_results['optimal_stop_loss']
            max_drawdown = percentage_change
        elif max_gain >= optimal_results['optimal_exit']:
            percentage_change = optimal_results['optimal_exit']
            max_gain = percentage_change
        else:
            percentage_change = 100 * (close_price - open_price)/open_price

        points_change = open_price * percentage_change

        optimal_trades_results.append({
            'Year': result['Year'],
            'Max Drawdown (Points)': max_drawdown * open_price,
            'Max Drawdown (%)': max_drawdown,
            'Max Gain (Points)': max_gain * open_price,
            'Max Gain (%)': max_gain,
            'Closing Points': round(points_change, 4),
            'Closing Percentage': round(percentage_change, 1)
        })

    return optimal_trades_results


def update_cumulative_chart_layout(fig, title):
    """
    Update the layout of a cumulative return chart to match the style of the distribution charts.
    Args:
        fig: The Plotly figure object.
        title: The title for the chart.
    """
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Cumulative Return (%)',
        plot_bgcolor='#1e1e1e',  # Same dark background as distribution charts
        paper_bgcolor='#1e1e1e',  # Same dark paper background
        font=dict(
            color='white',  # White text color
            family="'Press Start 2P', monospace"  # Same font as distribution charts
        ),
        legend=dict(
            orientation="h",  # Horizontal legend
            yanchor="bottom",
            y=1.02,  # Adjust position
            xanchor="right",
            x=1,
            font=dict(size=10)
        ),
        hovermode='x unified',  # Unified hover mode
        hoverlabel=dict(
            font=dict(family="'Press Start 2P', monospace"),
            bgcolor='#1e1e1e',
            bordercolor='white',
            font_color='white'
        ),
        xaxis=dict(
            showgrid=False  # Remove vertical grid lines
        ),
        yaxis=dict(
            showgrid=True,  # Keep horizontal grid lines
            zeroline=False  # Optionally remove the zero line if you don't need it
        )
    )


def create_cumulative_return_charts(start_month, start_day, end_month, end_day, direction, ohlc_data, num_years,
                                    optimal_results_15y, optimal_results_30y):
    """
    Function to create cumulative return charts for both scenarios (with and without stop-loss/optimal exit)
    over the specified number of years (15 or 30 years). It handles 15 and 30 years independently.
    """

    # Initialize two separate DataFrames for 15-year and 30-year data
    combined_data_15y = pd.DataFrame()
    combined_data_30y = pd.DataFrame()

    current_year = pd.Timestamp.now().year

    # Process 15-year and 30-year periods separately to avoid overlap
    for year_offset in range(30):  # We process 30 years total, but separate them by num_years
        year = current_year - year_offset

        # Get the nearest start and end dates for the current year
        start_data = find_nearest_date(ohlc_data[ohlc_data['Date'].dt.year == year],
                                       f"{year}-{start_month:02d}-{start_day:02d}")
        end_data = find_nearest_date(ohlc_data[ohlc_data['Date'].dt.year == year],
                                     f"{year}-{end_month:02d}-{end_day:02d}")

        if start_data is None or end_data is None:
            continue

        # Filter OHLC data for the specific date range
        yearly_data = ohlc_data[(ohlc_data['Date'] >= start_data['Date']) & (ohlc_data['Date'] <= end_data['Date'])]

        if year_offset < 15:
            # Ensure we only add to the 15-year dataset if we're processing the first 15 years
            combined_data_15y = pd.concat([combined_data_15y, yearly_data], ignore_index=True)
        if year_offset < 30:
            # Add the same data to the 30-year dataset (without overwriting)
            combined_data_30y = pd.concat([combined_data_30y, yearly_data], ignore_index=True)

    # Sort the dataframes by date to ensure proper calculations
    combined_data_15y.drop_duplicates(subset=['Date'], inplace=True)  # Remove duplicates, if any
    combined_data_30y.drop_duplicates(subset=['Date'], inplace=True)  # Remove duplicates, if any

    combined_data_15y.sort_values('Date', inplace=True)
    combined_data_30y.sort_values('Date', inplace=True)

    # Calculate daily returns for no stop-loss for both periods
    combined_data_15y['No_Stop_Returns'] = combined_data_15y['Close_Close_Pct_Change'].fillna(0)
    combined_data_30y['No_Stop_Returns'] = combined_data_30y['Close_Close_Pct_Change'].fillna(0)

    # Invert returns for short trades
    if direction == 'Short':
        combined_data_15y['No_Stop_Returns'] *= -1
        combined_data_30y['No_Stop_Returns'] *= -1

    # Initialize columns for stop-loss/optimal exit returns
    combined_data_15y['Stop_Loss_Returns'] = pd.Series(dtype=float)
    combined_data_30y['Stop_Loss_Returns'] = pd.Series(dtype=float)


    # Process each year in the 15-year data for stop-loss/exit strategy
    for year in combined_data_15y['Date'].dt.year.unique():
        yearly_data_15y = combined_data_15y[combined_data_15y['Date'].dt.year == year]

        # Apply stop-loss/exit for 15-year data slice
        stop_loss_returns_15y = calculate_stop_loss_return(yearly_data_15y, optimal_results_15y, direction)

        # Store the stop-loss/exit returns in the DataFrame
        combined_data_15y.loc[yearly_data_15y.index, 'Stop_Loss_Returns'] = stop_loss_returns_15y

    # Process each year in the 30-year data for stop-loss/exit strategy
    for year in combined_data_30y['Date'].dt.year.unique():
        yearly_data_30y = combined_data_30y[combined_data_30y['Date'].dt.year == year]

        # Apply stop-loss/exit for 30-year data slice
        stop_loss_returns_30y = calculate_stop_loss_return(yearly_data_30y, optimal_results_30y, direction)

        # Store the stop-loss/exit returns in the DataFrame
        combined_data_30y.loc[yearly_data_30y.index, 'Stop_Loss_Returns'] = stop_loss_returns_30y

        # Invert returns for short trades
    if direction == 'Short':
        combined_data_15y['Stop_Loss_Returns'] *= -1
        combined_data_30y['Stop_Loss_Returns'] *= -1

    # Calculate cumulative returns for both no stop-loss and with stop-loss/optimal exit strategies
    combined_data_15y['Cumulative_No_Stop'] = combined_data_15y['No_Stop_Returns'].cumsum()
    combined_data_15y['Cumulative_Stop_Loss'] = combined_data_15y['Stop_Loss_Returns'].cumsum()

    combined_data_30y['Cumulative_No_Stop'] = combined_data_30y['No_Stop_Returns'].cumsum()
    combined_data_30y['Cumulative_Stop_Loss'] = combined_data_30y['Stop_Loss_Returns'].cumsum()

    # Save each dataset to separate CSV files for review
    combined_data_15y.to_csv('combined_data_15y_review.csv', index=False)
    combined_data_30y.to_csv('combined_data_30y_review.csv', index=False)

    # Plotting for the 15-year data
    fig_15y = go.Figure()
    fig_15y.add_trace(
        go.Scatter(x=combined_data_15y['Date'], y=combined_data_15y['Cumulative_No_Stop'], mode='lines',
                   name='No Stop-Loss (15 Years)')
    )
    fig_15y.add_trace(
        go.Scatter(x=combined_data_15y['Date'], y=combined_data_15y['Cumulative_Stop_Loss'], mode='lines',
                   name='With Stop-Loss/Optimal Exit (15 Years)')
    )

    # Plotting for the 30-year data
    fig_30y = go.Figure()
    fig_30y.add_trace(
        go.Scatter(x=combined_data_30y['Date'], y=combined_data_30y['Cumulative_No_Stop'], mode='lines',
                   name='No Stop-Loss (30 Years)')
    )
    fig_30y.add_trace(
        go.Scatter(x=combined_data_30y['Date'], y=combined_data_30y['Cumulative_Stop_Loss'], mode='lines',
                   name='With Stop-Loss/Optimal Exit (30 Years)')
    )

    # For 15-year chart
    update_cumulative_chart_layout(fig_15y, 'Cumulative Returns Over 15 Years')

    # For 30-year chart
    update_cumulative_chart_layout(fig_30y, 'Cumulative Returns Over 30 Years')

    # Return the necessary data for plotting
    return (fig_15y, fig_30y,
            combined_data_15y['No_Stop_Returns'], combined_data_30y['No_Stop_Returns'],
            combined_data_15y['Stop_Loss_Returns'], combined_data_30y['Stop_Loss_Returns'],
            combined_data_15y['Cumulative_No_Stop'], combined_data_15y['Cumulative_Stop_Loss'],  # Cumulative returns
            combined_data_30y['Cumulative_No_Stop'], combined_data_30y['Cumulative_Stop_Loss']  # Cumulative returns
            )


def calculate_stop_loss_return(yearly_data, optimal_results, direction):
    """
    Function to calculate daily returns with stop-loss and optimal exit for a single year slice.
    Parameters:
        - yearly_data: pd.DataFrame, OHLC data for a single year.
        - optimal_results: dict, optimal stop-loss and exit values.
        - direction: 'Long' or 'Short', indicating the trade direction.
    Returns:
        - pd.Series: Daily returns with stop-loss/exit applied.
    """

    # Initialize cumulative return tracker
    stop_loss_returns = []
    stop_loss_hit = False
    take_profit_hit = False

    # Define the stop-loss and take-profit prices based on the Open of the first day
    first_open = yearly_data.iloc[0]['Open']

    if direction == 'Long':
        stop_loss_price = first_open * (1 - optimal_results['optimal_stop_loss'] / 100)
        take_profit_price = first_open * (1 + optimal_results['optimal_exit'] / 100)
    else:
        stop_loss_price = first_open * (1 + optimal_results['optimal_stop_loss'] / 100)
        take_profit_price = first_open * (1 - optimal_results['optimal_exit'] / 100)

    # Iterate over each day and calculate returns
    for i, row in yearly_data.iterrows():
        if stop_loss_hit or take_profit_hit:
            # After stop-loss or exit is hit, return 0 for all subsequent days
            stop_loss_returns.append(0)
        else:
            # Fetch the high and low prices for the day
            high_price = row['High']
            low_price = row['Low']
            open_price = row['Open']

            # Check if stop-loss or take-profit is triggered for Long trades
            if direction == 'Long':
                if low_price <= stop_loss_price:
                    # Stop-loss triggered, calculate percentage change from Open to stop-loss
                    stop_loss_return = (stop_loss_price - open_price) / open_price * 100
                    stop_loss_returns.append(stop_loss_return)
                    stop_loss_hit = True
                elif high_price >= take_profit_price:
                    # Optimal exit triggered, calculate percentage change from Open to take-profit
                    take_profit_return = (take_profit_price - open_price) / open_price * 100
                    stop_loss_returns.append(take_profit_return)
                    take_profit_hit = True
                else:
                    # Normal daily return, take from the pre-calculated pct change in OHLC table
                    stop_loss_returns.append(row['Close_Close_Pct_Change'])
            else:
                # Short trade logic: Reverse behavior for stop-loss and take-profit
                if high_price >= stop_loss_price:
                    # Stop-loss triggered for Short, calculate percentage change from Open to stop-loss
                    stop_loss_return = (open_price - stop_loss_price) / open_price * 100
                    stop_loss_returns.append(stop_loss_return)
                    stop_loss_hit = True
                elif low_price <= take_profit_price:
                    # Optimal exit triggered for Short, calculate percentage change from Open to take-profit
                    take_profit_return = (open_price - take_profit_price) / open_price * 100
                    stop_loss_returns.append(take_profit_return)
                    take_profit_hit = True
                else:
                    # Normal daily return for Short, take from the pre-calculated pct change
                    stop_loss_returns.append(row['Close_Close_Pct_Change'])

    return pd.Series(stop_loss_returns, index=yearly_data.index)



def calculate_risk_metrics(daily_returns, cumulative_returns):
    """
    Function to calculate various risk metrics including Max Drawdown using cumulative returns.
    """
    sharpe_ratio = calculate_sharpe_ratio(daily_returns)
    sortino_ratio = calculate_sortino_ratio(daily_returns)
    max_drawdown = calculate_maximum_drawdown(cumulative_returns)  # Pass cumulative returns here
    calmar_ratio = calculate_calmar_ratio(daily_returns, max_drawdown)
    volatility = calculate_volatility(daily_returns)

    return {
        'Sharpe Ratio': sharpe_ratio,
        'Sortino Ratio': sortino_ratio,
        'Max Drawdown': max_drawdown,
        'Calmar Ratio': calmar_ratio,
        'Volatility': volatility
    }


def format_risk_metrics(risk_metrics):
    return f"""
    Sharpe Ratio: {risk_metrics['Sharpe Ratio']:.2f}\n
    Sortino Ratio: {risk_metrics['Sortino Ratio']:.2f}\n
    Max Drawdown: {risk_metrics['Max Drawdown']:.2f}\n
    Calmar Ratio: {risk_metrics['Calmar Ratio']:.4f}\n
    Volatility: {risk_metrics['Volatility']:.2f}
    """


def update_risk_metrics_summary(risk_metrics, color):
    """
    Format the risk metrics with the given color.
    Args:
        risk_metrics: A dictionary containing risk metrics.
        color: The color for styling the text.
    Returns:
        A formatted HTML string with colored metrics.
    """
    return html.Div([
        html.P(f"Sharpe Ratio: {risk_metrics['Sharpe Ratio']:.2f}, "
               f"Sortino Ratio: {risk_metrics['Sortino Ratio']:.2f},"
               f" Max Drawdown: {risk_metrics['Max Drawdown']:.2f}%, "
               f"Calmar Ratio: {risk_metrics['Calmar Ratio']:.4f}, "
               f"Volatility: {risk_metrics['Volatility']:.2f}%", style={'color': color})
    ])


def compute_day_trading_stats(df):
    """
    Computes day trading statistics for a given DataFrame of OHLC data.

    Args:
        df (pd.DataFrame): DataFrame containing 'Date', 'Open', 'High', 'Low', 'Close' columns.

    Returns:
        dict: Dictionary containing the computed metrics.
    """
    # Ensure the data is sorted by date
    df = df.sort_values('Date').reset_index(drop=True)

    # Calculate daily changes
    df['Close_Change'] = df['Close'] - df['Open']

    # D UP: Days where Close > Open
    d_up = (df['Close_Change'] > 0).sum()

    # D DN: Days where Close < Open
    d_dn = (df['Close_Change'] < 0).sum()

    # Previous day's High and Low
    df['Prev_High'] = df['High'].shift(1)
    df['Prev_Low'] = df['Low'].shift(1)

    # PD-H: High >= Previous High but Low is not below or at Previous Low
    pd_h = ((df['High'] >= df['Prev_High']) & (df['Low'] > df['Prev_Low'])).sum()

    # PD-L: Low <= Previous Low but High is not above or at Previous High
    pd_l = ((df['Low'] <= df['Prev_Low']) & (df['High'] < df['Prev_High'])).sum()

    # PD-HL: Outside days (High > Prev High and Low < Prev Low)
    pd_hl = ((df['High'] > df['Prev_High']) & (df['Low'] < df['Prev_Low'])).sum()

    # PD-nHL: Inside days (High < Prev High and Low > Prev Low)
    pd_nhl = ((df['High'] < df['Prev_High']) & (df['Low'] > df['Prev_Low'])).sum()

    # Total number of trading days (excluding the first day because of shift)
    total_days = len(df) - 1  # The first day has NaN in Prev_High and Prev_Low

    # Handle division by zero
    if total_days == 0:
        total_days = 1

    # Calculate percentages
    stats = {
        'Year': df['Date'].dt.year.iloc[0],
        'Total Days': total_days,
        'D UP': d_up,
        'D UP %': round((d_up / total_days) * 100, 2),
        'D DN': d_dn,
        'D DN %': round((d_dn / total_days) * 100, 2),
        'PD-H': pd_h,
        'PD-H %': round((pd_h / total_days) * 100, 2),
        'PD-L': pd_l,
        'PD-L %': round((pd_l / total_days) * 100, 2),
        'PD-HL': pd_hl,
        'PD-HL %': round((pd_hl / total_days) * 100, 2),
        'PD-nHL': pd_nhl,
        'PD-nHL %': round((pd_nhl / total_days) * 100, 2),
    }

    return stats


def compute_day_trading_stats_for_all_years(ohlc_data, start_date, end_date):
    """
    Computes day trading statistics for each year in the OHLC data, filtered by the given date range.

    Args:
        ohlc_data (pd.DataFrame): DataFrame containing 'Date', 'Open', 'High', 'Low', 'Close' columns.
        start_date (str): Start date of the date range (from the Date-Picker).
        end_date (str): End date of the date range (from the Date-Picker).

    Returns:
        pd.DataFrame: DataFrame containing the metrics for each year within the date range.
    """
    # Ensure 'Date' is datetime and remove duplicates
    ohlc_data['Date'] = pd.to_datetime(ohlc_data['Date'])
    ohlc_data.drop_duplicates(subset=['Date'], inplace=True)  # Remove any duplicate rows based on the 'Date'

    # Filter data based on the date range from the Date-Picker
    filtered_data = ohlc_data[(ohlc_data['Date'] >= pd.to_datetime(start_date)) &
                              (ohlc_data['Date'] <= pd.to_datetime(end_date))]

    # Get list of unique years within the filtered range
    years = filtered_data['Date'].dt.year.unique()
    stats_list = []

    # Process each year separately
    for year in sorted(years):
        df_year = filtered_data[filtered_data['Date'].dt.year == year].copy()
        if len(df_year) > 1:  # Need at least two days to compute previous day's data
            stats = compute_day_trading_stats(df_year)
            stats_list.append(stats)

    # If no data was found, return an empty DataFrame
    if not stats_list:
        return pd.DataFrame()

    # Create DataFrame from the list of dictionaries
    stats_df = pd.DataFrame(stats_list)

    # Calculate total row
    total_days = stats_df['Total Days'].sum()

    total_row = {
        'Year': 'Total',
        'Total Days': total_days,
        'D UP': stats_df['D UP'].sum(),
        'D UP %': round((stats_df['D UP'].sum() / total_days) * 100, 2),
        'D DN': stats_df['D DN'].sum(),
        'D DN %': round((stats_df['D DN'].sum() / total_days) * 100, 2),
        'PD-H': stats_df['PD-H'].sum(),
        'PD-H %': round((stats_df['PD-H'].sum() / total_days) * 100, 2),
        'PD-L': stats_df['PD-L'].sum(),
        'PD-L %': round((stats_df['PD-L'].sum() / total_days) * 100, 2),
        'PD-HL': stats_df['PD-HL'].sum(),
        'PD-HL %': round((stats_df['PD-HL'].sum() / total_days) * 100, 2),
        'PD-nHL': stats_df['PD-nHL'].sum(),
        'PD-nHL %': round((stats_df['PD-nHL'].sum() / total_days) * 100, 2),
    }

    # Remove duplicates and sort the DataFrame by Year in descending order, excluding the 'Total' row
    stats_df.drop_duplicates(inplace=True)
    stats_df = stats_df[stats_df['Year'] != 'Total']  # Exclude total row during sorting
    stats_df = stats_df.sort_values(by='Year', ascending=False)

    # Add the 'Total' row back to the bottom of the DataFrame
    stats_df = pd.concat([stats_df, pd.DataFrame([total_row])], ignore_index=True)

    return stats_df



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
         Input('current-year', 'data')
         ],
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
                          col=1, opacity=0.6, secondary_y=True, hide_yaxis_ticks=True, show_legend=False, disable_hover=True)

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
                        # update_yaxis(fig, row=row_index, col=1, title='OI')


            elif subplot == 'OI Percentages':
                df = OpenInterestPercentagesFetcher.fetch_open_interest_percentages(
                    stored_market, current_year, table_suffix, report_type
                )

                if not df.empty:
                    if report_type == 'legacy':
                        # Add traces for Legacy report
                        add_trace(fig, df['Date'], df['pct_of_oi_noncomm_long_all'],
                                  f'% of OI Non-Commercials Long', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'])
                        # (name:) f'% of OI Non-Commercials Long ({table_suffix})'
                        add_trace(fig, df['Date'], df['pct_of_oi_noncomm_short_all'],
                                  f'% of OI Non-Commercials Short ', row=row_index, col=1,
                                  line_color=COLORS['noncomm_short'])
                        add_trace(fig, df['Date'], df['pct_of_oi_comm_long_all'],
                                  f'% of OI Commercials Long', row=row_index, col=1,
                                  line_color=COLORS['comm_long'])
                        add_trace(fig, df['Date'], df['pct_of_oi_comm_short_all'],
                                  f'% of OI Commercials Short', row=row_index, col=1,
                                  line_color=COLORS['comm_short'])
                        # update_yaxis(fig, row=row_index, col=1, title='% of Open Interest')

                    elif report_type == 'disaggregated':
                        # Add traces for Disaggregated report
                        add_trace(fig, df['Date'], df['pct_of_oi_m_money_long_all'],
                                  f'% of OI Managed Money Long', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'])
                        add_trace(fig, df['Date'], df['pct_of_oi_m_money_short_all'],
                                  f'% of OI Managed Money Short', row=row_index, col=1,
                                  line_color=COLORS['noncomm_short'])
                        add_trace(fig, df['Date'], df['pct_of_oi_prod_merc_long'],
                                  f'% of OI Producers/Merchants Long', row=row_index, col=1,
                                  line_color=COLORS['comm_long'])
                        add_trace(fig, df['Date'], df['pct_of_oi_prod_merc_short'],
                                  f'% of OI Producers/Merchants Short', row=row_index, col=1,
                                  line_color=COLORS['comm_short'])
                        add_trace(fig, df['Date'], df['pct_of_oi_swap_long_all'],
                                  f'% of OI Swap Dealers Long', row=row_index, col=1,
                                  line_color=COLORS['other_long'])
                        add_trace(fig, df['Date'], df['pct_of_oi_swap_short_all'],
                                  f'% of OI Swap Dealers Short', row=row_index, col=1,
                                  line_color=COLORS['other_short'])
                        # update_yaxis(fig, row=row_index, col=1, title='% of Open Interest')

                    elif report_type == 'tff':
                        # Add traces for TFF report
                        add_trace(fig, df['Date'], df['pct_of_oi_lev_money_long'],
                                  f'% of OI Managed Money Long', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'])
                        add_trace(fig, df['Date'], df['pct_of_oi_lev_money_short'],
                                  f'% of OI Managed Money Short', row=row_index, col=1,
                                  line_color=COLORS['noncomm_short'])
                        add_trace(fig, df['Date'], df['pct_of_oi_asset_mgr_long'],
                                  f'% of OI Asset Mgrs Long', row=row_index, col=1,
                                  line_color=COLORS['comm_long'])
                        add_trace(fig, df['Date'], df['pct_of_oi_asset_mgr_short'],
                                  f'% of OI Asset Mgrs Short', row=row_index, col=1,
                                  line_color=COLORS['comm_short'])
                        add_trace(fig, df['Date'], df['pct_of_oi_dealer_long_all'],
                                  f'% of OI Dealers Long', row=row_index, col=1,
                                  line_color=COLORS['other_long'])
                        add_trace(fig, df['Date'], df['pct_of_oi_dealer_short_all'],
                                  f'% of OI Dealers Short', row=row_index, col=1,
                                  line_color=COLORS['other_short'])
                        # update_yaxis(fig, row=row_index, col=1, title='% of Open Interest')

            elif subplot == 'Positions Change':
                df = PositionsChangeDataFetcher.fetch_positions_change_data(stored_market, current_year, table_suffix,
                                                                            report_type)
                if not df.empty:
                    df = df.apply(pd.to_numeric, errors='coerce')
                    df['Date'] = pd.to_datetime(df['Date'])

                    if report_type == 'legacy':

                        set_bar_width=70000000
                        add_trace(fig, df['Date'], df['pct_change_noncomm_long'],
                                  f'% Change Non-Commercials Long', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'], chart_type='bar', bar_width=set_bar_width, bar_offset=0)
                        add_trace(fig, df['Date'], df['pct_change_noncomm_short'],
                                  f'% Change Non-Commercials Short', row=row_index, col=1,
                                  line_color=COLORS['noncomm_short'], chart_type='bar', bar_width=set_bar_width, bar_offset=1*set_bar_width)
                        add_trace(fig, df['Date'], df['pct_change_comm_long'],
                                  f'% Change Commercials Long', row=row_index, col=1,
                                  line_color=COLORS['comm_long'], chart_type='bar', bar_width=set_bar_width, bar_offset=2*set_bar_width)
                        add_trace(fig, df['Date'], df['pct_change_comm_short'],
                                  f'% Change Commercials Short', row=row_index, col=1,
                                  line_color=COLORS['comm_short'], chart_type='bar', bar_width=set_bar_width, bar_offset=3*set_bar_width)
                        # update_yaxis(fig, row=row_index, col=1, title='% Change in Positions')

                    elif report_type == 'disaggregated':
                        set_bar_width = 60000000
                        add_trace(fig, df['Date'], df['pct_change_m_money_long'],
                                  f'% Change Managed Money Long', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'], chart_type='bar', bar_width=set_bar_width, bar_offset=0)
                        add_trace(fig, df['Date'], df['pct_change_m_money_short'],
                                  f'% Change Managed Money Short', row=row_index, col=1,
                                  line_color=COLORS['noncomm_short'], chart_type='bar', bar_width=set_bar_width, bar_offset=1*set_bar_width)
                        add_trace(fig, df['Date'], df['pct_change_prod_merc_long'],
                                  f'% Change Producers / Merchants Long', row=row_index, col=1,
                                  line_color=COLORS['comm_long'], chart_type='bar', bar_width=set_bar_width, bar_offset=2*set_bar_width)
                        add_trace(fig, df['Date'], df['pct_change_prod_merc_short'],
                                  f'% Change Producers / Merchants Short', row=row_index, col=1,
                                  line_color=COLORS['comm_short'], chart_type='bar', bar_width=set_bar_width, bar_offset=3*set_bar_width)
                        add_trace(fig, df['Date'], df['pct_change_swap_long'],
                                  f'% Change Swap Dealers Long', row=row_index, col=1,
                                  line_color=COLORS['other_long'], chart_type='bar', bar_width=set_bar_width, bar_offset=4*set_bar_width)
                        add_trace(fig, df['Date'], df['pct_change_swap_short'],
                                  f'% Change Swap Dealers Short', row=row_index, col=1,
                                  line_color=COLORS['other_short'], chart_type='bar', bar_width=set_bar_width, bar_offset=5*set_bar_width)
                        # update_yaxis(fig, row=row_index, col=1, title='% Change in Positions')

                    elif report_type == 'tff':
                        set_bar_width = 60000000
                        add_trace(fig, df['Date'], df['pct_change_lev_money_long'],
                                  f'% Change Managed Money Long', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'], chart_type='bar', bar_width=set_bar_width, bar_offset=0)
                        add_trace(fig, df['Date'], df['pct_change_lev_money_short'],
                                  f'% Change Managed Money Short', row=row_index, col=1,
                                  line_color=COLORS['noncomm_short'], chart_type='bar', bar_width=set_bar_width, bar_offset=1*set_bar_width)
                        add_trace(fig, df['Date'], df['pct_change_asset_mgr_long'],
                                  f'% Change Asset Mgrs Long', row=row_index, col=1,
                                  line_color=COLORS['comm_long'], chart_type='bar', bar_width=set_bar_width, bar_offset=2*set_bar_width)
                        add_trace(fig, df['Date'], df['pct_change_asset_mgr_short'],
                                  f'% Change Asset Mgrs Short', row=row_index, col=1,
                                  line_color=COLORS['comm_short'], chart_type='bar', bar_width=set_bar_width, bar_offset=3*set_bar_width)
                        add_trace(fig, df['Date'], df['pct_change_dealer_long'],
                                  f'% Change Swap Dealers Long', row=row_index, col=1,
                                  line_color=COLORS['other_long'], chart_type='bar', bar_width=set_bar_width, bar_offset=4*set_bar_width)
                        add_trace(fig, df['Date'], df['pct_change_dealer_short'],
                                  f'% Change Swap Dealers Short', row=row_index, col=1,
                                  line_color=COLORS['other_short'], chart_type='bar', bar_width=set_bar_width, bar_offset=5*set_bar_width)
                        # update_yaxis(fig, row=row_index, col=1, title='% Change in Positions')

            elif subplot == 'Net Positions':
                df = NetPositionsDataFetcher.fetch_net_positions_data(stored_market, current_year, table_suffix,
                                                                      report_type)
                if not df.empty:
                    df = df.apply(pd.to_numeric, errors='coerce')
                    df['Date'] = pd.to_datetime(df['Date'])

                    if report_type == 'legacy':
                        add_trace(fig, df['Date'], df['noncomm_net_positions'],
                                  f'Net Positions Non-Commercials', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'])
                        add_trace(fig, df['Date'], df['comm_net_positions'],
                                  f'Net Positions Commercials', row=row_index, col=1,
                                  line_color=COLORS['comm_long'])
                        # update_yaxis(fig, row=row_index, col=1, title='Net Positions')

                    elif report_type == 'disaggregated':
                        add_trace(fig, df['Date'], df['m_money_net_positions'],
                                  f'Net Positions Managed Money', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'])
                        add_trace(fig, df['Date'], df['prod_merc_net_positions'],
                                  f'Net Positions Producers / Merchants', row=row_index, col=1,
                                  line_color=COLORS['comm_long'])
                        add_trace(fig, df['Date'], df['swap_net_positions'],
                                  f'Net Positions Swap Dealers', row=row_index, col=1,
                                  line_color=COLORS['other_long'])
                        # update_yaxis(fig, row=row_index, col=1, title='Net Positions')

                    elif report_type == 'tff':
                        add_trace(fig, df['Date'], df['lev_money_net_positions'],
                                  f'Net Positions Managed Money', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'])
                        add_trace(fig, df['Date'], df['asset_mgr_net_positions'],
                                  f'Net Positions Asset Mgrs', row=row_index, col=1,
                                  line_color=COLORS['comm_long'])
                        add_trace(fig, df['Date'], df['dealer_net_positions'],
                                  f'Net Positions Dealers', row=row_index, col=1,
                                  line_color=COLORS['other_long'])
                        # update_yaxis(fig, row=row_index, col=1, title='Net Positions')

            elif subplot == 'Net Positions Change':
                df = PositionsChangeNetDataFetcher.fetch_positions_change_net_data(stored_market, current_year,
                                                                                   table_suffix, report_type)
                if not df.empty:
                    df = df.apply(pd.to_numeric, errors='coerce')
                    df['Date'] = pd.to_datetime(df['Date'])

                    if report_type == 'legacy':
                        set_bar_width = 70000000
                        add_trace(fig, df['Date'],
                                  df['pct_change_noncomm_net_positions'],
                                  f'% Change Net Positions Non-Commercials', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'], chart_type='bar', bar_width=set_bar_width, bar_offset=0*set_bar_width)
                        add_trace(fig, df['Date'],
                                  df['pct_change_comm_net_positions'],
                                  f'% Change Net Positions Commercials', row=row_index, col=1,
                                  line_color=COLORS['comm_long'], chart_type='bar', bar_width=set_bar_width, bar_offset=1*set_bar_width)
                        # update_yaxis(fig, row=row_index, col=1, title='% Change in Net Positions')

                    elif report_type == 'disaggregated':
                        set_bar_width = 60000000
                        add_trace(fig, df['Date'],
                                  df['pct_change_m_money_net_positions'],
                                  f'% Change Net Positions Managed Money', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'], chart_type='bar', bar_width=set_bar_width, bar_offset=0*set_bar_width)
                        add_trace(fig, df['Date'],
                                  df['pct_change_prod_merc_net_positions'],
                                  f'% Change Net Positions Producers / Merchants', row=row_index, col=1,
                                  line_color=COLORS['comm_long'], chart_type='bar', bar_width=set_bar_width, bar_offset=1*set_bar_width)
                        add_trace(fig, df['Date'],
                                  df['pct_change_swap_net_positions'],
                                  f'% Change Net Positions Swap Dealers', row=row_index, col=1,
                                  line_color=COLORS['other_long'], chart_type='bar', bar_width=set_bar_width, bar_offset=2*set_bar_width)
                        # update_yaxis(fig, row=row_index, col=1, title='% Change in Net Positions')

                    elif report_type == 'tff':
                        set_bar_width = 60000000
                        add_trace(fig, df['Date'],
                                  df['pct_change_lev_money_net_positions'],
                                  f'% Change Net Positions Managed Money', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'], chart_type='bar', bar_width=set_bar_width, bar_offset=0*set_bar_width)
                        add_trace(fig, df['Date'],
                                  df['pct_change_asset_mgr_net_positions'],
                                  f'% Change Net Positions Asset Mgrs', row=row_index, col=1,
                                  line_color=COLORS['comm_long'], chart_type='bar', bar_width=set_bar_width, bar_offset=1*set_bar_width)
                        add_trace(fig, df['Date'],
                                  df['pct_change_dealer_net_positions'],
                                  f'% Change Net Positions Dealers', row=row_index, col=1,
                                  line_color=COLORS['other_long'], chart_type='bar', bar_width=set_bar_width, bar_offset=2*set_bar_width)
                        # update_yaxis(fig, row=row_index, col=1, title='% Change in Net Positions')

            elif subplot == '26W Index':
                df = Index26WDataFetcher.fetch_26w_index_data(stored_market, current_year, table_suffix, report_type)
                if not df.empty:
                    df = df.apply(pd.to_numeric, errors='coerce')
                    df['Date'] = pd.to_datetime(df['Date'])

                    if report_type == 'legacy':
                        add_trace(fig, df['Date'], df['noncomm_26w_index'],
                                  f'Non-Commercials 26W Index', row=row_index, col=1, line_color=COLORS['noncomm_long'])
                        add_trace(fig, df['Date'], df['comm_26w_index'],
                                  f'Commercials 26W Index', row=row_index, col=1, line_color=COLORS['comm_long'])
                        add_shape(fig, df['Date'].min(), df['Date'].max(), 50, 50, row=row_index, col=1)
                        # update_yaxis(fig, row=row_index, col=1, title='26-Week Index')

                    elif report_type == 'disaggregated':
                        add_trace(fig, df['Date'], df['m_money_26w_index'],
                                  f'Managed Money 26W Index', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'])
                        add_trace(fig, df['Date'], df['prod_merc_26w_index'],
                                  f'Producers / Merchants 26W Index', row=row_index, col=1,
                                  line_color=COLORS['comm_long'])
                        add_trace(fig, df['Date'], df['swap_26w_index'],
                                  f'Swap Dealers 26W Index', row=row_index, col=1,
                                  line_color=COLORS['other_long'])
                        add_shape(fig, df['Date'].min(), df['Date'].max(), 50, 50, row=row_index, col=1)
                        # update_yaxis(fig, row=row_index, col=1, title='26-Week Index')

                    elif report_type == 'tff':
                        add_trace(fig, df['Date'], df['lev_money_26w_index'],
                                  f'Managed Money 26W Index', row=row_index, col=1,
                                  line_color=COLORS['noncomm_long'])
                        add_trace(fig, df['Date'], df['asset_mgr_26w_index'],
                                  f'Asset Mgrs 26W Index', row=row_index, col=1,
                                  line_color=COLORS['comm_long'])
                        add_trace(fig, df['Date'], df['dealer_26w_index'],
                                  f'Dealers 26W Index', row=row_index, col=1,
                                  line_color=COLORS['other_long'])
                        add_shape(fig, df['Date'].min(), df['Date'].max(), 50, 50, row=row_index, col=1)
                        # update_yaxis(fig, row=row_index, col=1, title='26-Week Index')

            row_index += 1

        # Hide the range slider for x-axis
        fig.update_xaxes(rangeslider=dict(visible=False), type='date', row=1, col=1)

        fig.update_layout(
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

        # fig.update_traces(hoverinfo="x+y", xaxis="x1") # If added xaxis="x1" it gives nice vertical line accross all subplots but not working for Week 26 Index

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
    def get_market_by_index(index, market_tickers):
        """
        Retrieve the market name by its index in the original order.

        Args:
            index (int): The index of the market.
            market_tickers (dict): The dictionary of market tickers.

        Returns:
            str: The market name corresponding to the given index.
        """
        markets = list(market_tickers.keys())  # Keep the original order from config.py
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
            ticker = market_tickers[new_market]  # Get the corresponding ticker for the dropdown

            return new_market, ticker  # Update both the stored-market and dropdown value

        # Default return if nothing is triggered
        return current_market, selected_market

    # Callback for Opportunity Analysis section

    def perform_analysis(market, start_month, start_day, end_month, end_day, direction, ohlc_data):
        """
        Perform analysis on OHLC data for a given market, start/end date range, and direction (Long/Short).
        """
        # Ensure 'Date' is a datetime-like object
        ohlc_data['Date'] = pd.to_datetime(ohlc_data['Date'], errors='coerce')

        # Initialize list to store analysis results for each year
        analysis_results = []

        # Get unique years from the OHLC data
        unique_years = ohlc_data['Date'].dt.year.unique()

        for year in unique_years:
            yearly_data = ohlc_data[ohlc_data['Date'].dt.year == year]

            # Get start and end dates for this year
            start_date_str = f"{year}-{start_month:02d}-{start_day:02d}"
            end_date_str = f"{year + (1 if end_month < start_month else 0)}-{end_month:02d}-{end_day:02d}"

            # Find the nearest available data for start and end dates within ±3 days
            start_data = find_nearest_date(yearly_data, start_date_str)
            end_data = find_nearest_date(yearly_data, end_date_str)

            if start_data is None or end_data is None:
                # Skip the year if no data is available within ±3 days of the start or end date
                continue

            # Use the 'Date' directly without accessing .values[0] (since 'Date' is a Timestamp)
            start_date = start_data['Date']
            end_date = end_data['Date']

            # Filter the data for this year to be within the specified date range
            filtered_yearly_data = yearly_data[(yearly_data['Date'] >= start_date) & (yearly_data['Date'] <= end_date)]

            if filtered_yearly_data.empty:
                # Skip the year if no data is available in the date range
                continue

            # Convert 'Open' and 'Close' prices to numeric to avoid errors
            open_price = pd.to_numeric(start_data['Open'], errors='coerce')
            close_price = pd.to_numeric(end_data['Close'], errors='coerce')

            if pd.isnull(open_price) or pd.isnull(close_price):
                # Skip the year if conversion failed and any value is NaN
                continue

            # Calculate points and percentage change based on direction (Long or Short)
            if direction == 'Long':
                points_change = close_price - open_price
                percentage_change = (points_change / open_price) * 100
            else:
                points_change = open_price - close_price
                percentage_change = (points_change / open_price) * 100

            # Calculate max drawdown and max gain for the filtered data range
            max_drawdown = calculate_max_drawdown(filtered_yearly_data, open_price, close_price, direction)
            max_gain = calculate_max_gain(filtered_yearly_data, open_price, close_price, direction)

            # Store yearly result with the year included
            analysis_results.append({
                'Year': year,
                'Max Drawdown (Points)': round(max_drawdown['points'], 4),
                'Max Drawdown (%)': round(max_drawdown['percentage'], 1),
                'Max Gain (Points)': round(max_gain['points'], 4),
                'Max Gain (%)': round(max_gain['percentage'], 1),
                'Closing Points': round(points_change, 4),
                'Closing Percentage': round(percentage_change, 1)
            })

        # Sort results by year in descending order
        analysis_results = sorted(analysis_results, key=lambda x: x['Year'], reverse=True)

        # Calculate summary statistics for the most recent 15 and 30 years
        summary_15y = calculate_summary_statistics(analysis_results[:15])  # First 15 items after sorting
        summary_30y = calculate_summary_statistics(analysis_results[:30])  # First 30 items after sorting

        # Now, calculate optimal stop-loss and exit based on historical data
        optimal_results = calculate_optimal_exit_and_stop_loss(analysis_results)

        # Simulate trades with optimal S/L and exit
        optimal_trades_results = []
        for result in analysis_results:
            # Get the 'Open' and 'Close' prices from the original data
            start_data = find_nearest_date(ohlc_data[ohlc_data['Date'].dt.year == result['Year']],
                                           f"{result['Year']}-{start_month:02d}-{start_day:02d}")
            end_data = find_nearest_date(ohlc_data[ohlc_data['Date'].dt.year == result['Year']],
                                         f"{result['Year']}-{end_month:02d}-{end_day:02d}")

            if start_data is None or end_data is None:
                continue

            open_price = pd.to_numeric(start_data['Open'], errors='coerce')
            close_price = pd.to_numeric(end_data['Close'], errors='coerce')

            # Apply stop loss and exit strategy based on optimal calculations
            max_drawdown = result['Max Drawdown (%)']
            max_gain = result['Max Gain (%)']

            if max_drawdown >= optimal_results['optimal_stop_loss']:
                # If the stop loss is hit
                points_change = -optimal_results['optimal_stop_loss'] * open_price / 100
            elif max_gain >= optimal_results['optimal_exit']:
                # If the exit is hit
                points_change = optimal_results['optimal_exit'] * open_price / 100
            else:
                # If neither is hit, use the normal closing points
                points_change = close_price - open_price

            percentage_change = (points_change / open_price) * 100

            # Append the results in the same structure
            optimal_trades_results.append({
                'Year': result['Year'],
                'Max Drawdown (Points)': result['Max Drawdown (Points)'],
                'Max Drawdown (%)': result['Max Drawdown (%)'],
                'Max Gain (Points)': result['Max Gain (Points)'],
                'Max Gain (%)': result['Max Gain (%)'],
                'Closing Points': round(points_change, 4),
                'Closing Percentage': round(percentage_change, 1)
            })

        # Return optimal trades results along with the other data
        return {
            'yearly_results': analysis_results,
            'optimal_trades_results': optimal_trades_results,  # Add this for the optimal trade strategy
            '15_year_summary': summary_15y,
            '30_year_summary': summary_30y
        }

    def calculate_max_drawdown(df, open_price, close_price, direction):
        """
        Calculate the maximum drawdown in points and percentage.
        """
        if direction == 'Long':
            # Convert 'Low' column to numeric and find the minimum price
            min_price = pd.to_numeric(df['Low'], errors='coerce').min()
            drawdown_points = open_price - min_price
        else:
            # Convert 'High' column to numeric and find the maximum price
            max_price = pd.to_numeric(df['High'], errors='coerce').max()
            drawdown_points = max_price - open_price

        # Ensure open_price is numeric
        open_price = pd.to_numeric(open_price, errors='coerce')

        drawdown_percentage = (drawdown_points / open_price) * 100
        return {'points': drawdown_points, 'percentage': drawdown_percentage}

    def calculate_max_gain(df, open_price, close_price, direction):
        """
        Calculate the maximum gain in points and percentage.
        """
        if direction == 'Long':
            # Convert 'High' column to numeric and find the maximum price
            max_price = pd.to_numeric(df['High'], errors='coerce').max()
            gain_points = max_price - open_price
        else:
            # Convert 'Low' column to numeric and find the minimum price
            min_price = pd.to_numeric(df['Low'], errors='coerce').min()
            gain_points = open_price - min_price

        # Ensure open_price is numeric
        open_price = pd.to_numeric(open_price, errors='coerce')

        gain_percentage = (gain_points / open_price) * 100
        return {'points': gain_points, 'percentage': gain_percentage}

    def calculate_optimal_exit_and_stop_loss(analysis_results):
        """
        Calculate the optimal stop loss and exit based on historical max drawdowns and gains.
        Args:
            analysis_results (list): List of yearly analysis results with max drawdown and max gain values.
        Returns:
            dict: A dictionary containing the optimal stop loss, optimal exit, win rate, and points gained.
        """
        total_years = len(analysis_results)
        if total_years == 0:
            return {
                'optimal_stop_loss': 0,
                'optimal_exit': 0,
                'win_rate': 0,
                'points_gained': 0
            }

        # Determine the maximum observed drawdown and gain across all years
        max_observed_drawdown = max(result['Max Drawdown (%)'] for result in analysis_results)
        max_observed_gain = max(result['Max Gain (%)'] for result in analysis_results)

        # Stop loss and exit thresholds to test (1% through max observed drawdown/gain)
        stop_loss_thresholds = [i for i in range(1, int(max_observed_drawdown) + 1)]
        exit_thresholds = [i for i in range(1, int(max_observed_gain) + 1)]

        # Store results for each stop loss and exit combination
        best_combination = {
            'stop_loss': None,
            'exit': None,
            'win_rate': 0,
            'points_gained': float('-inf')
        }

        # Iterate over stop loss thresholds
        for stop_loss in stop_loss_thresholds:
            # Iterate over exit thresholds
            for exit_level in exit_thresholds:
                wins = 0
                total_points = 0

                # Simulate each year with the given stop loss and exit combination
                for result in analysis_results:
                    max_drawdown = result['Max Drawdown (%)']
                    max_drawdown_points = result['Max Drawdown (Points)']
                    max_gain = result['Max Gain (%)']
                    max_gain_points = result['Max Gain (Points)']
                    closing_points = result['Closing Points']

                    # Apply stop loss (percentage-based)
                    if max_drawdown >= stop_loss:
                        # Loss proportional to the stop loss in points
                        total_points += (-stop_loss / max_drawdown) * max_drawdown_points
                    elif max_gain >= exit_level:
                        # Gain proportional to the exit level in points
                        total_points += (exit_level / max_gain) * max_gain_points
                        wins += 1  # Count this as a win because the exit level was hit
                    elif closing_points > 0:
                        # Positive closing points mean a win
                        total_points += closing_points
                        wins += 1  # Count this as a win because closing points are positive
                    else:
                        # Negative closing points, take the loss
                        total_points += closing_points

                # Calculate win rate for this stop loss and exit level
                win_rate = (wins / total_years) * 100

                # If this combination yields better points, update the best combination
                if total_points > best_combination['points_gained']:
                    best_combination = {
                        'stop_loss': stop_loss,
                        'exit': exit_level,
                        'win_rate': win_rate,
                        'points_gained': total_points
                    }

        # Return the best combination of stop loss and exit
        return {
            'optimal_stop_loss': best_combination['stop_loss'],
            'optimal_exit': best_combination['exit'],
            'win_rate': best_combination['win_rate'],
            'points_gained': round(best_combination['points_gained'],4)
        }

    def calculate_summary_statistics(analysis_results):
        total_years = len(analysis_results)
        if total_years == 0:
            return {
                'win_rate': 0,
                'total_points_gained': 0,
                'total_percent_gained': 0,
                'optimal_stop_loss': 0,
                'optimal_exit': 0,
                'optimal_win_rate' : 0,
                'optimal_points_gained': 0,
            }


        # Filter wins and losses
        wins = [result for result in analysis_results if result['Closing Points'] > 0]
        losses = [result for result in analysis_results if result['Closing Points'] <= 0]

        # Calculate win rate
        win_rate = (len(wins) / total_years) * 100

        # Calculate total points and percent gained
        total_points_gained = sum(result['Closing Points'] for result in wins)
        total_percent_gained = sum(result['Closing Percentage'] for result in wins)

        # Calculate optimal stop loss and exit
        max_drawdowns = [result['Max Drawdown (Points)'] for result in analysis_results]
        max_profits = [result['Max Gain (Points)'] for result in analysis_results]

        # optimal_stop_loss = round(sum(max_drawdowns) / total_years, 4)
        # optimal_exit = round(sum(max_profits) / total_years,4)

        optimal_calculations = calculate_optimal_exit_and_stop_loss(analysis_results)

        return {
            'win_rate': win_rate,
            'total_points_gained': round(total_points_gained,4),
            'total_percent_gained': total_percent_gained,
            'optimal_stop_loss': optimal_calculations['optimal_stop_loss'],
            'optimal_exit': optimal_calculations['optimal_exit'],
            'optimal_win_rate': optimal_calculations['win_rate'],
            'optimal_points_gained': optimal_calculations['points_gained']
        }

    def create_distribution_chart(yearly_data):
        """
        Create a distribution chart for the returns over a given range of years using Plotly's default binning.

        Args:
            yearly_data (list[dict]): List of dictionaries containing yearly analysis data.

        Returns:
            go.Figure: A Plotly figure representing the distribution of returns.
        """
        # Extract the percentage changes from the yearly data
        returns = [res['Closing Percentage'] for res in yearly_data]

        # Create a histogram to show the distribution of returns
        fig = go.Figure()

        fig.add_trace(go.Histogram(
            x=returns,
            # nbinsx=20, # Let Plotly decide on the best binning based on the data, but we can specify the number of bins.
            marker_color='#4CAF50',
            opacity=0.75
        ))

        fig.update_layout(
            # title='Distribution of Returns',
            xaxis_title='Return (%)',
            yaxis_title='Frequency',
            plot_bgcolor='#1e1e1e',
            paper_bgcolor='#1e1e1e',
            font=dict(color='white', family="'Press Start 2P', monospace"),
            bargap=0.1  # Adjusts the gap between bars for better visibility
        )

        return fig

    def create_optimal_distribution_chart(optimal_trades_results):
        # Use the same approach as the existing distribution chart
        fig = go.Figure()

        fig.add_trace(go.Histogram(
            x=optimal_trades_results,
            marker_color='#FF5733',  # Use a different color for this chart
            opacity=0.75
        ))

        fig.update_layout(
            xaxis_title='Return (%)',
            yaxis_title='Frequency',
            plot_bgcolor='#1e1e1e',
            paper_bgcolor='#1e1e1e',
            font=dict(color='white', family="'Press Start 2P', monospace"),
            bargap=0.1
        )

        return fig

    @app.callback(
        [Output('yearly-analysis-table', 'data'),
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
         Output('day-trading-stats-table', 'data')],
        [Input('perform-analysis-button', 'n_clicks'),
         Input('interval-auto-load', 'n_intervals')],
        [State('date-picker-range', 'start_date'),
         State('date-picker-range', 'end_date'),
         State('direction-dropdown', 'value'),
         State('years-checklist', 'value'),
         State('stored-market', 'data')],
        prevent_initial_call=True
    )
    def perform_analysis_and_update_layout(n_clicks, n_intervals, start_date,  end_date, direction, years_range, stored_market):

        # Convert the start and end dates to month and day values for processing
        start_month, start_day = pd.to_datetime(start_date).month, pd.to_datetime(start_date).day
        end_month, end_day = pd.to_datetime(end_date).month, pd.to_datetime(end_date).day

        # Ensure that the callback is only triggered when either the button is clicked or the interval fires
        if n_clicks is None and n_intervals == 0:
            raise dash.exceptions.PreventUpdate

        if start_month is None or start_day is None or end_month is None or end_day is None:
            return [], "Please provide valid start and end dates.", "", {}, {}


        # Initialize an empty DataFrame to store all OHLC data
        ohlc_data_all_years = pd.DataFrame()

        # Get the current year
        current_year = 2024  # Or dynamically fetch current year

        # Fetch OHLC data for the given range of years
        for year_offset in years_range:
            year = current_year - year_offset
            start_date = f'{year}-{start_month:02d}-{start_day:02d}'
            end_date = f'{current_year}-{end_month:02d}-{end_day:02d}'

            print(f"Fetching OHLC data for {stored_market} from {start_date} to {end_date}")

            # Fetch OHLC data for the market within the specified range
            ohlc_data_year = OHLCDataFetcher.fetch_ohlc_data_by_range(stored_market, start_date, end_date)

            if not ohlc_data_year.empty:
                ohlc_data_all_years = pd.concat([ohlc_data_all_years, ohlc_data_year], ignore_index=True)

        # Check if any data has been fetched
        if ohlc_data_all_years.empty:
            print(f"No OHLC data found for {stored_market} in the selected date range.")
            return [], "No data available for 15-Year Summary", "No data available for 30-Year Summary", {}, {}

        print(f"Fetched OHLC data: {ohlc_data_all_years.head()}")

        # Perform analysis on the fetched OHLC data (Unoptimized results)
        analysis_results = perform_analysis(stored_market, start_month, start_day, end_month, end_day, direction,
                                            ohlc_data_all_years)

        # Prepare data for the yearly analysis table (Unoptimized)
        yearly_data = analysis_results['yearly_results']

        # Calculate optimal stop-loss and exit for 15 and 30 years
        optimal_results_15y = calculate_optimal_exit_and_stop_loss(yearly_data[:15])

        optimal_results_30y = calculate_optimal_exit_and_stop_loss(yearly_data[:30])

        # Simulate trades with optimal S/L and exit for 15 years (Optimized)
        optimal_trades_results_15y = simulate_optimal_trades(yearly_data[:15], ohlc_data_all_years, start_month,
                                                             start_day, end_month, end_day, optimal_results_15y)

        # Simulate trades with optimal S/L and exit for 30 years (Optimized)
        optimal_trades_results_30y = simulate_optimal_trades(yearly_data[:30], ohlc_data_all_years, start_month,
                                                             start_day, end_month, end_day, optimal_results_30y)

        # Prepare summaries for 15 years and 30 years
        summary_15 = calculate_summary_statistics(yearly_data[:15])
        summary_30 = calculate_summary_statistics(yearly_data[:30])

        # Calculate optimal stop-loss and exit for 15 and 30 years
        optimal_results_15y = calculate_optimal_exit_and_stop_loss(yearly_data[:15])
        optimal_results_30y = calculate_optimal_exit_and_stop_loss(yearly_data[:30])

        # Simulate trades with optimal S/L and exit for 15 and 30 years
        optimal_trades_results_15y = simulate_optimal_trades(yearly_data[:15], ohlc_data_all_years, start_month,
                                                             start_day, end_month, end_day, optimal_results_15y)
        optimal_trades_results_30y = simulate_optimal_trades(yearly_data[:30], ohlc_data_all_years, start_month,
                                                             start_day, end_month, end_day, optimal_results_30y)

        # Distribution Charts for 15 and 30 years
        distribution_chart_15 = create_distribution_chart(yearly_data[:15])
        optimal_distribution_chart_15 = create_distribution_chart(optimal_trades_results_15y)
        distribution_chart_30 = create_distribution_chart(yearly_data[:30])
        optimal_distribution_chart_30 = create_distribution_chart(optimal_trades_results_30y)

        # Cumulative return charts for 15 and 30 years
        fig_15y, fig_30y, daily_returns_15, daily_returns_30, daily_returns_15_stoploss, daily_returns_30_stoploss, cum_returns_no_stop_15, cum_returns_stop_15, cum_returns_no_stop_30, cum_returns_stop_30 = create_cumulative_return_charts(
            start_month, start_day, end_month, end_day, direction, ohlc_data_all_years, 15, optimal_results_15y,
            optimal_results_30y
        )

        # Calculate risk metrics using cumulative returns for max drawdown
        risk_metrics_15 = calculate_risk_metrics(daily_returns_15, cum_returns_no_stop_15)
        risk_metrics_30 = calculate_risk_metrics(daily_returns_30, cum_returns_no_stop_30)

        stop_loss_metrics_15 = calculate_risk_metrics(daily_returns_15_stoploss, cum_returns_stop_15)
        stop_loss_metrics_30 = calculate_risk_metrics(daily_returns_30_stoploss, cum_returns_stop_30)

        # After calculating the risk metrics and cumulative charts:
        stop_loss_color = '#ff7e67'  # Use the color of the line in your cumulative chart
        no_stop_loss_color = '#347474'  # Color for the other line

        # Pass these colors into the risk metrics summary
        risk_metrics_summary_15 = update_risk_metrics_summary(risk_metrics_15, no_stop_loss_color)
        risk_metrics_summary_30 = update_risk_metrics_summary(risk_metrics_30, no_stop_loss_color)

        stop_loss_metrics_summary_15 = update_risk_metrics_summary(stop_loss_metrics_15, stop_loss_color)
        stop_loss_metrics_summary_30 = update_risk_metrics_summary(stop_loss_metrics_30, stop_loss_color)

        # Compute day trading stats
        # ohlc_data_all_years.to_csv('ohlcDataAllYears.csv', index=False)
        stats_df = compute_day_trading_stats_for_all_years(ohlc_data_all_years, start_date, end_date)

        # Separate the 'Total' row and the numeric years for sorting
        total_row = stats_df[stats_df['Year'] == 'Total']
        stats_df = stats_df[stats_df['Year'] != 'Total']

        # Ensure the 'Year' column is integer type for sorting
        stats_df['Year'] = stats_df['Year'].astype(int)

        # Sort the data in descending order by 'Year'
        stats_df.drop_duplicates(subset=['Year'], inplace=True)
        stats_df.sort_values(by='Year', ascending=False, inplace=True)

        # Add the 'Total' row back to the end of the DataFrame
        stats_df = pd.concat([stats_df, total_row], ignore_index=True)

        # Convert the DataFrame to a dictionary for Dash DataTable
        day_trading_stats = stats_df.to_dict('records')

        # Return both unoptimized and optimized results, summaries, and charts
        return (
            yearly_data,  # Unoptimized data for the yearly analysis table
            f"15-Year Summary: Win Rate: {summary_15['win_rate']:.2f}%, Points Gained: {summary_15['total_points_gained']}, "
            f"Optimal S/L: {summary_15['optimal_stop_loss']:.2f}%, Optimal Exit: {summary_15['optimal_exit']:.2f}%, "
            f"Optimal Win Rate: {summary_15['optimal_win_rate']:.2f}%, Optimal Points Gained: {summary_15['optimal_points_gained']}",
            f"30-Year Summary: Win Rate: {summary_30['win_rate']:.2f}%, Points Gained: {summary_30['total_points_gained']}, "
            f"Optimal S/L: {summary_30['optimal_stop_loss']:.2f}%, Optimal Exit: {summary_30['optimal_exit']:.2f}%, "
            f"Optimal Win Rate: {summary_30['optimal_win_rate']:.2f}%, Optimal Points Gained: {summary_30['optimal_points_gained']}",
            distribution_chart_15,  # Unoptimized distribution chart for 15 years
            optimal_distribution_chart_15,  # Optimized distribution chart for 15 years
            distribution_chart_30,  # Unoptimized distribution chart for 30 years
            optimal_distribution_chart_30,  # Optimized distribution chart for 30 years
            fig_15y,
            fig_30y,
            risk_metrics_summary_15,
            risk_metrics_summary_30,
            stop_loss_metrics_summary_15,
            stop_loss_metrics_summary_30,
            day_trading_stats,
        )
