import yfinance as yf
from datetime import datetime
import sqlite3
import pandas as pd
import os
# from config import market_tickers  # Import market_tickers from config.py

# Path to the database
db_path = os.getenv('DATABASE_PATH', '/Users/kamil/PycharmProjects/MarketsDashboard/app/data/markets_data.db')

def fetch_ohlc_data(ticker, market_name, conn):
    start_date = "1989-01-01"
    end_date = (datetime.now() - pd.Timedelta(days=1)).strftime('%Y-%m-%d')  # Fetch data up to yesterday

    # Fetch OHLC data from yfinance
    data = yf.download(ticker, start=start_date, end=end_date)

    if data.empty:
        print(f"No data fetched for {market_name}.")
        return

    # Reset the index to get the Date column
    data.reset_index(inplace=True)

    # Rename columns to match the desired format
    data.rename(columns={'Close': 'Close'}, inplace=True)

    # Ensure the correct column order
    data = data[['Date', 'Close', 'Open', 'High', 'Low']]

    # Create table name
    table_name = market_name.lower().replace(' ', '_') + '_ohlc'

    # Check if the table exists; if not, create it
    try:
        conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (Date TEXT PRIMARY KEY, Close REAL, Open REAL, High REAL, Low REAL)")
    except Exception as e:
        print(f"Error creating table: {e}")

    # Insert or replace the new data
    data.to_sql(table_name, conn, if_exists='replace', index=False)
    print(f"Data for {market_name} inserted into the database.")

def main():
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)

    # Fetch and save OHLC data for each market from config.py
    # for market_name, ticker in market_tickers.items():
    #     print(f"Fetching OHLC data for {market_name}...")
    #     fetch_ohlc_data(ticker, market_name, conn)
    fetch_ohlc_data("ETH=F", "Ethereum", conn)

    # Commit the changes and close the database connection
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()
