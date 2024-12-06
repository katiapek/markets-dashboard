import pandas as pd
import sqlite3


def merge_csv_to_sqlite(historical_file, db_name, table_name):
    # Specify columns to load to avoid including unwanted columns
    usecols = ['Date', 'Close', 'Open', 'High', 'Low']

    # Date parser for the specific format mm/dd/yyyy
    date_parser = lambda x: pd.to_datetime(x, format='%m/%d/%Y')

    # Load only the specified columns from the CSV file
    historical_df = pd.read_csv(historical_file, usecols=usecols, parse_dates=['Date'], date_format='%m/%d/%Y')

    # Connect to SQLite database
    conn = sqlite3.connect(db_name)

    # Check if the table exists and fetch existing dates if so
    try:
        existing_dates = pd.read_sql_query(f"SELECT Date FROM {table_name}", conn)
        existing_dates['Date'] = pd.to_datetime(existing_dates['Date'])
    except (pd.io.sql.DatabaseError, sqlite3.OperationalError):
        # If the table does not exist, create it with all data from historical_df
        historical_df.to_sql(table_name, conn, if_exists='replace', index=False)
        conn.close()
        print(f"Table '{table_name}' created and data saved in database '{db_name}'.")
        return

    # Filter out records in historical_df that are already in the database
    merged_df = historical_df[~historical_df['Date'].isin(existing_dates['Date'])]

    # Append only new records to the database
    if not merged_df.empty:
        merged_df.to_sql(table_name, conn, if_exists='append', index=False)
        print(f"New records added to table '{table_name}' in database '{db_name}'.")
    else:
        print(f"No new records to add. All dates in '{historical_file}' are already in the database.")

    # Close the connection
    conn.close()


# Example usage
merge_csv_to_sqlite(
    historical_file='Bitcoin Historical Data.csv',
    db_name='markets_data.db',
    table_name='bitcoin_ohlc'
)
