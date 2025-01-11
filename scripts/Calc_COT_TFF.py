import pandas as pd
from sqlalchemy import create_engine, text
import os
from config import market_tickers, db_path_str

# Database URL from environment variable or config
db_url = os.environ.get(db_path_str)
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)

# Create the database engine
engine = create_engine(db_url)


def calculate_and_store_cot_data(market_name, data_type):
    print(f"Processing data for {market_name}...")

    # Determine the input and output table names
    input_table = f"{market_name.lower().replace(' ', '_')}_{data_type}"
    output_table = f"{market_name.lower().replace(' ', '_')}_{data_type}_calc"

    with engine.connect() as conn:
        # Fetch the data
        query = text(f"SELECT * FROM {input_table}")
        df = pd.read_sql(query, conn)


        # Ensure correct data types for calculations
        numeric_columns = {
            'cot_tff_combined': [
                'open_interest_all', 'lev_money_positions_long', 'lev_money_positions_short',
                'asset_mgr_positions_long', 'asset_mgr_positions_short',
                'dealer_positions_long_all', 'dealer_positions_short_all'
            ],
            'cot_tff_futures_only': [
                'open_interest_all', 'lev_money_positions_long', 'lev_money_positions_short',
                'asset_mgr_positions_long', 'asset_mgr_positions_short',
                'dealer_positions_long_all', 'dealer_positions_short_all'
            ]
        }

        for col in numeric_columns[data_type]:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Forward fill missing values
        df.sort_values('report_date_as_yyyy_mm_dd', ascending=True)
        df = df.ffill()

        # Calculate percentage changes
        df['pct_change_open_interest'] = df['open_interest_all'].pct_change() * 100
        df['pct_change_lev_money_long'] = df['lev_money_positions_long'].pct_change() * 100
        df['pct_change_lev_money_short'] = df['lev_money_positions_short'].pct_change() * 100
        df['pct_change_asset_mgr_long'] = df['asset_mgr_positions_long'].pct_change() * 100
        df['pct_change_asset_mgr_short'] = df['asset_mgr_positions_short'].pct_change() * 100
        df['pct_change_dealer_long'] = df['dealer_positions_long_all'].pct_change() * 100
        df['pct_change_dealer_short'] = df['dealer_positions_short_all'].pct_change() * 100

        # Calculate net positions
        df['lev_money_net_positions'] = df['lev_money_positions_long'] - df['lev_money_positions_short']
        df['asset_mgr_net_positions'] = df['asset_mgr_positions_long'] - df['asset_mgr_positions_short']
        df['dealer_net_positions'] = df['dealer_positions_long_all'] - df['dealer_positions_short_all']

        # Calculate percentage change in net positions
        df['pct_change_lev_money_net_positions'] = df['lev_money_net_positions'].pct_change() * 100
        df['pct_change_asset_mgr_net_positions'] = df['asset_mgr_net_positions'].pct_change() * 100
        df['pct_change_dealer_net_positions'] = df['dealer_net_positions'].pct_change() * 100

        # Calculate 26-week indices
        def calculate_index(series):
            min_val = series.rolling(window=26, min_periods=1).min()
            max_val = series.rolling(window=26, min_periods=1).max()
            return ((series - min_val) / (max_val - min_val)) * 100

        df['lev_money_26w_index'] = calculate_index(df['lev_money_net_positions'])
        df['asset_mgr_26w_index'] = calculate_index(df['asset_mgr_net_positions'])
        df['dealer_26w_index'] = calculate_index(df['dealer_net_positions'])

        # Select only necessary columns for the new table
        calc_df = df[['report_date_as_yyyy_mm_dd', 'pct_change_open_interest',
                      'pct_change_lev_money_long', 'pct_change_lev_money_short',
                      'pct_change_asset_mgr_long', 'pct_change_asset_mgr_short',
                      'pct_change_dealer_long', 'pct_change_dealer_short',
                      'lev_money_net_positions', 'asset_mgr_net_positions', 'dealer_net_positions',
                      'pct_change_lev_money_net_positions', 'pct_change_asset_mgr_net_positions',
                      'pct_change_dealer_net_positions',
                      'lev_money_26w_index', 'asset_mgr_26w_index', 'dealer_26w_index']]

        # Round numbers to 1 decimal place
        calc_df = calc_df.round(1)

        # Save to new table, appending instead of replacing
        try:
            calc_df.to_sql(output_table, engine, if_exists='append', index=False, method="multi")
            print(f"Calculated data for {market_name} saved to {output_table}.")
        except Exception as e:
            print(f"Error saving data for {market_name}: {e}")


# Calculate and store data for all markets and types
data_types = ['cot_tff_combined', 'cot_tff_futures_only']

for market in market_tickers.keys():
    for data_type in data_types:
        calculate_and_store_cot_data(market, data_type)
