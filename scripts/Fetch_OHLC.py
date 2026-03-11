# Fetch_OHLC.py

import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from config import market_tickers, db_path_str  # Import the market_tickers dictionary
import os
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.sql import text

# Database URL from environment variable or config
db_path = os.environ.get(db_path_str)
if db_path.startswith("postgres://"):
    db_path = db_path.replace("postgres://", "postgresql+psycopg2://", 1)

def calculate_day_type_1(df):
    """
    Calculate the primary day type for each row in the DataFrame.

    Args:
        df (pd.DataFrame): The OHLC data with necessary columns.

    Returns:
        pd.Series: A series indicating the day type for each row.
    """
    conditions = [
        (df['high'] >= df['high'].shift(1)) & (df['low'] > df['low'].shift(1)),  # PD-H
        (df['low'] <= df['low'].shift(1)) & (df['high'] < df['high'].shift(1)),  # PD-L
        (df['high'] >= df['high'].shift(1)) & (df['low'] <= df['low'].shift(1)),  # PD-HL
        (df['high'] < df['high'].shift(1)) & (df['low'] > df['low'].shift(1))  # PD-nHL
    ]
    choices = ['PD-H', 'PD-L', 'PD-HL', 'PD-nHL']
    return np.select(conditions, choices, default='None')


def calculate_day_type_2(df):
    """
    Calculate the secondary day type for each row in the DataFrame.

    Args:
        df (pd.DataFrame): The OHLC data with necessary columns.

    Returns:
        pd.Series: A series indicating the day type for each row.
    """
    conditions = [
        (df['high'] >= df['high'].shift(1)) & (df['low'] > df['low'].shift(1)) & (df['close'] > df['high'].shift(1)),
        # CaPD-H
        (df['low'] <= df['low'].shift(1)) & (df['high'] < df['high'].shift(1)) & (df['close'] < df['low'].shift(1)),
        # CbPD-L
        (df['high'] >= df['high'].shift(1)) & (df['low'] <= df['low'].shift(1)) & (df['close'] > df['high'].shift(1)),
        # CaPD-HL
        (df['low'] <= df['low'].shift(1)) & (df['high'] >= df['high'].shift(1)) & (df['close'] < df['low'].shift(1)),
        # CbPD-HL
        (df['low'] > df['high'].shift(2)),  # BISI
        (df['high'] < df['low'].shift(2))  # SIBI
    ]
    choices = ['CaPD-H', 'CbPD-L', 'CaPD-HL', 'CbPD-HL', 'BISI', 'SIBI']
    return np.select(conditions, choices, default='None')


def clean_numerical_values(df, columns):
    """
    Remove commas and convert columns to numeric types.
    """
    df_cleaned = df.copy()  # Create a copy of the DataFrame to avoid setting with copy warnings
    for column in columns:
        # Remove commas and convert to float
        df_cleaned[column] = df_cleaned[column].astype(str).str.replace(',', '').astype(float)
    return df_cleaned


def calculate_percentage_changes(df):
    """
    Calculate percentage changes for Close-Close, Open-Close, Open-High, Open-Low, Close-High, Close-Low.
    """

    df['close_close_pct_change'] = ((df['close']-df['close'].shift(1)) / df['close'].shift(1)) * 100
    df['open_close_pct_change'] = ((df['close'] - df['open']) / df['open']) * 100
    df['open_high_pct_change'] = ((df['high'] - df['open']) / df['open']) * 100
    df['open_low_pct_change'] = ((df['low'] - df['open']) / df['open']) * 100
    df['close_high_pct_change'] = ((df['high'] - df['close']) / df['close']) * 100
    df['close_low_pct_change'] = ((df['low'] - df['close']) / df['close']) * 100

    # New calculations for PDL_Low_Pct_Change and PDH_High_Pct_Change
    df['pdl_low_pct_change'] = ((df['low'] - df['low'].shift(1)) / df['low'].shift(1)) * 100
    df['pdh_high_pct_change'] = ((df['high'] - df['high'].shift(1)) / df['high'].shift(1)) * 100

    # Round the percentage change columns to 2 decimal places
    # df = df.round(2)

    return df


