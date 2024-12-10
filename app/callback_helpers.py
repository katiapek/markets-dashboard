# callback_helpers.py

import numpy as np
import plotly.graph_objs as go
import pandas as pd
from sklearn.cluster import KMeans
from datetime import timedelta
from dash import html
from scripts.config import market_tickers, DEFAULT_MARKET, DEFAULT_YEAR
import cProfile
import pstats


def add_trace(fig, x, y, trace_name, row, col, mode='lines', line_color=None, secondary_y=False, chart_type='line',
              opacity=1, hide_yaxis_ticks=False, bar_width=None, bar_offset=None, show_legend=True,
              disable_hover=False):
    """
    Adds a trace to the figure. Handles both line and bar charts.

    Args:
        fig: The figure object.
        x: X-axis data.
        y: Y-axis data.
        trace_name: Name of the trace.
        row: Row position of the trace in the figure.
        col: Column position of the trace in the figure.
        mode: The drawing mode for line charts ('lines', 'markers', etc.).
        line_color: Color of the line or bar.
        secondary_y: Boolean to use the secondary y-axis.
        chart_type: Type of chart ('line' or 'bar').
        hide_yaxis_ticks: Boolean to indicate whether to hide the y-axis ticks for this trace.
    """
    if chart_type == 'line':
        trace = go.Scatter(x=x, y=y, mode=mode, name=trace_name, line=dict(color=line_color), showlegend=show_legend,
                           opacity=opacity, connectgaps=True, hoverinfo='skip' if disable_hover else 'x+y',
                           hovertemplate='%{y:.2f}',
                           )
    else:  # chart_type == 'bar':
        trace = go.Bar(x=x, y=y, name=trace_name, marker=dict(color=line_color), showlegend=show_legend,
                       opacity=opacity, width=bar_width, offset=bar_offset, hovertemplate='%{y:.2f}',
                       )

    fig.add_trace(trace, row=row, col=col, secondary_y=secondary_y)
    fig.update_layout(bargap=0.2)

    # If hide_yaxis_ticks is True, hide the y-axis tick labels
    if hide_yaxis_ticks:
        fig.update_yaxes(showticklabels=False, row=row, col=col, secondary_y=secondary_y)


def add_candlestick_trace(fig, x, c_open, high, low, close, c_name, row, col, secondary_y=False):
    trace = go.Candlestick(
        x=x,
        open=c_open,
        high=high,
        low=low,
        close=close,
        name=c_name,
        yaxis='y2',
        hoverinfo='x+y',
        showlegend=False,
        increasing=dict(line=dict(color="white"), fillcolor="white"),
        decreasing=dict(line=dict(color="white"), fillcolor="black")
    )
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


def add_distribution_annotation(key, std, color, direction="Vertical"):
    if direction == "Vertical":
        key.add_annotation(
            x=std,  # Position along the x-axis
            y=1,  # Position at the top of the plot area
            yref='paper',  # Use plot area for y positioning
            text=f"{round(std, 2)}",  # Annotation text
            showarrow=False,
            textangle=-45,  # Rotate text to make it vertical
            font=dict(color=color, size=9),  # Same color as the line
            xanchor="center",  # Center text horizontally on the line
            yanchor="bottom"  # Align the text at the bottom of the plot area
        )
    else:
        key.add_annotation(
            x=1,  # Position along the x-axis
            y=std,
            xref='paper',  # Use plot area for y positioning
            text=f"{round(std, 2)}",  # Annotation text
            showarrow=False,
            textangle=0,  # Rotate text to make it vertical
            font=dict(color=color, size=9),  # Same color as the line
            xanchor="center",  # Center text horizontally on the line
            yanchor="bottom"  # Align the text at the bottom of the plot area
        )

    return key


def add_percentile_lines(fig, data, title="", day_type='pdh'):
    """
    Add standard deviation lines to a given figure.

    Args:
        fig (go.Figure): The plotly figure to update.
        data (pd.Series): Data to calculate mean and standard deviation.
        title (str): Title for the figure.
        day_type (str): Type of day for analysis - 'pdh', 'pdl', or 'pdhl'.
    """

    lower_70, upper_70, lower_95, upper_95 = calculate_percentiles(data.to_frame(), str(data.name))

    if day_type == 'pdh':
        fig.add_vline(x=upper_70, line_dash="dash", line_color="CornflowerBlue")
        add_distribution_annotation(fig, upper_70, "CornflowerBlue")
        fig.add_vline(x=upper_95, line_dash="dash", line_color="Salmon")
        add_distribution_annotation(fig, upper_95, "Salmon")
    elif day_type == 'pdl':
        fig.add_vline(x=lower_70, line_dash="dash", line_color="CornflowerBlue")
        add_distribution_annotation(fig, lower_70, "CornflowerBlue")
        fig.add_vline(x=lower_95, line_dash="dash", line_color="Salmon")
        add_distribution_annotation(fig, lower_95, "Salmon")
    elif day_type == 'dup' or day_type == 'ddown':
        fig.add_vline(x=lower_70, line_dash="dash", line_color="CornflowerBlue")
        add_distribution_annotation(fig, lower_70, "CornflowerBlue")
        fig.add_vline(x=upper_70, line_dash="dash", line_color="CornflowerBlue")
        add_distribution_annotation(fig, upper_70, "CornflowerBlue")
        fig.add_vline(x=lower_95, line_dash="dash", line_color="Salmon")
        add_distribution_annotation(fig, lower_95, "Salmon")
        fig.add_vline(x=upper_95, line_dash="dash", line_color="Salmon")
        add_distribution_annotation(fig, upper_95, "Salmon")
    else:
        fig.add_vline(x=lower_70, line_dash="dash", line_color="CornflowerBlue")
        add_distribution_annotation(fig, lower_70, "CornflowerBlue")
        fig.add_vline(x=upper_70, line_dash="dash", line_color="CornflowerBlue")
        add_distribution_annotation(fig, upper_70, "CornflowerBlue")
        fig.add_vline(x=lower_95, line_dash="dash", line_color="Salmon")
        add_distribution_annotation(fig, lower_95, "Salmon")
        fig.add_vline(x=upper_95, line_dash="dash", line_color="Salmon")
        add_distribution_annotation(fig, upper_95, "Salmon")

    fig.update_layout(
        # title=title,
        xaxis_title=title,
        yaxis_title='Frequency',
        plot_bgcolor='#1e1e1e',
        paper_bgcolor='#1e1e1e',
        font=dict(color='white', family="'Press Start 2P', monospace"),
        bargap=0.1
    )


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
    cumulative_max = cumulative_returns.cummax()

    # Step 2: Calculate the drawdown as the difference between the peak and the current value
    drawdown = cumulative_returns - cumulative_max

    # Step 3: Find the maximum drawdown (i.e., the largest negative value in the drawdown series)
    max_drawdown = drawdown.min()  # This returns the most negative value, which represents the max drawdown

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


def calculate_points_change(direction, open_price, close_price):
    """
    Calculate the points and percentage change based on trade direction (Long/Short).

    Args:
        direction (str): Trade direction ('Long' or 'Short').
        open_price (float): Opening price for the period.
        close_price (float): Closing price for the period.

    Returns:
        tuple: points_change (float), percentage_change (float)
    """
    # Calculate points change and percentage change for Long/Short direction
    if direction == 'Long':
        points_change = close_price - open_price
        percentage_change = (points_change / open_price) * 100
    else:  # Short direction
        points_change = open_price - close_price
        percentage_change = (points_change / open_price) * 100

    return points_change, percentage_change


