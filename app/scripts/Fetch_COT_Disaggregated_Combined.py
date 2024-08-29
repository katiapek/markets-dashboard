import requests
import pandas as pd
import sqlite3
from pathlib import Path

def fetch_all_data(base_url, headers=None, limit=1000):
    """
    Fetch all data from the given API endpoint with pagination.
    """
    all_data = []
    offset = 0
    while True:
        params = {
            '$limit': limit,
            '$offset': offset,
            '$order': ':id'
        }

        response = requests.get(base_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        if not data:
            break  # Exit loop if no more data is returned

        all_data.extend(data)
        offset += limit

    return all_data

def load_data_to_dataframe(all_data):
    """
    Load the entire dataset into a DataFrame.
    """
    return pd.DataFrame(all_data)

def filter_and_save_by_market(df, market_codes, conn):
    """
    Filter the DataFrame for each market code, sort by date, and save to the database.
    """
    for commodity_name, market_code in market_codes.items():
        filtered_df = df[df['cftc_contract_market_code'] == market_code].copy()  # Make a copy of the DataFrame

        # Ensure sorting by the 'report_date_as_yyyy_mm_dd' column
        if 'report_date_as_yyyy_mm_dd' in filtered_df.columns:
            filtered_df.loc[:, 'report_date_as_yyyy_mm_dd'] = pd.to_datetime(
                filtered_df['report_date_as_yyyy_mm_dd'].str[:10])  # Convert to datetime
            filtered_df.sort_values('report_date_as_yyyy_mm_dd', inplace=True)  # Sort by date

        # Convert datetime to string for SQLite compatibility
        filtered_df['report_date_as_yyyy_mm_dd'] = filtered_df['report_date_as_yyyy_mm_dd'].astype(str)

        table_name = commodity_name.replace(" ", "_").lower() + '_cot_disaggregated_combined'
        save_to_database(filtered_df, table_name, conn)

def save_to_database(df, table_name, conn):
    """
    Save the DataFrame to the SQLite database in the specified table.
    """
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    print(f"Data for {table_name} saved to the database.")

def main():
    base_url = "https://publicreporting.cftc.gov/resource/kh3c-gbw2.json"
    app_token = "DpRffv2Bz276EwYjvO0EutvuP"
    headers = {"X-App-Token": app_token}

    # Fetch all data from the API
    all_data = fetch_all_data(base_url, headers=headers)

    # Load the data into a DataFrame
    df = load_data_to_dataframe(all_data)

    # Market codes for filtering
    market_codes = {
        'Australian Dollar': '232741',
        'British Pound': '096742',
        'Canadian Dollar': '090741',
        'Cocoa': '073732',
        'Coffee': '083731',
        'Corn': '002602',
        'Crude Oil': '067651',
        'Euro FX': '099741',
        'Gold': '088691',
        'Japanese Yen': '097741',
        'New Zealand Dollar': '112741',
        'Silver': '084691',
        'Soybeans': '005602',
        'Swiss Franc': '092741',
        'Wheat': '001602'
    }

    # Connect to the SQLite database
    db_path = Path(__file__).parent.parent / 'data/markets_data.db'
    conn = sqlite3.connect(db_path)

    # Filter and save data for each market into the database
    filter_and_save_by_market(df, market_codes, conn)

    # Commit the changes and close the database connection
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()
