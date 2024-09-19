import sqlite3


def remove_commas_from_table(conn, table_name, columns):
    """
    Remove commas from numeric columns in the specified table.
    """
    cursor = conn.cursor()

    for column in columns:
        # Update the table to remove commas from the specified column
        update_query = f"""
        UPDATE {table_name}
        SET {column} = REPLACE({column}, ',', '')
        WHERE {column} LIKE '%,%'
        """
        cursor.execute(update_query)

    # Commit the changes
    conn.commit()


def alter_table_schema(conn, table_name):
    """
    Ensure the column types in the specified table are REAL.
    """
    cursor = conn.cursor()

    # Check current column types
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for col in columns:
        column_name, column_type = col[1], col[2]
        if column_type not in ('REAL', 'FLOAT'):
            print(f"Column {column_name} in {table_name} is of type {column_type}. Converting to REAL.")
            # Alter table to change column type to REAL
            conn.execute(f"""
            CREATE TABLE temp_{table_name} AS SELECT * FROM {table_name}
            """)
            conn.execute(f"""
            DROP TABLE {table_name}
            """)
            conn.execute(f"""
            CREATE TABLE {table_name} AS SELECT * FROM temp_{table_name}
            """)
            conn.execute(f"""
            DROP TABLE temp_{table_name}
            """)

    conn.commit()


def main():
    # Connect to the SQLite database
    conn = sqlite3.connect('../data/markets_data.db')

    # Define the tables and columns to fix
    tables_and_columns = {
        'cocoa_ohlc': ['Close', 'Open', 'High', 'Low'],
        'gold_ohlc': ['Close', 'Open', 'High', 'Low']
    }

    for table_name, columns in tables_and_columns.items():
        print(f"Fixing historical data for {table_name}...")
        remove_commas_from_table(conn, table_name, columns)
        alter_table_schema(conn, table_name)

    # Close the database connection
    conn.close()
    print("Fixing completed.")


if __name__ == "__main__":
    main()