def fetch_ohlc_for_2024(ticker, market_name, engine):
    """
    Fetch OHLC data for the year 2024 and append new entries to the database.

    Args:
        ticker (str): Ticker symbol of the market.
        market_name (str): Name of the market.
        engine (postgresql.Connection): Database connection.
    """
    # Define the table name
    table_name = market_name.lower().replace(' ', '_') + '_ohlc'

    # Query the latest date in the database
    query = f"SELECT MAX(date) FROM {table_name}"
    with engine.connect() as connection:
        result = connection.execute(text(query)).fetchone()
    last_date = result[0]

    # Determine the start date for fetching new data
    if last_date:
        start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        start_date = (datetime.now() - timedelta(days=365 * 35)).strftime('%Y-%m-%d')

    # Define the end date as yesterday
    end_date = (datetime.now()).strftime('%Y-%m-%d')

    # If start_date is after end_date, no need to fetch
    if datetime.strptime(start_date, '%Y-%m-%d') > datetime.strptime(end_date, '%Y-%m-%d'):
        print(f"No new data to fetch for {market_name}.")
        return

    # Fetch OHLC data from yfinance
    data = yf.download(ticker, start=start_date, end=end_date, interval="1d")

    if data.empty:
        print(f"No new data fetched for {market_name}.")
        return

    # Reset the index to get the Date column
    data.reset_index(inplace=True)

    # Flatten MultiIndex columns if present
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0] for col in data.columns]

    # Rename columns to match the desired format
    data.rename(columns={'Date': 'date', 'Close': 'close', 'Open': 'open', 'High': 'high', 'Low': 'low'}, inplace=True)

    # Ensure the correct column order
    data = data[['date', 'close', 'open', 'high', 'low']]

    # Sort data by date
    data.sort_values('date', inplace=True)

    # Calculate percentage changes
    data = calculate_percentage_changes(data)

    # Calculate day types and weekday
    data['day_type_1'] = calculate_day_type_1(data)
    data['day_type_2'] = calculate_day_type_2(data)
    data['weekday'] = data['date'].dt.day_name()

    # Don't insert first row - it's only used for calculations when .shift(1) needed
    data_to_insert = data.iloc[1:]

    # Create SQLAlchemy engine and insert data
    data_to_insert.to_sql(table_name, engine, if_exists='append', index=False)
    print(f"New data for {market_name} appended to the database.")


def remove_outliers(df, col, threshold=3):
    """
    Remove outliers based on standard deviation.
    """
    mean = df[col].mean()
    std = df[col].std()
    df = df[(df[col] >= mean - threshold * std) & (df[col] <= mean + threshold * std)]
    return df


def compute_and_store_seasonality(market_name, engine):
    table_name = market_name.lower().replace(' ', '_') + '_ohlc'

    # Define the table names for storing seasonal patterns
    for years in [15, 35]:
        seasonality_table_name = f"{table_name}_seasonality_{years}_years"

        # Compute the seasonal patterns
        end_date = datetime.now()
        start_date = end_date - pd.DateOffset(years=years)

        query = f"""
        SELECT * FROM {table_name}
        WHERE date BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}'
        ORDER BY date ASC
        """

        df = pd.read_sql(query, engine)
        df['date'] = pd.to_datetime(df['date'])

        # Ensure numerical columns are in the correct forma
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df['open'] = pd.to_numeric(df['open'], errors='coerce')
        df['high'] = pd.to_numeric(df['high'], errors='coerce')
        df['low'] = pd.to_numeric(df['low'], errors='coerce')

        # Drop rows with NaN values in critical columns
        df.dropna(subset=['close'], inplace=True)

        # Sort by date to ensure correct order
        df.sort_values('date', inplace=True)

        # Calculate day of the year
        df['day_of_year'] = df['date'].dt.dayofyear

        # Calculate percentage change for seasonality
        df['pct_change'] = df['close'].pct_change() * 100

        # Round the seasonal percentage change to 2 decimal places
        df['pct_change'] = df['pct_change'].round(2)

        # Remove 3 std outliers from the calculation
        df = remove_outliers(df, 'pct_change', threshold=3)

        # Group by day of the year and calculate average percentage change
        avg_pct_change = df.groupby('day_of_year')['pct_change'].mean()

        # Ensure all days are included
        all_days = pd.DataFrame(index=np.arange(1, 368), columns=['pct_change'])  # 1 to 367, to account for leap year
        avg_pct_change = avg_pct_change.reindex(all_days.index).fillna(0)  # Fill missing days with 0

        # Calculate cumulative sum
        cum_sum = avg_pct_change.cumsum()

        # Find the max and min values of cumulative sum
        max_value = cum_sum.max()
        min_value = cum_sum.min()

        # Normalize to a 0-100 index
        indexed_cum_sum = 100 * (cum_sum - min_value) / (max_value - min_value)

        # Create the table if it doesn't exist
        with engine.connect() as conn:
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {seasonality_table_name} (
                    day_of_year INTEGER PRIMARY KEY,
                    indexed_cumulative_percent_change REAL
                )
            """))

            # Insert or replace the indexed cumulative percentage change data
            for day, value in indexed_cum_sum.items():
                conn.execute(text(f"""
                    INSERT INTO {seasonality_table_name} (day_of_year, indexed_cumulative_percent_change)
                    VALUES (:day_of_year, :indexed_cumulative_percent_change)
                    ON CONFLICT (day_of_year)
                    DO UPDATE SET indexed_cumulative_percent_change = EXCLUDED.indexed_cumulative_percent_change
                """), {"day_of_year": day, "indexed_cumulative_percent_change": value})

        print(f"Seasonality data for {market_name} for {years} years stored in the database.")


def collect_pct_changes(engine, market_tickers, days=180):
    """
    Collects close-to-close percentage changes for all markets over the last specified days.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    pct_changes = {}

    for market_name in market_tickers.keys():
        table_name = market_name.lower().replace(' ', '_') + '_ohlc'

        query = f"""
        SELECT date, close_close_pct_change FROM {table_name}
        WHERE date BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}'
        ORDER BY date ASC
        """
        df = pd.read_sql(query, engine, parse_dates=['date'])

        # Only store percentage changes, drop duplicate dates keeping last
        series = df.set_index('date')['close_close_pct_change']
        pct_changes[market_name] = series[~series.index.duplicated(keep='last')]

    # Combine all percentage changes into one DataFrame with markets as columns
    pct_changes_df = pd.DataFrame(pct_changes)
    return pct_changes_df


