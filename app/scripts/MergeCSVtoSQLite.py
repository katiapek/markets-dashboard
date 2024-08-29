import pandas as pd
import sqlite3

def merge_csv_to_sqlite(historical_file, current_file, db_name, table_name):
    # Date parser for the specific format mm/dd/yyyy
    date_parser = lambda x: pd.to_datetime(x, format='%m/%d/%Y')

    # Load historical and current data with the correct date format
    historical_df = pd.read_csv(historical_file, parse_dates=['Date'], date_parser=date_parser)
    current_df = pd.read_csv(current_file, parse_dates=['Date'], date_parser=date_parser)

    # Merge dataframes
    merged_df = pd.concat([historical_df, current_df])

    # Drop duplicates if necessary
    merged_df.drop_duplicates(subset='Date', keep='last', inplace=True)

    # Sort by date (if not already sorted)
    merged_df.sort_values(by='Date', inplace=True)

    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect(db_name)

    # Store the merged data in the specified table
    merged_df.to_sql(table_name, conn, if_exists='replace', index=False)

    # Close the connection
    conn.close()

    print(f"Data merged and saved to table '{table_name}' in database '{db_name}'.")

# Example usage
merge_csv_to_sqlite(
    historical_file='Wheat OHLC historical.csv',
    current_file='Wheat OHLC yeartodate.csv',
    db_name='markets_data.db',
    table_name='wheat_ohlc'
)
