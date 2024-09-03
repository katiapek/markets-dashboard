import pandas as pd
import sqlite3
import os

# Path to the database
db_path = os.getenv('DATABASE_PATH', '/Users/kamil/PycharmProjects/MarketsDashboard/app/data/markets_data.db')

# List of markets (adjust as necessary or import from config.py)
market_tickers = {
    'Australian Dollar': 'AUDUSD=X',
    'New Zealand Dollar': 'NZDUSD=X',
    'British Pound': 'GBPUSD=X',
    'Canadian Dollar': 'USDCAD=X',
    'Cocoa': 'CC=F',
    'Coffee': 'KC=F',
    'Corn': 'ZC=F',
    'Crude Oil': 'CL=F',
    'Euro FX': 'EURUSD=X',
    'Gold': 'GC=F',
    'Japanese Yen': 'USDJPY=X',
    'Silver': 'SI=F',
    'Soybeans': 'ZS=F',
    'Swiss Franc': 'USDCHF=X',
    'Wheat': 'ZW=F'
}

def calculate_and_store_cot_data(market_name):
    print(f"Processing data for {market_name}...")

    # Connect to the database
    conn = sqlite3.connect(db_path)
    query = f"SELECT * FROM {market_name.lower().replace(' ', '_')}_cot_legacy_combined"
    df = pd.read_sql(query, conn)

    # Ensure correct data types for calculations
    numeric_columns = [
        'open_interest_all',
        'noncomm_positions_long_all',
        'noncomm_positions_short_all',
        'comm_positions_long_all',
        'comm_positions_short_all'
    ]
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Forward fill missing values
    df = df.ffill()

    # Calculate percentage changes
    df['pct_change_open_interest'] = df['open_interest_all'].pct_change() * 100
    df['pct_change_noncomm_long'] = df['noncomm_positions_long_all'].pct_change() * 100
    df['pct_change_noncomm_short'] = df['noncomm_positions_short_all'].pct_change() * 100
    df['pct_change_comm_long'] = df['comm_positions_long_all'].pct_change() * 100
    df['pct_change_comm_short'] = df['comm_positions_short_all'].pct_change() * 100

    # Calculate net positions
    df['noncomm_net_positions'] = df['noncomm_positions_long_all'] - df['noncomm_positions_short_all']
    df['comm_net_positions'] = df['comm_positions_long_all'] - df['comm_positions_short_all']

    # Calculate percentage change in net positions
    df['pct_change_noncomm_net_positions'] = df['noncomm_net_positions'].pct_change() * 100
    df['pct_change_comm_net_positions'] = df['comm_net_positions'].pct_change() * 100

    # Calculate 26-week indices
    def calculate_index(series):
        min_val = series.rolling(window=26, min_periods=1).min()
        max_val = series.rolling(window=26, min_periods=1).max()
        return ((series - min_val) / (max_val - min_val)) * 100

    df['noncomm_26w_index'] = calculate_index(df['noncomm_net_positions'])
    df['comm_26w_index'] = calculate_index(df['comm_net_positions'])

    # Select only necessary columns for the new table
    calc_df = df[['report_date_as_yyyy_mm_dd', 'pct_change_open_interest',
                  'pct_change_noncomm_long', 'pct_change_noncomm_short',
                  'pct_change_comm_long', 'pct_change_comm_short',
                  'noncomm_net_positions', 'comm_net_positions',
                  'pct_change_noncomm_net_positions', 'pct_change_comm_net_positions',
                  'noncomm_26w_index', 'comm_26w_index']]

    # Round numbers to 1 decimal place
    calc_df = calc_df.round(1)

    # Save to new table
    output_table = f"{market_name.lower().replace(' ', '_')}_cot_legacy_combined_calc"
    calc_df.to_sql(output_table, conn, if_exists='replace', index=False)
    print(f"Calculated data for {market_name} saved to {output_table}.")

    # Close the connection
    conn.close()

# Calculate and store data for all markets
for market in market_tickers.keys():
    calculate_and_store_cot_data(market)
