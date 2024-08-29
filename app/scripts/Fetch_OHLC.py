import yfinance as yf
from datetime import datetime, timedelta
import sqlite3
import pandas as pd
import numpy as np
from config import market_tickers  # Import the market_tickers dictionary


def clean_numerical_values(df, columns):
    """
    Remove commas and convert columns to numeric types.
    """
    df_cleaned = df.copy()  # Create a copy of the DataFrame to avoid setting with copy warnings
    for column in columns:
        # Remove commas and convert to float
        df_cleaned[column] = df_cleaned[column].astype(str).str.replace(',', '').astype(float)
    return df_cleaned



def fetch_ohlc_for_2024(ticker, market_name, conn):
    # Define the start date for 2024 and end date as yesterday
    start_date = "2024-01-01"
    end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')  # Fetch data up to yesterday

    # Fetch OHLC data from yfinance
    data = yf.download(ticker, start=start_date, end=end_date)

    if data.empty:
        print(f"No data fetched for {market_name}.")
        return

    # Reset the index to get the Date column
    data.reset_index(inplace=True)

    # Rename columns to match the desired format
    data.rename(columns={'Close': 'Close', 'Open': 'Open', 'High': 'High', 'Low': 'Low'}, inplace=True)

    # Ensure the correct column order
    data = data[['Date', 'Close', 'Open', 'High', 'Low']]

    # Clean numerical values to remove commas
    data = clean_numerical_values(data, ['Close', 'Open', 'High', 'Low'])

    # Replace existing data if Date already exists
    table_name = market_name.lower().replace(' ', '_') + '_ohlc'

    # Delete existing rows starting from the start_date
    conn.execute(f"DELETE FROM {table_name} WHERE Date >= ?", (start_date,))

    # Insert the new data into the corresponding table in the SQLite database
    data.to_sql(table_name, conn, if_exists='append', index=False)
    print(f"Data for {market_name} inserted into the database.")


def compute_and_store_seasonality(market_name, conn):
    table_name = market_name.lower().replace(' ', '_') + '_ohlc'

    # Define the table names for storing seasonal patterns
    for years in [15, 35]:
        seasonality_table_name = f"{table_name}_seasonality_{years}_years"

        # Compute the seasonal patterns
        end_date = datetime.now()
        start_date = end_date - pd.DateOffset(years=years)

        query = f"""
        SELECT * FROM {table_name}
        WHERE Date BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}'
        ORDER BY Date ASC
        """

        df = pd.read_sql(query, conn)
        df['Date'] = pd.to_datetime(df['Date'])

        # Ensure numerical columns are in the correct format
        df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
        df['Open'] = pd.to_numeric(df['Open'], errors='coerce')
        df['High'] = pd.to_numeric(df['High'], errors='coerce')
        df['Low'] = pd.to_numeric(df['Low'], errors='coerce')

        # Drop rows with NaN values in critical columns
        df.dropna(subset=['Close'], inplace=True)

        # Sort by date to ensure correct order
        df.sort_values('Date', inplace=True)

        # Calculate day of the year
        df['Day_of_Year'] = df['Date'].dt.dayofyear

        # Calculate percentage change
        df['Pct_Change'] = df['Close'].pct_change() * 100

        # Group by day of the year and calculate average percentage change
        avg_pct_change = df.groupby('Day_of_Year')['Pct_Change'].mean()

        # Ensure all days are included
        all_days = pd.DataFrame(index=np.arange(1, 368), columns=['Pct_Change'])  # 1 to 367, to account for leap year
        avg_pct_change = avg_pct_change.reindex(all_days.index).fillna(0)  # Fill missing days with 0

        # Calculate cumulative sum
        cum_sum = avg_pct_change.cumsum()

        # Find the max and min values of cumulative sum
        max_value = cum_sum.max()
        min_value = cum_sum.min()

        # Normalize to a 0-100 index
        indexed_cum_sum = 100 * (cum_sum - min_value) / (max_value - min_value)

        # Create the table if it doesn't exist
        conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {seasonality_table_name} (
            Day_of_Year INTEGER PRIMARY KEY,
            Indexed_Cumulative_Percent_Change REAL
        )
        """)

        # Insert or replace the indexed cumulative percentage change data
        for day, value in indexed_cum_sum.items():
            conn.execute(f"""
            INSERT OR REPLACE INTO {seasonality_table_name} (Day_of_Year, Indexed_Cumulative_Percent_Change)
            VALUES (?, ?)
            """, (day, value))

        print(f"Seasonality data for {market_name} for {years} years stored in the database.")


def main():
    # Connect to the SQLite database
    conn = sqlite3.connect('../data/markets_data.db')

    # Iterate over each market and fetch the data
    for market_name, ticker in market_tickers.items():
        print(f"Fetching OHLC data for {market_name}...")
        fetch_ohlc_for_2024(ticker, market_name, conn)

        # Compute and store seasonal patterns
        compute_and_store_seasonality(market_name, conn)

    # Commit the changes and close the database connection
    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
