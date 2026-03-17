import requests
import pandas as pd
from sqlalchemy import create_engine, text
from config import market_codes, db_path_str
import os

# db_path = os.environ[db_path_str]
# engine = create_engine(db_path)

db_url = os.environ.get(db_path_str)
if not db_url:
    raise ValueError("Database URL not found. Please set the variable correctly.")

if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
engine = create_engine(db_url)


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


def filter_and_save_by_market(df, market_codes):
    """
    Filter the DataFrame for each market code, sort by date, and save to the database.
    """
    with engine.connect() as conn:
        for commodity_name, market_code in market_codes.items():
            filtered_df = df[df['cftc_contract_market_code'] == market_code].copy()  # Make a copy of the DataFrame

            if filtered_df.empty:
                print(f"No data found for {commodity_name}. Skipping...")
                continue

            # Ensure sorting by the 'report_date_as_yyyy_mm_dd' column
            if 'report_date_as_yyyy_mm_dd' in filtered_df.columns:
                filtered_df['report_date_as_yyyy_mm_dd'] = pd.to_datetime(
                    filtered_df['report_date_as_yyyy_mm_dd'].str[:10], errors='coerce'
                ).dt.strftime('%Y-%m-%d %H:%M:%S')  # Convert to datetime
                filtered_df.sort_values('report_date_as_yyyy_mm_dd', inplace=True)  # Sort by date

            table_name = commodity_name.replace(" ", "_").lower() + '_cot_disaggregated_futures_only'

            query = f"SELECT MAX(report_date_as_yyyy_mm_dd) FROM {table_name}"
            try:
                latest_date = conn.execute(text(query)).scalar()
                if latest_date:
                    latest_date = pd.to_datetime(latest_date)
            except Exception:
                latest_date = None

            # Filter new rows based on the latest found date in the report
            if latest_date:
                latest_date = pd.to_datetime(latest_date)
                filtered_df['report_date_as_yyyy_mm_dd'] = pd.to_datetime(filtered_df['report_date_as_yyyy_mm_dd'])
                filtered_df = filtered_df[filtered_df['report_date_as_yyyy_mm_dd'] > latest_date]

            if filtered_df.empty:
                print(f"No new data to insert for {commodity_name}. Skipping...")
                continue

            # Convert date format back to string for saving
            filtered_df['report_date_as_yyyy_mm_dd'] = filtered_df['report_date_as_yyyy_mm_dd'].dt.strftime(
                '%Y-%m-%d %H:%M:%S'
            )

            # Save data to the database
            try:
                filtered_df.to_sql(table_name, conn, if_exists='append', index=False)
                conn.commit()
                print(f"Saved {len(filtered_df)} rows to {table_name}.")
            except Exception as e:
                    print(f"Error saving data to {table_name}: {e}")


def main():
    base_url = "https://publicreporting.cftc.gov/resource/72hh-3qpy.json"
    app_token = os.environ.get("CFTC_TOKEN")
    headers = {"X-App-Token": app_token}

    # Fetch all data from the API
    all_data = fetch_all_data(base_url, headers=headers)

    # Load the data into a DataFrame
    df = load_data_to_dataframe(all_data)

    if df.empty:
        print("No data retrieved from the API. Exiting...")
        return

    # Filter and save data for each market into the database
    filter_and_save_by_market(df, market_codes)


if __name__ == "__main__":
    main()