def compute_and_store_correlations(engine, market_tickers):
    """
    Calculate correlations between markets for 180 days and 15 years.
    """
    # Get data for 180 days and 15 years
    pct_changes_180d = collect_pct_changes(engine, market_tickers, days=180)
    pct_changes_15y = collect_pct_changes(engine, market_tickers, days=365 * 15)

    # Calculate correlations
    correlation_180d = pct_changes_180d.corr()
    correlation_15y = pct_changes_15y.corr()

    # Store in the database
    store_correlation_in_db(correlation_180d, engine, "correlation_180_days")
    store_correlation_in_db(correlation_15y, engine, "correlation_15_years")
    print("Correlation data stored successfully.")


def store_correlation_in_db(correlation_df, engine, table_name):

    with engine.connect() as conn:
        trans = conn.begin()

        try:
            # Create the correlation table if it doesn't exist
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                market_1 TEXT,
                market_2 TEXT,
                correlation REAL
            )
            """
            conn.execute(text(create_table_query))

            # Clear existing data in the table
            conn.execute(text(f"DELETE FROM {table_name}"))

            # Insert new correlation data using parameterized queries
            insert_query = text(f"""
                            INSERT INTO {table_name} (market_1, market_2, correlation)
                            VALUES (:market_1, :market_2, :correlation)
                        """)

            for market_pair, correlation in correlation_df.stack().items():
                conn.execute(
                    insert_query,
                    {"market_1": market_pair[0], "market_2": market_pair[1], "correlation": correlation}
                )

            # Commit the transaction
            trans.commit()
            print(f"Correlation data stored in table '{table_name}'.")
        except Exception as e:
            # Rollback in case of error
            trans.rollback()
            print(f"Error storing correlation data: {e}")


def main():
    # Create the database engine
    engine = create_engine(db_path)

    # Iterate over each market and fetch the data for all markets:
    for market_name, ticker in market_tickers.items():
        print(f"Fetching OHLC data for {market_name}...")
        fetch_ohlc_for_2024(ticker, market_name, engine)

        # Compute and store seasonal patterns for all
        compute_and_store_seasonality(market_name, engine)

    # For all
    compute_and_store_correlations(engine, market_tickers)

    # For one market:
    # fetch_ohlc_for_2024('ETH=F', 'Ethereum', engine)

    # For one:
    # compute_and_store_seasonality('Ethereum', engine)



if __name__ == "__main__":
    main()