def calculate_stop_loss_return(yearly_data, optimal_results, direction):
    """
    Calculate the stop-loss return for the yearly data based on the optimal stop-loss.

    Args:
        yearly_data (pd.DataFrame): Yearly OHLC data.
        optimal_results (dict): Contains the optimal stop-loss and exit levels.
        direction (str): Long or Short.

    Returns:
        pd.Series: The returns calculated with stop-loss applied.
    """
    stop_loss_returns = []
    stop_loss_or_take_profit = False

    # Loop through each trade in yearly data
    for i, row in yearly_data.iterrows():
        if stop_loss_or_take_profit:
            stop_loss_returns.append(0)  # Append 0 for all subsequent days after trade closure
            continue

        first_open = row['Open']

        # Ensure first_open is a float
        try:
            first_open = float(first_open)
        except ValueError:
            print(f"Error: 'Open' value {first_open} is not a valid float.")
            continue

        # Calculate the stop-loss and take-profit prices
        if direction == 'Long':
            stop_loss_price = first_open * (1 - optimal_results['optimal_stop_loss'] / 100)
            take_profit_price = first_open * (1 + optimal_results['optimal_exit'] / 100)
        else:
            stop_loss_price = first_open * (1 + optimal_results['optimal_stop_loss'] / 100)
            take_profit_price = first_open * (1 - optimal_results['optimal_exit'] / 100)

        # Track the cumulative return for this trade
        daily_return = 0

        # Evaluate trade outcome based on daily price range
        # if stop_loss_or_take_profit:
        #     daily_return = 0
        if direction == 'Long':
            if row['Low'] <= stop_loss_price:  # Stop-loss hit
                daily_return = (stop_loss_price - row['Open']) / first_open * 100
            elif row['High'] >= take_profit_price:  # Take-profit hit
                daily_return = (take_profit_price - row['Open']) / first_open * 100
            else:  # Neither hit, close at the end of the day
                daily_return = (row['Close'] - row['Open']) / first_open * 100
        else:  # Short direction
            if row['High'] >= stop_loss_price:  # Stop-loss hit
                daily_return = (row['Open'] - stop_loss_price) / first_open * 100
            elif row['Low'] <= take_profit_price:  # Take-profit hit
                daily_return = (row['Open'] - take_profit_price) / first_open * 100
            else:  # Neither hit, close at the end of the day
                daily_return = (row['Open'] - row['Close']) / first_open * 100

        # Append the return for this trade
        stop_loss_returns.append(daily_return)

        # Break out of the loop for this trade if stop-loss or take-profit is hit
        if (direction == 'Long' and (row['Low'] <= stop_loss_price or row['High'] >= take_profit_price)) or \
                (direction == 'Short' and (row['High'] >= stop_loss_price or row['Low'] <= take_profit_price)):
            stop_loss_or_take_profit = True

    # Return the series of stop-loss returns
    return pd.Series(stop_loss_returns)


