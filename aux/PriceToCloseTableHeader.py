import sqlite3

def rename_price_column(db_path, table_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if the "Close" column exists in the original table
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]

    if 'Price' not in columns:
        print(f"'Price' column not found in {table_name}. Skipping.")
        conn.close()
        return

    # Define the new table name
    new_table_name = table_name + "_new"

    # Create a new table with the corrected schema
    cursor.execute(f"""
    CREATE TABLE {new_table_name} AS
    SELECT Date, Open, High, Low, Price AS Close
    FROM {table_name}
    """)

    # Drop the old table
    cursor.execute(f"DROP TABLE {table_name}")

    # Rename the new table to the original table name
    cursor.execute(f"ALTER TABLE {new_table_name} RENAME TO {table_name}")

    # Commit changes and close the connection
    conn.commit()
    conn.close()

def main():
    db_path = '../data/markets_data.db'
    tables = [
        'australian_dollar_ohlc',
        'new_zealand_dollar_ohlc',
        'british_pound_ohlc',
        'canadian_dollar_ohlc',
        'cocoa_ohlc',
        'coffee_ohlc',
        'corn_ohlc',
        'crude_oil_ohlc',
        'euro_fx_ohlc',
        'gold_ohlc',
        'japanese_yen_ohlc',
        'silver_ohlc',
        'soybeans_ohlc',
        'swiss_franc_ohlc',
        'wheat_ohlc'
    ]

    for table in tables:
        print(f"Updating column names for table: {table}")
        rename_price_column(db_path, table)

if __name__ == "__main__":
    main()