def calculate_risk_metrics(daily_returns, cumulative_returns):
    """
    Function to calculate various risk metrics including Max Drawdown using cumulative returns,
    and annualized expected return based on daily returns.
    """
    # Calculate core risk metrics
    sharpe_ratio = calculate_sharpe_ratio(daily_returns)
    sortino_ratio = calculate_sortino_ratio(daily_returns)
    max_drawdown = calculate_maximum_drawdown(cumulative_returns)  # Pass cumulative returns here
    calmar_ratio = calculate_calmar_ratio(daily_returns, max_drawdown)
    volatility = calculate_volatility(daily_returns)

    # Calculate the annualized expected return
    average_daily_return = daily_returns.mean()
    annualized_expected_return = average_daily_return * 252  # assuming 252 trading days in a year

    return {
        'Sharpe Ratio': sharpe_ratio,
        'Sortino Ratio': sortino_ratio,
        'Max Drawdown': max_drawdown,
        'Calmar Ratio': calmar_ratio,
        'Volatility': volatility,
        'Annualized Expected Return': annualized_expected_return
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
    total_years = len(analysis_results)
    if total_years == 0:
        return {
            'optimal_stop_loss': 0,
            'optimal_exit': 0,
            'win_rate': 0,
            'points_gained': 0
        }

    # Precompute reusable data
    max_observed_drawdown = max(result['Max Drawdown (%)'] for result in analysis_results)
    max_observed_gain = max(result['Max Gain (%)'] for result in analysis_results)

    # Optimize thresholds
    stop_loss_thresholds = np.linspace(1, max_observed_drawdown, num=50)
    exit_thresholds = np.linspace(1, max_observed_gain, num=50)

    best_combination = {'stop_loss': None, 'exit': None, 'win_rate': 0, 'points_gained': float('-inf')}

    for stop_loss in stop_loss_thresholds:
        for exit_level in exit_thresholds:
            total_points, wins = 0, 0
            for result in analysis_results:
                max_drawdown = result['Max Drawdown (%)']
                max_drawdown_points = result['Max Drawdown (Points)']
                max_gain = result['Max Gain (%)']
                max_gain_points = result['Max Gain (Points)']
                closing_points = result['Closing Points']

                if max_drawdown >= stop_loss:
                    total_points += (-stop_loss / max_drawdown) * max_drawdown_points
                elif max_gain >= exit_level:
                    total_points += (exit_level / max_gain) * max_gain_points
                    wins += 1
                else:
                    total_points += closing_points
                    if closing_points > 0:
                        wins += 1

            win_rate = (wins / total_years) * 100
            if total_points > best_combination['points_gained']:
                best_combination.update({
                    'stop_loss': stop_loss,
                    'exit': exit_level,
                    'win_rate': win_rate,
                    'points_gained': total_points
                })

    return {
        'optimal_stop_loss': best_combination['stop_loss'],
        'optimal_exit': best_combination['exit'],
        'win_rate': best_combination['win_rate'],
        'points_gained': round(best_combination['points_gained'], 4)
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
            'optimal_win_rate': 0,
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
        'total_points_gained': round(total_points_gained, 4),
        'total_percent_gained': total_percent_gained,
        'optimal_stop_loss': optimal_calculations['optimal_stop_loss'],
        'optimal_exit': optimal_calculations['optimal_exit'],
        'optimal_win_rate': optimal_calculations['win_rate'],
        'optimal_points_gained': optimal_calculations['points_gained']
    }


def compute_day_trading_stats(df):
    """
    Compute regular day trading stats and extended day trading stats for a given DataFrame,
    both overall and grouped by weekday.

    Args:
        df (pd.DataFrame): The OHLC data for the given period.

    Returns:
        tuple: A tuple containing four dictionaries:
               - Overall regular stats
               - Overall extended stats
               - Weekday regular stats
               - Weekday extended stats
    """
    total_days = len(df)

    # Overall regular stats
    stats = {
        'Total Days': total_days,
        'D UP': (df['Close'] > df['Open']).sum(),
        'D UP %': round((df['Close'] > df['Open']).sum() / total_days * 100, 2),
        'D DN': (df['Close'] < df['Open']).sum(),
        'D DN %': round((df['Close'] < df['Open']).sum() / total_days * 100, 2),
        'PD-H': (df['Day_Type_1'] == 'PD-H').sum(),
        'PD-H %': round((df['Day_Type_1'] == 'PD-H').sum() / total_days * 100, 2),
        'PD-L': (df['Day_Type_1'] == 'PD-L').sum(),
        'PD-L %': round((df['Day_Type_1'] == 'PD-L').sum() / total_days * 100, 2),
        'PD-HL': (df['Day_Type_1'] == 'PD-HL').sum(),
        'PD-HL %': round((df['Day_Type_1'] == 'PD-HL').sum() / total_days * 100, 2),
        'PD-nHL': (df['Day_Type_1'] == 'PD-nHL').sum(),
        'PD-nHL %': round((df['Day_Type_1'] == 'PD-nHL').sum() / total_days * 100, 2),
    }

    # Overall extended stats
    stats_1 = {
        'Total Days': total_days,
        'CaPD-H': (df['Day_Type_2'] == 'CaPD-H').sum(),
        'CaPD-H %': round((df['Day_Type_2'] == 'CaPD-H').sum() / total_days * 100, 2),
        'CbPD-L': (df['Day_Type_2'] == 'CbPD-L').sum(),
        'CbPD-L %': round((df['Day_Type_2'] == 'CbPD-L').sum() / total_days * 100, 2),
        'CaPD-HL': (df['Day_Type_2'] == 'CaPD-HL').sum(),
        'CaPD-HL %': round((df['Day_Type_2'] == 'CaPD-HL').sum() / total_days * 100, 2),
        'CbPD-HL': (df['Day_Type_2'] == 'CbPD-HL').sum(),
        'CbPD-HL %': round((df['Day_Type_2'] == 'CbPD-HL').sum() / total_days * 100, 2),
        'BISI': (df['Day_Type_2'] == 'BISI').sum(),
        'BISI %': round((df['Day_Type_2'] == 'BISI').sum() / total_days * 100, 2),
        'SIBI': (df['Day_Type_2'] == 'SIBI').sum(),
        'SIBI %': round((df['Day_Type_2'] == 'SIBI').sum() / total_days * 100, 2),
    }

    # Compute stats grouped by weekday
    stats_weekdays = {}
    stats_1_weekdays = {}

    for weekday, group in df.groupby('Weekday'):
        weekday_total = len(group)

        # Regular stats by weekday
        stats_weekdays[weekday] = {
            'Total Days': weekday_total,
            'D UP': (group['Close'] > group['Open']).sum(),
            'D UP %': round((group['Close'] > group['Open']).sum() / weekday_total * 100, 2),
            'D DN': (group['Close'] < group['Open']).sum(),
            'D DN %': round((group['Close'] < group['Open']).sum() / weekday_total * 100, 2),
            'PD-H': (group['Day_Type_1'] == 'PD-H').sum(),
            'PD-H %': round((group['Day_Type_1'] == 'PD-H').sum() / weekday_total * 100, 2),
            'PD-L': (group['Day_Type_1'] == 'PD-L').sum(),
            'PD-L %': round((group['Day_Type_1'] == 'PD-L').sum() / weekday_total * 100, 2),
            'PD-HL': (group['Day_Type_1'] == 'PD-HL').sum(),
            'PD-HL %': round((group['Day_Type_1'] == 'PD-HL').sum() / weekday_total * 100, 2),
            'PD-nHL': (group['Day_Type_1'] == 'PD-nHL').sum(),
            'PD-nHL %': round((group['Day_Type_1'] == 'PD-nHL').sum() / weekday_total * 100, 2),
        }

        # Extended stats by weekday
        stats_1_weekdays[weekday] = {
            'Total Days': weekday_total,
            'CaPD-H': (group['Day_Type_2'] == 'CaPD-H').sum(),
            'CaPD-H %': round((group['Day_Type_2'] == 'CaPD-H').sum() / weekday_total * 100, 2),
            'CbPD-L': (group['Day_Type_2'] == 'CbPD-L').sum(),
            'CbPD-L %': round((group['Day_Type_2'] == 'CbPD-L').sum() / weekday_total * 100, 2),
            'CaPD-HL': (group['Day_Type_2'] == 'CaPD-HL').sum(),
            'CaPD-HL %': round((group['Day_Type_2'] == 'CaPD-HL').sum() / weekday_total * 100, 2),
            'CbPD-HL': (group['Day_Type_2'] == 'CbPD-HL').sum(),
            'CbPD-HL %': round((group['Day_Type_2'] == 'CbPD-HL').sum() / weekday_total * 100, 2),
            'BISI': (group['Day_Type_2'] == 'BISI').sum(),
            'BISI %': round((group['Day_Type_2'] == 'BISI').sum() / weekday_total * 100, 2),
            'SIBI': (group['Day_Type_2'] == 'SIBI').sum(),
            'SIBI %': round((group['Day_Type_2'] == 'SIBI').sum() / weekday_total * 100, 2),
        }

    return stats, stats_1, stats_weekdays, stats_1_weekdays


def compute_day_trading_stats_for_all_years(ohlc_data, start_date, end_date, group_by='year'):
    """
    Computes day trading statistics for each year in the OHLC data, filtered by the given date range.
    Args:
        ohlc_data (pd.DataFrame): DataFrame containing 'Date', 'Open', 'High', 'Low', 'Close' columns.
        start_date (str): Start date of the date range (from the Date-Picker).
        end_date (str): End date of the date range (from the Date-Picker).
        group_by (str): Whether to group by 'year' (only grouping by year is allowed for now).

    Returns:
        tuple: Contains yearly stats DataFrames, extended stats DataFrames, weekday stats DataFrames.
    """
    # Ensure 'Date' is datetime and remove duplicates
    ohlc_data['Date'] = pd.to_datetime(ohlc_data['Date'])
    ohlc_data.drop_duplicates(subset=['Date'], inplace=True)

    # Convert the start and end dates into day-month format for filtering each year
    start_month_day = pd.to_datetime(start_date).strftime('%m-%d')
    end_month_day = pd.to_datetime(end_date).strftime('%m-%d')

    # Filter the data by the selected date range
    filtered_data = ohlc_data[
        (ohlc_data['Date'].dt.strftime('%m-%d') >= start_month_day) &
        (ohlc_data['Date'].dt.strftime('%m-%d') <= end_month_day)
        ].copy()

    # Add weekday column for grouping
    filtered_data['Weekday'] = filtered_data['Date'].dt.day_name()

    # Initialize lists to store yearly and weekday stats
    stats_list, stats_1_list, stats_weekdays_list, stats_1_weekdays_list = [], [], [], []

    # Get list of unique years within the filtered range
    years = filtered_data['Date'].dt.year.unique()

    # Process each year separately
    for year in sorted(years):
        df_year = filtered_data[filtered_data['Date'].dt.year == year].copy()
        if len(df_year) > 1:  # Need at least two days to compute previous day's data
            # Compute the yearly statistics only once
            stats, stats_1, stats_weekdays, stats_1_weekdays = compute_day_trading_stats(df_year)

            # Add 'Year' to each yearly stats dictionary
            stats['Year'] = year
            stats_1['Year'] = year
            stats_list.append(stats)
            stats_1_list.append(stats_1)

            # For each weekday, group data and assign stats from stats_weekdays and stats_1_weekdays
            for weekday in df_year['Weekday'].unique():
                weekday_data = df_year[df_year['Weekday'] == weekday]
                if len(weekday_data) > 0:
                    # Extract weekday-specific stats
                    weekday_stats = stats_weekdays.get(weekday, {}).copy()
                    weekday_stats_1 = stats_1_weekdays.get(weekday, {}).copy()

                    # Add 'Year' and 'Weekday' to the stats for proper identification
                    weekday_stats.update({'Year': year, 'Weekday': weekday})
                    weekday_stats_1.update({'Year': year, 'Weekday': weekday})
                    stats_weekdays_list.append(weekday_stats)
                    stats_1_weekdays_list.append(weekday_stats_1)

    # If no data was found, return empty DataFrames
    if not stats_list or not stats_1_list:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # Create DataFrames from the lists of dictionaries
    stats_df = pd.DataFrame(stats_list)
    stats_1_df = pd.DataFrame(stats_1_list)

    # Add a total row for yearly stats
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
    stats_df = pd.concat([stats_df, pd.DataFrame([total_row])], ignore_index=True)

    total_1_days = stats_1_df['Total Days'].sum()
    total_1_row = {
        'Year': 'Total',
        'Total Days': total_1_days,
        'CaPD-H': stats_1_df['CaPD-H'].sum(),
        'CaPD-H %': round((stats_1_df['CaPD-H'].sum() / total_1_days) * 100, 2),
        'CbPD-L': stats_1_df['CbPD-L'].sum(),
        'CbPD-L %': round((stats_1_df['CbPD-L'].sum() / total_1_days) * 100, 2),
        'CaPD-HL': stats_1_df['CaPD-HL'].sum(),
        'CaPD-HL %': round((stats_1_df['CaPD-HL'].sum() / total_1_days) * 100, 2),
        'CbPD-HL': stats_1_df['CbPD-HL'].sum(),
        'CbPD-HL %': round((stats_1_df['CbPD-HL'].sum() / total_1_days) * 100, 2),
        'BISI': stats_1_df['BISI'].sum(),
        'BISI %': round((stats_1_df['BISI'].sum() / total_1_days) * 100, 2),
        'SIBI': stats_1_df['SIBI'].sum(),
        'SIBI %': round((stats_1_df['SIBI'].sum() / total_1_days) * 100, 2),
    }
    stats_1_df = pd.concat([stats_1_df, pd.DataFrame([total_1_row])], ignore_index=True)

    # Group Weekdays stats by Weekdays
    # Convert lists of dictionaries to DataFrames
    stats_weekdays_df = pd.DataFrame(stats_weekdays_list)
    stats_1_weekdays_df = pd.DataFrame(stats_1_weekdays_list)

    # Aggregate by 'Weekday' to get a summary for each weekday across all years
    weekday_summary_df = stats_weekdays_df.groupby('Weekday').sum()
    weekday_summary_1_df = stats_1_weekdays_df.groupby('Weekday').sum()

    # Calculate percentages for each weekday summary
    for col in ['D UP', 'D DN', 'PD-H', 'PD-L', 'PD-HL', 'PD-nHL']:
        weekday_summary_df[f"{col} %"] = (weekday_summary_df[col] / weekday_summary_df['Total Days'] * 100).round(2)

    for col in ['CaPD-H', 'CbPD-L', 'CaPD-HL', 'CbPD-HL', 'BISI', 'SIBI']:
        weekday_summary_1_df[f"{col} %"] = (weekday_summary_1_df[col] / weekday_summary_1_df['Total Days'] * 100).round(
            2)

    # Reset index to have 'Weekday' as a column rather than the index
    weekday_summary_df.reset_index(inplace=True)
    weekday_summary_1_df.reset_index(inplace=True)

    # Define the correct order for weekdays
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    # Sort by the defined weekday order
    weekday_summary_df['Weekday'] = pd.Categorical(weekday_summary_df['Weekday'], categories=weekday_order,
                                                   ordered=True)
    weekday_summary_df = weekday_summary_df.dropna(subset=['Weekday'])

    weekday_summary_df.sort_values('Weekday', inplace=True)

    weekday_summary_1_df['Weekday'] = pd.Categorical(weekday_summary_1_df['Weekday'], categories=weekday_order,
                                                     ordered=True)
    weekday_summary_1_df = weekday_summary_1_df.dropna(subset=['Weekday'])
    weekday_summary_1_df.sort_values('Weekday', inplace=True)

    return stats_df, stats_1_df, weekday_summary_df, weekday_summary_1_df


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

        # CHECK
        if year == 2018:
            stop_loss_returns_15y.to_csv('stop_loss_returns.csv', index=False)

        # Ensure lengths match
        if len(stop_loss_returns_15y) == len(yearly_data_15y):
            # Align indices and store stop-loss/exit returns
            combined_data_15y.loc[yearly_data_15y.index, 'Stop_Loss_Returns'] = stop_loss_returns_15y.values
        else:
            print(
                f"Warning: Mismatch in lengths for year {year}. Yearly data length: {len(yearly_data_15y)}"
                f", Stop-loss return length: {len(stop_loss_returns_15y)}")

    # Process each year in the 30-year data for stop-loss/exit strategy
    for year in combined_data_30y['Date'].dt.year.unique():
        yearly_data_30y = combined_data_30y[combined_data_30y['Date'].dt.year == year]

        # Apply stop-loss/exit for 30-year data slice
        stop_loss_returns_30y = calculate_stop_loss_return(yearly_data_30y, optimal_results_30y, direction)

        # Ensure lengths match
        if len(stop_loss_returns_30y) == len(yearly_data_30y):
            # Align indices and store stop-loss/exit returns
            combined_data_30y.loc[yearly_data_30y.index, 'Stop_Loss_Returns'] = stop_loss_returns_30y.values
        else:
            print(
                f"Warning: Mismatch in lengths for year {year}. Yearly data length: {len(yearly_data_30y)}"
                f", Stop-loss return length: {len(stop_loss_returns_30y)}")

    # Calculate cumulative returns for both no stop-loss and with stop-loss/optimal exit strategies
    combined_data_15y['Cumulative_No_Stop'] = combined_data_15y['No_Stop_Returns'].cumsum()
    combined_data_15y['Cumulative_Stop_Loss'] = combined_data_15y['Stop_Loss_Returns'].cumsum()

    combined_data_30y['Cumulative_No_Stop'] = combined_data_30y['No_Stop_Returns'].cumsum()
    combined_data_30y['Cumulative_Stop_Loss'] = combined_data_30y['Stop_Loss_Returns'].cumsum()

    # Plotting for the 15-year data
    fig_15y = go.Figure()
    fig_15y.add_trace(
        go.Scatter(x=combined_data_15y['Date'], y=combined_data_15y['Cumulative_No_Stop'], mode='lines',
                   name='No Stop-Loss (15 Years)', line=dict(color='CornflowerBlue'))
    )
    fig_15y.add_trace(
        go.Scatter(x=combined_data_15y['Date'], y=combined_data_15y['Cumulative_Stop_Loss'], mode='lines',
                   name='With Stop-Loss/Optimal Exit (15 Years)', line=dict(color='Salmon'))
    )

    # Plotting for the 30-year data
    fig_30y = go.Figure()
    fig_30y.add_trace(
        go.Scatter(x=combined_data_30y['Date'], y=combined_data_30y['Cumulative_No_Stop'], mode='lines',
                   name='No Stop-Loss (30 Years)', line=dict(color='CornflowerBlue'))
    )
    fig_30y.add_trace(
        go.Scatter(x=combined_data_30y['Date'], y=combined_data_30y['Cumulative_Stop_Loss'], mode='lines',
                   name='With Stop-Loss/Optimal Exit (30 Years)', line=dict(color='Salmon'))
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

def create_scatter_plots(day_data, direction="Long", best_stop_loss_level=None, best_exit_level=None,
                         expected_return_stop_loss=None, expected_return_exit=None, add_distribution_annotations=True,
                         use_gl = True,
                         n_clusters=3):
    """
    Create scatter plots with clustering for better visualization.

    Args:
        day_data (pd.DataFrame): DataFrame with daily data.
        direction (str): "Long" or "Short" for the trade direction.
        best_stop_loss_level (float): Optimal stop-loss level.
        best_exit_level (float): Optimal take-profit level.
        n_clusters (int): Number of clusters for K-Means clustering.

    Returns:
        dict: Dictionary containing the two scatter plots with clustering.
    """
    # Define columns based on the direction
    if direction == "Long":
        x_col_1 = 'Open_Low_Pct_Change'
        y_col_1 = 'Open_Close_Pct_Change'
        x_col_2 = 'Open_Low_Pct_Change'
        y_col_2 = 'Open_High_Pct_Change'
        xaxis_title_1 = 'Open-Low % Change'
        xaxis_title_2 = 'Open-Low % Change'
        yaxis_title_1 = 'Open-Close % Change'
        yaxis_title_2 = 'Open-High % Change'
    else:  # Short direction
        x_col_1 = 'Open_High_Pct_Change'
        y_col_1 = 'Open_Close_Pct_Change'
        x_col_2 = 'Open_High_Pct_Change'
        y_col_2 = 'Open_Low_Pct_Change'
        xaxis_title_1 = 'Open-High % Change'
        xaxis_title_2 = 'Open-High % Change'
        yaxis_title_1 = 'Open-Close % Change'
        yaxis_title_2 = 'Open-Low % Change'

    def add_scatter_with_clustering(fig, x, y, xaxis_title, yaxis_title, title):
        # Perform K-Means clustering
        data = np.column_stack((x, y))
        # Remove rows with NaN values
        data = data[~np.isnan(data).any(axis=1)]
        # Check if there is enough data after removing NaNs
        if data.shape[0] < n_clusters:
            raise ValueError("Not enough valid data points for clustering. Please check the input data.")

        kmeans = KMeans(n_clusters=n_clusters, random_state=42).fit(data)
        labels = kmeans.labels_

        if not use_gl:
            # Add clustered points to the plot
            for cluster_id in range(n_clusters):
                cluster_points = data[labels == cluster_id]
                fig.add_trace(go.Scatter(
                    x=cluster_points[:, 0],
                    y=cluster_points[:, 1],
                    mode='markers',
                    marker=dict(size=7),
                    name=f'Cluster {cluster_id + 1}'
                ))
        else:
            fig.add_traces([
                go.Scattergl(
                    x=data[labels == cluster_id, 0],
                    y=data[labels == cluster_id, 1],
                    mode='markers',
                    marker=dict(size=7),
                    name=f'Cluster {cluster_id + 1}'
                )
                for cluster_id in range(n_clusters)
            ])

        # Add layout settings
        fig.update_layout(
            # title=title,
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title,
            plot_bgcolor='#1e1e1e',
            paper_bgcolor='#1e1e1e',
            font=dict(color='white', family="'Press Start 2P', monospace"),
            showlegend=False  # Hide the legend
        )
        return fig

    # Scatter Plot 1: Relation between Open-[Low/High] vs Open-Close
    scatter_1 = go.Figure()
    scatter_1 = add_scatter_with_clustering(
        scatter_1,
        day_data[x_col_1],
        day_data[y_col_1],
        xaxis_title_1,
        yaxis_title_1,
        f'{xaxis_title_1} vs {yaxis_title_1} (Clustering)'
    )

    # Add optimal stop-loss level as a vertical line
    if best_stop_loss_level is not None and add_distribution_annotations:
        scatter_1.add_vline(
            x=best_stop_loss_level,
            line_dash="dash",
            line_color="Salmon",
            # annotation_text=f"Stop Loss: {best_stop_loss_level:.2f}",
            # annotation_position="top left"
        )
        add_distribution_annotation(scatter_1, best_stop_loss_level, "Salmon")

        # Add optimal exit level as a horizontal line
        scatter_1.add_hline(
            y=expected_return_stop_loss,
            line_dash="dash",
            line_color="Aquamarine",
            # annotation_text=f"Exit: {expected_return:.2f}",
            # annotation_position="top right"
        )
        add_distribution_annotation(scatter_1, expected_return_stop_loss, "Aquamarine", direction="Horizontal")

    # Scatter Plot 2: Relation between Open-[Low/High] vs Open-[High/Low]
    scatter_2 = go.Figure()
    scatter_2 = add_scatter_with_clustering(
        scatter_2,
        day_data[x_col_2],
        day_data[y_col_2],
        xaxis_title_2,
        yaxis_title_2,
        f'{xaxis_title_2} vs {yaxis_title_2} (Clustering)'
    )

    # Add optimal stop-loss and exit levels as lines for Scatter Plot 2
    if best_stop_loss_level is not None and best_exit_level is not None and add_distribution_annotations:
        scatter_2.add_vline(
            x=best_stop_loss_level,
            line_dash="dash",
            line_color="Salmon",
            # annotation_text=f"Stop Loss: {best_stop_loss_level:.2f}",
            # annotation_position="top left"
        )

        add_distribution_annotation(scatter_2, best_stop_loss_level, "Salmon")

        scatter_2.add_hline(
            y=best_exit_level,
            line_dash="dash",
            line_color="CornflowerBlue",
            # annotation_text=f"Exit: {best_exit_level:.2f}",
            # annotation_position="top right"
        )
        add_distribution_annotation(scatter_2, best_exit_level, "CornflowerBlue", direction="Horizontal")

        scatter_2.add_hline(
            y=expected_return_exit,
            line_dash="dash",
            line_color="Aquamarine",
            # annotation_text=f"Exit: {optimal_close_y:.2f}",
            # annotation_position="top right"
        )
        add_distribution_annotation(scatter_2, expected_return_exit, "Aquamarine", direction="Horizontal")

    return {
        'scatter_1': scatter_2,
        'scatter_2': scatter_1
    }


def create_high_low_vs_prev_distribution(day_data, day_type="pdh"):
    """
    Create distribution plots for percentage changes relative to the previous day's high or low.

    Args:
        day_data (pd.DataFrame): The filtered dataframe containing PD-H, PD-L, or PD-HL days.
        day_type (str): Type of day for analysis - 'pdh', 'pdl', or 'pdhl'.

    Returns:
        go.Figure or tuple: Distribution figures. A single figure for `pdh` and `pdl` types,
        or a tuple of figures for `pdhl`.
    """
    if day_type == "pdh":
        high_pct_changes = day_data['PDH_High_Pct_Change'].dropna()
        fig_high = go.Figure(data=[go.Histogram(x=high_pct_changes, nbinsx=50)])
        add_percentile_lines(fig_high, high_pct_changes, title='High-Previous Day High % Change', day_type=day_type)
        return fig_high

    elif day_type == "pdl":
        low_pct_changes = day_data['PDL_Low_Pct_Change'].dropna()
        fig_low = go.Figure(data=[go.Histogram(x=low_pct_changes, nbinsx=50)])
        add_percentile_lines(fig_low, low_pct_changes, title='Low-Previous Day Low % Change', day_type=day_type)
        return fig_low

    elif day_type == "pdhl":
        high_pct_changes = day_data['PDH_High_Pct_Change'].dropna()
        fig_high = go.Figure(data=[go.Histogram(x=high_pct_changes, nbinsx=50)])
        add_percentile_lines(fig_high, high_pct_changes, title='High-Previous Day High % Change', day_type='pdh')

        low_pct_changes = day_data['PDL_Low_Pct_Change'].dropna()
        fig_low = go.Figure(data=[go.Histogram(x=low_pct_changes, nbinsx=50)])
        add_percentile_lines(fig_low, low_pct_changes, title='Low-Previous Day Low % Change', day_type='pdl')

        return fig_high, fig_low

    elif day_type == "dup" or day_type == "ddown":
        high_pct_changes = day_data['PDH_High_Pct_Change'].dropna()
        fig_high = go.Figure(data=[go.Histogram(x=high_pct_changes, nbinsx=50)])
        add_percentile_lines(fig_high, high_pct_changes, title='High-Previous Day High % Change', day_type=day_type)

        low_pct_changes = day_data['PDL_Low_Pct_Change'].dropna()
        fig_low = go.Figure(data=[go.Histogram(x=low_pct_changes, nbinsx=50)])
        add_percentile_lines(fig_low, low_pct_changes, title='Low-Previous Day Low % Change', day_type=day_type)

        return fig_high, fig_low

    else:
        high_pct_changes = day_data['PDH_High_Pct_Change'].dropna()
        fig_high = go.Figure(data=[go.Histogram(x=high_pct_changes, nbinsx=50)])
        add_percentile_lines(fig_high, high_pct_changes, title='High-Previous Day High % Change', day_type=day_type)

        low_pct_changes = day_data['PDL_Low_Pct_Change'].dropna()
        fig_low = go.Figure(data=[go.Histogram(x=low_pct_changes, nbinsx=50)])
        add_percentile_lines(fig_low, low_pct_changes, title='Low-Previous Day Low % Change', day_type=day_type)

        return fig_high, fig_low

def calculate_percentiles(day_data, column):
    """
    Calculate percentiles for a given column in the day data.

    Args:
        day_data (pd.DataFrame): The data containing daily price change metrics.
        column (str): The column for which to calculate percentiles.

    Returns:
        tuple: Lower and upper bounds for 70% and 95% ranges.
    """
    metric_data = day_data[column].dropna()
    lower_70 = metric_data.quantile(0.15)  # Lower bound for 70% range
    upper_70 = metric_data.quantile(0.85)  # Upper bound for 70% range
    lower_95 = metric_data.quantile(0.025)  # Lower bound for 95% range
    upper_95 = metric_data.quantile(0.975)  # Upper bound for 95% range

    return lower_70, upper_70, lower_95, upper_95


def create_distributions(day_data, day_type="None"):
    distributions = {}
    open_high_col = "Open_High_Pct_Change"
    open_low_col = "Open_Low_Pct_Change"
    open_close_col = "Open_Close_Pct_Change"

    # Calculate distributions for each metric
    for key, col in zip(['open_high', 'open_low', 'open_close'], [open_high_col, open_low_col, open_close_col]):
        metric_data = day_data[col].dropna()
        lower_70, upper_70, lower_95, upper_95 = calculate_percentiles(day_data, col)

        # Create histogram with percentile lines
        distributions[key] = go.Figure(data=[go.Histogram(x=metric_data, nbinsx=50)])

        if key == 'open_high':
            distributions[key].add_vline(x=upper_70, line_dash="dash", line_color="CornflowerBlue")
            add_distribution_annotation(distributions[key], upper_70, "CornflowerBlue")

            distributions[key].add_vline(x=upper_95, line_dash="dash", line_color="Salmon")
            add_distribution_annotation(distributions[key], upper_95, "Salmon")
        elif key == 'open_low':
            distributions[key].add_vline(x=lower_70, line_dash="dash", line_color="CornflowerBlue")
            add_distribution_annotation(distributions[key], lower_70, "CornflowerBlue")

            distributions[key].add_vline(x=lower_95, line_dash="dash", line_color="Salmon")
            add_distribution_annotation(distributions[key], lower_95, "Salmon")
        elif day_type == 'dup':
            distributions[key].add_vline(x=upper_70, line_dash="dash", line_color="CornflowerBlue")
            add_distribution_annotation(distributions[key], upper_70, "CornflowerBlue")

            distributions[key].add_vline(x=upper_95, line_dash="dash", line_color="Salmon")
            add_distribution_annotation(distributions[key], upper_95, "Salmon")
        elif day_type == 'ddown':
            distributions[key].add_vline(x=lower_70, line_dash="dash", line_color="CornflowerBlue")
            add_distribution_annotation(distributions[key], lower_70, "CornflowerBlue")

            distributions[key].add_vline(x=lower_95, line_dash="dash", line_color="Salmon")
            add_distribution_annotation(distributions[key], lower_95, "Salmon")
        else:
            distributions[key].add_vline(x=lower_70, line_dash="dash", line_color="CornflowerBlue")
            add_distribution_annotation(distributions[key], lower_70, "CornflowerBlue")

            distributions[key].add_vline(x=upper_70, line_dash="dash", line_color="CornflowerBlue")
            add_distribution_annotation(distributions[key], upper_70, "CornflowerBlue")

            distributions[key].add_vline(x=lower_95, line_dash="dash", line_color="Salmon")
            add_distribution_annotation(distributions[key], lower_95, "Salmon")

            distributions[key].add_vline(x=upper_95, line_dash="dash", line_color="Salmon")
            add_distribution_annotation(distributions[key], upper_95, "Salmon")

        # Update layout for styling
        distributions[key].update_layout(
            xaxis_title=f"{col.replace('_Pct_Change', '').replace('_', ' ')} % Change",
            yaxis_title='Frequency',
            plot_bgcolor='#1e1e1e',
            paper_bgcolor='#1e1e1e',
            font=dict(color='white', family="'Press Start 2P', monospace"),
            bargap=0.1
        )

    return distributions


def create_distribution_chart(yearly_data, title="Distribution of Returns"):
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
        marker=dict(color='#4CAF50'),
        opacity=0.75
    ))

    fig.update_layout(
        title=title,
        title_font_size=12,
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
        marker=dict(color='#FF5733'),  # Use a different color for this chart
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


def filter_dup_days(df):
    """
    Filters the dataframe to return only D-UP days (where today's Close is above or equal to today's Open).

    Args:
        df (pd.DataFrame): The input OHLC dataframe with percentage changes.

    Returns:
        pd.DataFrame: A dataframe filtered for D-UP days.
    """
    # Filter for D-UP days directly
    return df[df['Close'] > df['Open']].copy()


def filter_ddown_days(df):
    """
    Filters the dataframe to return only D-DOWN days (where today's Close is below today's Open).

    Args:
        df (pd.DataFrame): The input OHLC dataframe with percentage changes.

    Returns:
        pd.DataFrame: A dataframe filtered for D-DOWN days.
    """
    # Filter for D-DOWN days directly
    return df[df['Close'] < df['Open']].copy()


def filter_pdh_days(df):
    """
    Filters the dataframe to return only PD-H days based on the precomputed 'Day_Type_1' column.

    Args:
        df (pd.DataFrame): The input OHLC dataframe with precomputed 'Day_Type_1' column.

    Returns:
        pd.DataFrame: A dataframe filtered for PD-H days.
    """
    return df[df['Day_Type_1'] == 'PD-H'].copy()


def filter_pdl_days(df):
    """
    Filters the dataframe to return only PD-L days based on the precomputed 'Day_Type_1' column.

    Args:
        df (pd.DataFrame): The input OHLC dataframe with precomputed 'Day_Type_1' column.

    Returns:
        pd.DataFrame: A dataframe filtered for PD-L days.
    """
    return df[df['Day_Type_1'] == 'PD-L'].copy()


def filter_pdhl_days(df):
    """
    Filters the dataframe to return only PD-HL days based on the precomputed 'Day_Type_1' column.

    Args:
        df (pd.DataFrame): The input OHLC dataframe with precomputed 'Day_Type_1' column.

    Returns:
        pd.DataFrame: A dataframe filtered for PD-HL days.
    """
    return df[df['Day_Type_1'] == 'PD-HL'].copy()


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


def get_market_by_index(index, market_ticker):
    """
    Retrieve the market name by its index in the original order.

    Args:
        index (int): The index of the market.
        market_ticker (dict): The dictionary of market tickers.

    Returns:
        str: The market name corresponding to the given index.
    """
    markets = list(market_ticker.keys())  # Keep the original order from config.py
    if 0 <= index < len(markets):
        return markets[index]
    return DEFAULT_MARKET  # Default market if index is out of bounds


def optimize_stop_loss_open_to_close(day_data, direction="Long"):
    """
    Optimize stop-loss based on Open-Low (for Long) or Open-High (for Short) and Open-Close percentage changes.

    Args:
        day_data (pd.DataFrame): DataFrame containing day data with 'Open_Low_Pct_Change'
        and 'Open_Close_Pct_Change' (Long)
        or 'Open_High_Pct_Change' and 'Open_Close_Pct_Change' (Short).
        direction (str): Trade direction, either "Long" or "Short".

    Returns:
        tuple: Optimal stop-loss level (percentage change) and expected return.
    """
    best_stop_loss_level = None
    max_cumulative_return = -float('inf')
    best_expected_return = 0

    # Choose columns based on direction
    stop_loss_col = 'Open_Low_Pct_Change' if direction == "Long" else 'Open_High_Pct_Change'
    close_pct_col = 'Open_Close_Pct_Change'

    # Determine range for stop-loss levels
    if direction == 'Long':
        stop_loss_max = 0  # For Long, stop-loss is negative (lower than the open)
        stop_loss_min = day_data[stop_loss_col].min()
    else:
        stop_loss_max = day_data[stop_loss_col].max()  # For Short, stop-loss is positive (higher than the open)
        stop_loss_min = 0

    # Define the range for stop-loss levels
    stop_loss_range = np.linspace(stop_loss_min, stop_loss_max, 50)

    # Loop through possible stop-loss levels
    for stop_loss_level in stop_loss_range:
        if direction == "Long":
            trades_not_stopped = day_data[day_data[stop_loss_col] > stop_loss_level]
        else:
            trades_not_stopped = day_data[day_data[stop_loss_col] < stop_loss_level]

        # Calculate cumulative return for Open-Close percentage changes
        cumulative_return = trades_not_stopped[close_pct_col].sum()

        # For Short trades, invert the sign of the cumulative return
        if direction == "Short":
            cumulative_return *= -1

        # Update best stop-loss level if this level gives a higher cumulative return
        if cumulative_return > max_cumulative_return:
            max_cumulative_return = cumulative_return
            best_stop_loss_level = stop_loss_level

            # Calculate expected return for this stop-loss level
            best_expected_return = trades_not_stopped[close_pct_col].mean()

            # Handle empty DataFrame case
            if pd.isna(best_expected_return):
                best_expected_return = 0

    return best_stop_loss_level, best_expected_return


def optimize_stop_loss_and_exit(day_data, best_stop_loss_level, direction="Long"):
    """
    Optimize take-profit based on a fixed stop-loss level and Open-High (Long) or Open-Low (Short).

    Args:
        day_data (pd.DataFrame): DataFrame containing day data with 'Open_Low_Pct_Change', 'Open_High_Pct_Change',
                                 and 'Open_Close_Pct_Change'.
        best_stop_loss_level (float): Optimal stop-loss level calculated previously.
        direction (str): Trade direction, either "Long" or "Short".

    Returns:
        float: Optimal take-profit level (percentage change) that maximizes net return.
    """
    best_exit_level = None
    max_net_return = -float('inf')
    trades_with_take_profit_exit = None
    trades_with_stop_loss_exit = None
    trades_with_no_exit = None

    # Choose columns based on direction
    exit_col = 'Open_High_Pct_Change' if direction == "Long" else 'Open_Low_Pct_Change'
    stop_loss_col = 'Open_Low_Pct_Change' if direction == "Long" else 'Open_High_Pct_Change'
    close_pct_col = 'Open_Close_Pct_Change'

    if direction == 'Long':
        take_profit_max = day_data[exit_col].max()
        take_profit_min = 0
    else:
        take_profit_max = 0
        take_profit_min = day_data[exit_col].min()

    # Define range of take-profit levels
    take_profit_range = np.linspace(take_profit_min, take_profit_max, 50)  # Covers both positive and negative values

    for take_profit_level in take_profit_range:
        if direction == "Long":
            trades_with_take_profit_exit = day_data[
                (day_data[stop_loss_col] > best_stop_loss_level) &
                (day_data[exit_col] > take_profit_level)
                ]
            trades_with_no_exit = day_data[
                (day_data[stop_loss_col] > best_stop_loss_level) &
                (day_data[exit_col] < take_profit_level)
                ]
            trades_with_stop_loss_exit = day_data[
                (day_data[stop_loss_col] < best_stop_loss_level)
            ]
        else:
            trades_with_take_profit_exit = day_data[
                (day_data[stop_loss_col] < best_stop_loss_level) &
                (day_data[exit_col] < take_profit_level)
                ]
            trades_with_no_exit = day_data[
                (day_data[stop_loss_col] < best_stop_loss_level) &
                (day_data[exit_col] > take_profit_level)
                ]
            trades_with_stop_loss_exit = day_data[
                (day_data[stop_loss_col] > best_stop_loss_level)
            ]

        # Calculate net return
        net_return_take_profit_exit = len(trades_with_take_profit_exit) * take_profit_level
        net_return_stop_loss_exit = len(trades_with_stop_loss_exit) * best_stop_loss_level
        net_return_no_exit = trades_with_no_exit[close_pct_col].sum()
        if direction == 'Long':
            total_net_return = net_return_take_profit_exit + net_return_no_exit  # + net_return_stop_loss_exit
            # - I resigned from it, and decided to calculate expected return values only when I'm right.
        else:
            total_net_return = (net_return_take_profit_exit + net_return_no_exit * (-1))  # + net_return_stop_loss_exit

        # Update best exit level if it provides a higher net return
        if total_net_return > max_net_return:
            max_net_return = total_net_return
            best_exit_level = take_profit_level

    # Calculate expected return
    total_trades = len(trades_with_take_profit_exit) + len(trades_with_no_exit)  # +len(trades_with_stop_loss_exit)
    if total_trades > 0:
        expected_return = max_net_return / total_trades
    else:
        expected_return = 0  # No trades scenario

    if direction == "Short":
        expected_return = -expected_return

    return best_exit_level, expected_return


def perform_analysis(market, start_date, end_date, direction, ohlc_data):
    """
    Perform analysis on OHLC data for a given market, start/end date range, and direction (Long/Short),
    including yearly results, optimal trades, day trading stats, and PD-H analysis.
    """
    # Extract start and end months and days from the given dates
    start_month, start_day = pd.to_datetime(start_date).month, pd.to_datetime(start_date).day
    end_month, end_day = pd.to_datetime(end_date).month, pd.to_datetime(end_date).day

    # Ensure 'Date' is a datetime-like object
    ohlc_data['Date'] = pd.to_datetime(ohlc_data['Date'], errors='coerce')

    # Initialize list to store analysis results for each year
    analysis_results = []

    # Get unique years from the OHLC data
    unique_years = ohlc_data['Date'].dt.year.unique()

    # Concatenated DataFrames for D-UP, D-DOWN, PD-H, PD-L, and PD-HL day types
    dup_days_all_years = pd.DataFrame()
    ddown_days_all_years = pd.DataFrame()
    pdh_days_all_years = pd.DataFrame()
    pdl_days_all_years = pd.DataFrame()
    pdhl_days_all_years = pd.DataFrame()
    pdh_pdl_pdhl_days_all_years = pd.DataFrame()

    # Perform yearly analysis and accumulate filtered data for each day type
    for year in unique_years:
        yearly_data = ohlc_data[ohlc_data['Date'].dt.year == year]
        start_date_str = f"{year}-{start_month:02d}-{start_day:02d}"
        end_date_str = f"{year + (1 if end_month < start_month else 0)}-{end_month:02d}-{end_day:02d}"

        start_data = find_nearest_date(yearly_data, start_date_str)
        end_data = find_nearest_date(yearly_data, end_date_str)

        if start_data is None or end_data is None:
            continue

        # Filter data for this year and date range
        start_date = start_data['Date']
        end_date = end_data['Date']
        filtered_yearly_data = yearly_data[(yearly_data['Date'] >= start_date) & (yearly_data['Date'] <= end_date)]

        if filtered_yearly_data.empty:
            continue

        # Perform calculations (points change, max drawdown, etc.)
        open_price = pd.to_numeric(start_data['Open'], errors='coerce')
        close_price = pd.to_numeric(end_data['Close'], errors='coerce')
        if pd.isnull(open_price) or pd.isnull(close_price):
            continue

        points_change, percentage_change = calculate_points_change(direction, open_price, close_price)
        max_drawdown = calculate_max_drawdown(filtered_yearly_data, open_price, close_price, direction)
        max_gain = calculate_max_gain(filtered_yearly_data, open_price, close_price, direction)

        analysis_results.append({
            'Year': year,
            'Max Drawdown (Points)': round(max_drawdown['points'], 4),
            'Max Drawdown (%)': round(max_drawdown['percentage'], 1),
            'Max Gain (Points)': round(max_gain['points'], 4),
            'Max Gain (%)': round(max_gain['percentage'], 1),
            'Closing Points': round(points_change, 4),
            'Closing Percentage': round(percentage_change, 1)
        })

        # Sort analysis results by year
        analysis_results = sorted(analysis_results, key=lambda x: x['Year'], reverse=True)

        # Filter columns for dup and ddown analysis
        filtered_yearly_data_for_dup_ddown = filtered_yearly_data[['Open_Low_Pct_Change', 'Open_High_Pct_Change',
                                                                   'Open_Close_Pct_Change', 'Close', 'Open', 'Day_Type_1',
                                                                   'PDH_High_Pct_Change', 'PDL_Low_Pct_Change']]

        # Filter columns for pdh, pdl, and pdhl analysis
        filtered_yearly_data_for_pdh_pdl_pdhl = filtered_yearly_data[['Open_Low_Pct_Change', 'Open_High_Pct_Change',
                                                                      'Open_Close_Pct_Change', 'Day_Type_1',
                                                                      'PDH_High_Pct_Change', 'PDL_Low_Pct_Change']]

        # Aggregate filtered data for D-UP, D-DOWN, PD-H, PD-L, and PD-HL analysis across all years
        dup_days_all_years = pd.concat([dup_days_all_years, filter_dup_days(filtered_yearly_data_for_dup_ddown)],
                                       ignore_index=True)
        ddown_days_all_years = pd.concat([ddown_days_all_years, filter_ddown_days(filtered_yearly_data_for_dup_ddown)],
                                         ignore_index=True)
        pdh_days_all_years = pd.concat([pdh_days_all_years, filter_pdh_days(filtered_yearly_data_for_pdh_pdl_pdhl)],
                                       ignore_index=True)
        pdl_days_all_years = pd.concat([pdl_days_all_years, filter_pdl_days(filtered_yearly_data_for_pdh_pdl_pdhl)],
                                       ignore_index=True)
        pdhl_days_all_years = pd.concat([pdhl_days_all_years, filter_pdhl_days(filtered_yearly_data_for_pdh_pdl_pdhl)],
                                        ignore_index=True)

    # D-UP Analysis
    dup_best_stop_loss_level, dup_expected_return_stop_loss = (
        optimize_stop_loss_open_to_close(dup_days_all_years, direction))
    dup_best_exit_level, dup_expected_return_exit = (
        optimize_stop_loss_and_exit(dup_days_all_years, dup_best_stop_loss_level, direction))
    dup_distributions = create_distributions(dup_days_all_years, day_type='dup')
    if direction == 'Short':
        dup_scatters = create_scatter_plots(dup_days_all_years, direction,
                                            dup_best_stop_loss_level, dup_best_exit_level,
                                            dup_expected_return_stop_loss, dup_expected_return_exit,
                                            add_distribution_annotations=False)
    else:
        dup_scatters = create_scatter_plots(dup_days_all_years, direction,
                                            dup_best_stop_loss_level, dup_best_exit_level,
                                            dup_expected_return_stop_loss, dup_expected_return_exit)
    dup_high_vs_prev_high_dist, dup_low_vs_prev_low_dist = create_high_low_vs_prev_distribution(dup_days_all_years,
                                                                                                day_type='dup')

    # D-DOWN Analysis
    ddown_best_stop_loss_level, ddown_expected_return_stop_loss = optimize_stop_loss_open_to_close(ddown_days_all_years,
                                                                                                   direction)
    ddown_best_exit_level, ddown_expected_return_exit = optimize_stop_loss_and_exit(ddown_days_all_years,
                                                                                    ddown_best_stop_loss_level,
                                                                                    direction)
    ddown_distributions = create_distributions(ddown_days_all_years, day_type='ddown')
    if direction == 'Long':
        ddown_scatters = create_scatter_plots(ddown_days_all_years, direction, ddown_best_stop_loss_level,
                                              ddown_best_exit_level,
                                              ddown_expected_return_stop_loss, ddown_expected_return_exit,
                                              add_distribution_annotations=False)
    else:
        ddown_scatters = create_scatter_plots(ddown_days_all_years, direction, ddown_best_stop_loss_level,
                                              ddown_best_exit_level,
                                              ddown_expected_return_stop_loss, ddown_expected_return_exit)
    ddown_high_vs_prev_high_dist, ddown_low_vs_prev_low_dist = create_high_low_vs_prev_distribution(
        ddown_days_all_years, day_type='ddown')

    # PD-H Analysis
    pdh_best_stop_loss_level, pdh_expected_return_stop_loss = optimize_stop_loss_open_to_close(pdh_days_all_years,
                                                                                               direction)
    pdh_best_exit_level, pdh_expected_return_exit = optimize_stop_loss_and_exit(pdh_days_all_years,
                                                                                pdh_best_stop_loss_level, direction)
    pdh_distributions = create_distributions(pdh_days_all_years)
    pdh_scatters = create_scatter_plots(pdh_days_all_years, direction, pdh_best_stop_loss_level, pdh_best_exit_level,
                                        pdh_expected_return_stop_loss, pdh_expected_return_exit)
    pdh_high_vs_prev_high_dist = create_high_low_vs_prev_distribution(pdh_days_all_years, day_type='pdh')

    # PD-L Analysis
    pdl_best_stop_loss_level, pdh_expected_return_stop_loss = optimize_stop_loss_open_to_close(pdl_days_all_years,
                                                                                               direction)
    pdl_best_exit_level, pdl_expected_return_exit = optimize_stop_loss_and_exit(pdl_days_all_years,
                                                                                pdl_best_stop_loss_level, direction)
    pdl_distributions = create_distributions(pdl_days_all_years)
    pdl_scatters = create_scatter_plots(pdl_days_all_years, direction, pdl_best_stop_loss_level, pdl_best_exit_level,
                                        pdh_expected_return_stop_loss, pdl_expected_return_exit, use_gl=False)
    pdl_low_vs_prev_low_dist = create_high_low_vs_prev_distribution(pdl_days_all_years, day_type='pdl')

    # PD-HL Analysis
    pdhl_best_stop_loss_level, pdhl_expected_return_stop_loss = optimize_stop_loss_open_to_close(pdhl_days_all_years,
                                                                                                 direction)
    pdhl_best_exit_level, pdhl_expected_return_exit = optimize_stop_loss_and_exit(pdhl_days_all_years,
                                                                                  pdhl_best_stop_loss_level, direction)
    pdhl_distributions = create_distributions(pdhl_days_all_years)
    pdhl_scatters = create_scatter_plots(pdhl_days_all_years, direction, pdhl_best_stop_loss_level,
                                         pdhl_best_exit_level,
                                         pdhl_expected_return_stop_loss, pdhl_expected_return_exit, use_gl=False)
    pdhl_high_vs_prev_high_dist, pdhl_low_vs_prev_low_dist = create_high_low_vs_prev_distribution(pdhl_days_all_years,
                                                                                                  day_type='pdhl')

    # PD-H, PD-L and PD-HL day types
    pdh_pdl_pdhl_days_all_years = pd.concat([pdh_days_all_years, pdl_days_all_years, pdhl_days_all_years],
                                            ignore_index=True)

    pdh_pdl_pdhl_best_stop_loss_level, pdh_pdl_pdhl_expected_return_stop_loss = optimize_stop_loss_open_to_close(
        pdh_pdl_pdhl_days_all_years, direction)
    pdh_pdl_pdhl_best_exit_level, pdh_pdl_pdhl_expected_return_exit = optimize_stop_loss_and_exit(
        pdh_pdl_pdhl_days_all_years, pdh_pdl_pdhl_best_stop_loss_level,
        direction)
    pdh_pdl_pdhl_distributions = create_distributions(pdh_pdl_pdhl_days_all_years)
    pdh_pdl_pdhl_scatters = create_scatter_plots(pdh_pdl_pdhl_days_all_years, direction,
                                                 pdh_pdl_pdhl_best_stop_loss_level,
                                                 pdh_pdl_pdhl_best_exit_level, pdh_pdl_pdhl_expected_return_stop_loss,
                                                 pdh_pdl_pdhl_expected_return_exit)
    pdh_pdl_pdhl_high_vs_prev_high_dist, pdh_pdl_pdhl_low_vs_prev_low_dist = create_high_low_vs_prev_distribution(
        pdh_pdl_pdhl_days_all_years,
        day_type='pdh_pdl_pdhl')

    # Calculate optimal stop-loss and exit for 15 and 30 years
    optimal_results_15y = calculate_optimal_exit_and_stop_loss(analysis_results[:15])
    optimal_trades_results_15y = simulate_optimal_trades(analysis_results, ohlc_data, start_month, start_day, end_month,
                                                         end_day, optimal_results_15y, direction)

    optimal_results_30y = calculate_optimal_exit_and_stop_loss(analysis_results[:30])
    optimal_trades_results_30y = simulate_optimal_trades(analysis_results, ohlc_data, start_month, start_day, end_month,
                                                         end_day, optimal_results_30y, direction)

    # Calculate summary statistics
    summary_15 = calculate_summary_statistics(analysis_results[:15])
    summary_30 = calculate_summary_statistics(analysis_results[:30])

    # Day trading stats by year
    day_trading_stats, day_trading_stats_1, day_trading_stats_weekday, day_trading_stats_1_weekday = (
        compute_day_trading_stats_for_all_years(ohlc_data, start_date, end_date, group_by='year'))

    # Return analysis results and PD-H analysis data
    return {
        'yearly_results': analysis_results,
        'optimal_results_15y': optimal_results_15y,
        'optimal_results_30y': optimal_results_15y,
        'optimal_trades_results_15y': optimal_trades_results_15y,
        'optimal_trades_results_30y': optimal_trades_results_30y,
        '15_year_summary': summary_15,
        '30_year_summary': summary_30,
        'day_trading_stats': day_trading_stats,
        'day_trading_stats_1': day_trading_stats_1,
        'day_trading_stats_weekday': day_trading_stats_weekday,
        'day_trading_stats_1_weekday': day_trading_stats_1_weekday,
        'dup_distributions': dup_distributions,
        'dup_scatters': dup_scatters,
        'dup_low_vs_prev_low_dist': dup_low_vs_prev_low_dist,
        'dup_high_vs_prev_high_dist': dup_high_vs_prev_high_dist,
        'ddown_distributions': ddown_distributions,
        'ddown_scatters': ddown_scatters,
        'ddown_low_vs_prev_low_dist': ddown_low_vs_prev_low_dist,
        'ddown_high_vs_prev_high_dist': ddown_high_vs_prev_high_dist,
        'pdh_distributions': pdh_distributions,
        'pdh_scatters': pdh_scatters,
        'pdh_high_vs_prev_high_dist': pdh_high_vs_prev_high_dist,
        'pdl_distributions': pdl_distributions,
        'pdl_scatters': pdl_scatters,
        'pdl_low_vs_prev_low_dist': pdl_low_vs_prev_low_dist,
        'pdhl_distributions': pdhl_distributions,
        'pdhl_scatters': pdhl_scatters,
        'pdhl_low_vs_prev_low_dist': pdl_low_vs_prev_low_dist,
        'pdhl_high_vs_prev_high_dist': pdhl_high_vs_prev_high_dist,
        'pdh_pdl_pdhl_distributions': pdh_pdl_pdhl_distributions,
        'pdh_pdl_pdhl_scatters': pdh_pdl_pdhl_scatters,
        'pdh_pdl_pdhl_low_vs_prev_low_dist': pdh_pdl_pdhl_low_vs_prev_low_dist,
        'pdh_pdl_pdhl_high_vs_prev_high_dist': pdh_pdl_pdhl_high_vs_prev_high_dist,
    }


def simulate_optimal_trades(analysis_results, ohlc_data, start_month, start_day, end_month, end_day, optimal_results, direction):
    """
    Simulates trades with stop-loss and exit strategy applied, using the optimal results.
    Args:
        analysis_results (list): Yearly analysis results.
        ohlc_data (pd.DataFrame): OHLC data for the market.
        start_month, start_day, end_month, end_day (int): Date range for the analysis.
        optimal_results (dict): Optimal stop-loss and exit strategy values.
        direction (str): Direction of the trade ('Long' or 'Short').
    Returns:
        list: List of simulated trade results with stop-loss and exit applied.
    """

    # Ensure optimal stop-loss and exit are defined
    stop_loss_threshold = optimal_results.get('optimal_stop_loss')
    exit_threshold = optimal_results.get('optimal_exit')

    if stop_loss_threshold is None or exit_threshold is None:
        return []  # Return empty if thresholds are missing

    # Pre-filter the OHLC data for the relevant years
    years = [result['Year'] for result in analysis_results]
    ohlc_filtered = ohlc_data[ohlc_data['Date'].dt.year.isin(years)]

    # Precompute start and end dates for each year
    start_dates = {}
    end_dates = {}
    for year in years:
        start_date = find_nearest_date(ohlc_filtered[ohlc_filtered['Date'].dt.year == year],
                                       f"{year}-{start_month:02d}-{start_day:02d}")
        end_date = find_nearest_date(ohlc_filtered[ohlc_filtered['Date'].dt.year == year],
                                     f"{year}-{end_month:02d}-{end_day:02d}")
        if start_date is not None and end_date is not None:
            start_dates[year] = start_date
            end_dates[year] = end_date

    # Initialize list to store results
    optimal_trades_results = []

    # Iterate through the analysis results
    for result in analysis_results:
        year = result['Year']

        # Skip if start or end date is missing
        if year not in start_dates or year not in end_dates:
            continue

        start_data = start_dates[year]
        end_data = end_dates[year]

        # Get the 'Open' and 'Close' prices
        open_price = pd.to_numeric(start_data['Open'], errors='coerce')
        close_price = pd.to_numeric(end_data['Close'], errors='coerce')

        if pd.isnull(open_price) or pd.isnull(close_price):
            continue  # Skip if prices are invalid

        max_drawdown = result['Max Drawdown (%)']
        max_gain = result['Max Gain (%)']

        # Determine points change based on thresholds
        if max_drawdown >= stop_loss_threshold:
            points_change = -stop_loss_threshold * open_price / 100
        elif max_gain >= exit_threshold:
            points_change = exit_threshold * open_price / 100
        else:
            points_change = (close_price - open_price) if direction == 'Long' else (open_price - close_price)

        percentage_change = (points_change / open_price) * 100

        # Append the result
        optimal_trades_results.append({
            'Year': year,
            'Max Drawdown (Points)': result['Max Drawdown (Points)'],
            'Max Drawdown (%)': result['Max Drawdown (%)'],
            'Max Gain (Points)': result['Max Gain (Points)'],
            'Max Gain (%)': result['Max Gain (%)'],
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
               f"Volatility: {risk_metrics['Volatility']:.2f}%, "
               f"Expected Return: {risk_metrics['Annualized Expected Return']:.2f}%", style={'color': color})
    ])
