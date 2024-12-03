# data_fetchers.py

import os
import sqlite3
import pandas as pd
from scripts.config import db_path_str
from datetime import timedelta
from dateutil import parser
from functools import lru_cache


# Set the database path
db_path = os.getenv('DATABASE_PATH', db_path_str)

@lru_cache(maxsize=10)
def fetch_ohlc_data_cached(market, year):
    """
    Fetches and caches OHLC data for a specific market and year.
    """
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    return OHLCDataFetcher.fetch_ohlc_data_by_range(market, start_date, end_date)


@lru_cache(maxsize=10)
def fetch_active_subplot_data(market, year, subplot, table_suffix, report_type):
    if subplot == 'Open Interest':
        return OpenInterestDataFetcher.fetch_open_interest_data(market, year, table_suffix, report_type)
    elif subplot == 'OI Percentages':
        return OpenInterestPercentagesFetcher.fetch_open_interest_percentages(market, year, table_suffix, report_type)
    elif subplot == 'Positions Change':
        return PositionsChangeDataFetcher.fetch_positions_change_data(market, year, table_suffix, report_type)
    elif subplot == 'Net Positions':
        return NetPositionsDataFetcher.fetch_net_positions_data(market, year, table_suffix, report_type)
    elif subplot == 'Net Positions Change':
        return PositionsChangeNetDataFetcher.fetch_positions_change_net_data(market, year, table_suffix, report_type)
    elif subplot == '26W Index':
        return Index26WDataFetcher.fetch_26w_index_data(market, year, table_suffix, report_type)
    return pd.DataFrame()


@lru_cache(maxsize=5)
def fetch_seasonal_data_cached(market, years, base_year):
    return SeasonalDataFetcher.fetch_seasonal_data(market, years, base_year)


def clean_ohlc_data(df):
    """
    Clean OHLC data by removing commas from Open, High, Low, Close columns.

    Args:
        df (pd.DataFrame): DataFrame containing OHLC data.

    Returns:
        pd.DataFrame: Cleaned DataFrame with commas removed from numeric columns.
    """
    ohlc_columns = ['Open', 'High', 'Low', 'Close']

    for col in ohlc_columns:
        df[col] = df[col].astype(str).str.replace(',', '').astype(float)

    return df

class BaseDataFetcher:
    """
    Base class for fetching data from an SQLite database.
    """

    @staticmethod
    def fetch_data(query, params=None):
        """
        Fetch data from the database using the given query and parameters.

        Args:
            query (str): The SQL query to execute.
            params (tuple, optional): The parameters for the SQL query.

        Returns:
            pd.DataFrame: DataFrame containing the fetched data.
        """
        conn = sqlite3.connect(db_path)
        try:
            df = pd.read_sql(query, conn, params=params)
        except Exception as e:
            print(f"Error fetching data: {e}")
            df = pd.DataFrame()
        finally:
            conn.close()
        return df


class SeasonalDataFetcher(BaseDataFetcher):
    """
    Data fetcher for seasonal data.
    """

    @staticmethod
    def fetch_seasonal_data(market, years, current_year):
        """
        Fetch seasonal data for a given market and number of years.

        Args:
            market (str): The market name.
            years (int): Number of years for the seasonal data.
            current_year (int): The year for which to align the Day_of_Year to Date.

        Returns:
            pd.DataFrame: DataFrame containing the seasonal data with an additional 'Date' column.
        """
        table_name = f"{market.lower().replace(' ', '_')}_ohlc_seasonality_{years}_years" # f"{format_market_name(market)}_seasonality_{years}_years"
        query = f"SELECT * FROM {table_name} ORDER BY Day_of_Year ASC"
        df = SeasonalDataFetcher.fetch_data(query)

        if not df.empty:
            # Ensure Day_of_Year is treated as an integer
            df['Day_of_Year'] = df['Day_of_Year'].astype(int)

            # Creating base date string for January 1st of the current year
            base_date = parser.parse(f"{current_year}-01-01")

            # Convert Day_of_Year to actual dates within the current year
            df['Date'] = df['Day_of_Year'].apply(lambda x: (base_date + timedelta(days=x - 1)).strftime("%Y-%m-%d"))

            # Convert 'Date' column to datetime format explicitly
            df['Date'] = pd.to_datetime(df['Date'], format="%Y-%m-%d")

            # Sort by the new Date column
            df.sort_values(by='Date', inplace=True)

        return df


class OHLCDataFetcher(BaseDataFetcher):
    """
    Data fetcher for OHLC (Open, High, Low, Close) data.
    """

    @staticmethod
    def fetch_ohlc_data(market, year):
        table_name = f"{market.lower().replace(' ', '_')}_ohlc"
        print(f"Fetching OHLC from table: {table_name} for year: {year}")

        query = f"SELECT * FROM {table_name} WHERE Date BETWEEN ? AND ?"
        params = (f'{year}-01-01 00:00:00', f'{year}-12-31 23:59:59')
        print(f"Running query: {query} with params: {params}")

        df = OHLCDataFetcher.fetch_data(query, params)

        if df.empty:
            print(f"No data found for {market} in {year}")
        else:
            df['Date'] = pd.to_datetime(df['Date'], format="%Y-%m-%d %H:%M:%S")
            df['Day_of_Year'] = df['Date'].dt.dayofyear
            print(f"Fetched data for {year}: {df.head()}")
        df = clean_ohlc_data(df)

        return df

    @staticmethod
    def fetch_ohlc_data_by_range(market, start_date, end_date):
        """
        Fetch OHLC data for a given market within a date range.

        Args:
            market (str): The market name.
            start_date (str): The start date in the format 'YYYY-MM-DD'.
            end_date (str): The end date in the format 'YYYY-MM-DD'.

        Returns:
            pd.DataFrame: DataFrame containing the OHLC data.
        """
        table_name = f"{market.lower().replace(' ', '_')}_ohlc"
        print(f"Fetching OHLC from table: {table_name} for date range: {start_date} to {end_date}")

        query = f"SELECT * FROM {table_name} WHERE Date BETWEEN ? AND ?"
        params = (f'{start_date} 00:00:00', f'{end_date} 23:59:59')

        df = OHLCDataFetcher.fetch_data(query, params)

        if not df.empty:
            # Parse the 'Date' column with the appropriate format
            df['Date'] = pd.to_datetime(df['Date'], format="%Y-%m-%d %H:%M:%S")
            df['Day_of_Year'] = df['Date'].dt.dayofyear

        df = clean_ohlc_data(df)
        return df


class OpenInterestDataFetcher(BaseDataFetcher):
    """
    Data fetcher for Open Interest data.
    """

    @staticmethod
    def fetch_open_interest_data(market, year, table_suffix, report_type):
        """
        Fetch Open Interest data for a given market and year.

        Args:
            market (str): The market name.
            year (int): The year for which to fetch the Open Interest data.
            table_suffix (str): The table suffix indicating combined or futures-only.
            report_type (str): The report type, e.g., 'legacy' or 'disaggregated'.


        Returns:
            pd.DataFrame: DataFrame containing the Open Interest data with additional 'Day_of_Year' column.
        """
        table_name = f"{market.lower().replace(' ', '_')}{table_suffix}"
        # print(f"Fetching from Table {table_name} and report: {report_type}")
        # Select columns based on the report type
        if report_type == 'legacy':
            columns = 'report_date_as_yyyy_mm_dd, open_interest_all'
        elif report_type == 'disaggregated':
            columns = 'report_date_as_yyyy_mm_dd, open_interest_all'
            # m_money_positions_long_all, m_money_positions_short_all,
            # prod_merc_positions_long, prod_merc_positions_short, swap_positions_long_all,
            # swap_positions_short_all
        elif report_type == 'tff':
            columns = 'report_date_as_yyyy_mm_dd, open_interest_all'
        else:
            raise ValueError(f"Unknown report type: {report_type}")

        query = f"""
        SELECT {columns}
        FROM {table_name}
        WHERE report_date_as_yyyy_mm_dd BETWEEN ? AND ?
        """
        params = (f'{year}-01-01', f'{year}-12-31')
        df = OpenInterestDataFetcher.fetch_data(query, params)
        if not df.empty:
            df['report_date_as_yyyy_mm_dd'] = pd.to_datetime(df['report_date_as_yyyy_mm_dd'], format="%Y-%m-%d %H:%M:%S")
            # df['Day_of_Year'] = df['report_date_as_yyyy_mm_dd'].dt.dayofyear
            # df['Date'] = pd.to_datetime(df['report_date_as_yyyy_mm_dd'], format="%Y-%m-%d %H:%M:%S")
            df['Date'] = df['report_date_as_yyyy_mm_dd']
            df.sort_values(by='Date', inplace=True)
        return df

class OpenInterestPercentagesFetcher(BaseDataFetcher):
    """
    Data fetcher for Open Interest Percentages data.
    """

    @staticmethod
    def fetch_open_interest_percentages(market, year, table_suffix, report_type):
        """
        Fetch Open Interest Percentages data for a given market and year.

        Args:
            market (str): The market name.
            year (int): The year for which to fetch the Open Interest Percentages data.
            table_suffix (str): The table suffix indicating combined or futures-only.
            report_type (str): The report type, e.g., 'legacy' or 'disaggregated'.

        Returns:
            pd.DataFrame: DataFrame containing the Open Interest Percentages data with additional 'Day_of_Year' column.
        """
        table_name = f"{market.lower().replace(' ', '_')}{table_suffix}"

        # Select columns based on the report type
        if report_type == 'legacy':
            columns = ('report_date_as_yyyy_mm_dd, '
                       'pct_of_oi_noncomm_long_all, '
                       'pct_of_oi_noncomm_short_all, '
                       'pct_of_oi_comm_long_all, '
                       'pct_of_oi_comm_short_all')

            numeric_columns = [
                'pct_of_oi_noncomm_long_all',
                'pct_of_oi_noncomm_short_all',
                'pct_of_oi_comm_long_all',
                'pct_of_oi_comm_short_all'
            ]

        elif report_type == 'disaggregated':
            columns = ('report_date_as_yyyy_mm_dd, '
                       'pct_of_oi_m_money_long_all, pct_of_oi_m_money_short_all,'
                       'pct_of_oi_prod_merc_long, pct_of_oi_prod_merc_short,'
                       'pct_of_oi_swap_long_all, pct_of_oi_swap_short_all')

            numeric_columns = [
                'pct_of_oi_m_money_long_all',
                'pct_of_oi_m_money_short_all',
                'pct_of_oi_prod_merc_long',
                'pct_of_oi_prod_merc_short',
                'pct_of_oi_swap_long_all',
                'pct_of_oi_swap_short_all'
            ]

        elif report_type == 'tff':
            columns = ('report_date_as_yyyy_mm_dd, '
                       'pct_of_oi_lev_money_long, pct_of_oi_lev_money_short,'
                       'pct_of_oi_asset_mgr_long, pct_of_oi_asset_mgr_short,'
                       'pct_of_oi_dealer_long_all, pct_of_oi_dealer_short_all')

            numeric_columns = [
                'pct_of_oi_lev_money_long',
                'pct_of_oi_lev_money_short',
                'pct_of_oi_asset_mgr_long',
                'pct_of_oi_asset_mgr_short',
                'pct_of_oi_dealer_long_all',
                'pct_of_oi_dealer_short_all'
            ]

        else:
            raise ValueError(f"Unknown report type: {report_type}")

        query = f"""
        SELECT {columns}
        FROM {table_name}
        WHERE report_date_as_yyyy_mm_dd BETWEEN ? AND ?
        """
        params = (f'{year}-01-01', f'{year}-12-31')
        df = OpenInterestPercentagesFetcher.fetch_data(query, params)

        if not df.empty:
            df['report_date_as_yyyy_mm_dd'] = pd.to_datetime(df['report_date_as_yyyy_mm_dd'])
            # df['Day_of_Year'] = df['report_date_as_yyyy_mm_dd'].dt.dayofyear

            # Convert the relevant columns to numeric, based on report type
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            df['Date'] = df['report_date_as_yyyy_mm_dd']
            df.sort_values(by='Date', inplace=True)

        return df

class PositionsChangeDataFetcher(BaseDataFetcher):
    """
    Data fetcher for Positions Change data.
    """

    @staticmethod
    def fetch_positions_change_data(market, year, table_suffix, report_type):
        """
        Fetch Positions Change data for a given market and year.

        Args:
            market (str): The market name.
            year (int): The year for which to fetch the Positions Change data.
            table_suffix (str): The table suffix indicating combined or futures-only.
            report_type (str): The report type, e.g., 'legacy' or 'disaggregated'.

        Returns:
            pd.DataFrame: DataFrame containing the Positions Change data with additional 'Day_of_Year' column.
        """
        table_name = f"{market.lower().replace(' ', '_')}{table_suffix}_calc"

        # Select columns based on the report type
        if report_type == 'legacy':
            columns = ('report_date_as_yyyy_mm_dd, '
                       'pct_change_noncomm_long, '
                       'pct_change_noncomm_short, '
                       'pct_change_comm_long, '
                       'pct_change_comm_short')

            numeric_columns = ['report_date_as_yyyy_mm_dd',
                               'pct_change_noncomm_long',
                               'pct_change_noncomm_short',
                               'pct_change_comm_long',
                               'pct_change_comm_short']

        elif report_type == 'disaggregated':

            columns = ('report_date_as_yyyy_mm_dd, '
                       'pct_change_m_money_long, pct_change_m_money_short,'
                       'pct_change_prod_merc_long, pct_change_prod_merc_short,'
                       'pct_change_swap_long, pct_change_swap_short')

            numeric_columns = [
                'report_date_as_yyyy_mm_dd',
                'pct_change_m_money_long', 'pct_change_m_money_short',
                'pct_change_prod_merc_long', 'pct_change_prod_merc_short',
                'pct_change_swap_long', 'pct_change_swap_short']

        elif report_type == 'tff':

            columns = ('report_date_as_yyyy_mm_dd, '
                       'pct_change_lev_money_long, pct_change_lev_money_short,'
                       'pct_change_asset_mgr_long, pct_change_asset_mgr_short,'
                       'pct_change_dealer_long, pct_change_dealer_short')

            numeric_columns = [
                'report_date_as_yyyy_mm_dd',
                'pct_change_lev_money_long', 'pct_change_lev_money_short',
                'pct_change_asset_mgr_long', 'pct_change_asset_mgr_short',
                'pct_change_dealer_long', 'pct_change_dealer_short']

        else:
            raise ValueError(f"Unknown report type: {report_type}")

        query = f"""
        SELECT {columns}
        FROM {table_name}
        WHERE report_date_as_yyyy_mm_dd BETWEEN ? AND ?
        """
        params = (f'{year}-01-01', f'{year}-12-31')
        df = PositionsChangeDataFetcher.fetch_data(query, params)

        if not df.empty:
            df['report_date_as_yyyy_mm_dd'] = pd.to_datetime(df['report_date_as_yyyy_mm_dd'])
            # df['Day_of_Year'] = df['report_date_as_yyyy_mm_dd'].dt.dayofyear

            # Convert the relevant columns to numeric, based on report type
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            df['Date'] = df['report_date_as_yyyy_mm_dd']
            df.sort_values(by='Date', inplace=True)
        return df

class NetPositionsDataFetcher(BaseDataFetcher):
    """
    Data fetcher for Net Positions data.
    """

    @staticmethod
    def fetch_net_positions_data(market, year, table_suffix, report_type):
        """
        Fetch Net Positions data for a given market and year.

        Args:
            market (str): The market name.
            year (int): The year for which to fetch the Net Positions data.
            table_suffix (str): The table suffix indicating combined or futures-only.
            report_type (str): The report type, e.g., 'legacy' or 'disaggregated'.

        Returns:
            pd.DataFrame: DataFrame containing the Net Positions data with additional 'Day_of_Year' column.
        """
        table_name = f"{market.lower().replace(' ', '_')}{table_suffix}_calc"

        # Select columns based on the report type
        if report_type == 'legacy':
            columns = 'report_date_as_yyyy_mm_dd, noncomm_net_positions, comm_net_positions'

            numeric_columns = ['report_date_as_yyyy_mm_dd', 'noncomm_net_positions', 'comm_net_positions']

        elif report_type == 'disaggregated':

            columns = ('report_date_as_yyyy_mm_dd, '
                       'm_money_net_positions,'
                       'prod_merc_net_positions,'
                       'swap_net_positions')

            numeric_columns = [
                'report_date_as_yyyy_mm_dd',
                'm_money_net_positions',
                'prod_merc_net_positions',
                'swap_net_positions']

        elif report_type == 'tff':

            columns = ('report_date_as_yyyy_mm_dd, '
                       'lev_money_net_positions,'
                       'asset_mgr_net_positions,'
                       'dealer_net_positions')

            numeric_columns = [
                'report_date_as_yyyy_mm_dd',
                'lev_money_net_positions',
                'asset_mgr_net_positions',
                'dealer_net_positions']

        else:
            raise ValueError(f"Unknown report type: {report_type}")

        query = f"""
        SELECT {columns}
        FROM {table_name}
        WHERE report_date_as_yyyy_mm_dd BETWEEN ? AND ?
        """
        params = (f'{year}-01-01', f'{year}-12-31')
        df = NetPositionsDataFetcher.fetch_data(query, params)

        if not df.empty:
            df['report_date_as_yyyy_mm_dd'] = pd.to_datetime(df['report_date_as_yyyy_mm_dd'])
            # df['Day_of_Year'] = df['report_date_as_yyyy_mm_dd'].dt.dayofyear

            # Convert the relevant columns to numeric, based on report type
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            df['Date'] = df['report_date_as_yyyy_mm_dd']
            df.sort_values(by='Date', inplace=True)
        return df


class PositionsChangeNetDataFetcher(BaseDataFetcher):
    """
    Data fetcher for Positions Change Net data.
    """

    @staticmethod
    def fetch_positions_change_net_data(market, year, table_suffix, report_type):
        """
        Fetch Positions Change Net data for a given market and year.

        Args:
            market (str): The market name.
            year (int): The year for which to fetch the Positions Change Net data.
            table_suffix (str): The table suffix indicating combined or futures-only.
            report_type (str): The report type, e.g., 'legacy' or 'disaggregated'.

        Returns:
            pd.DataFrame: DataFrame containing the Positions Change Net data with additional 'Day_of_Year' column.
        """
        table_name = f"{market.lower().replace(' ', '_')}{table_suffix}_calc"

        # Select columns based on the report type
        if report_type == 'legacy':
            columns = 'report_date_as_yyyy_mm_dd, pct_change_noncomm_net_positions, pct_change_comm_net_positions'

            numeric_columns = ['report_date_as_yyyy_mm_dd', 'pct_change_noncomm_net_positions',
                               'pct_change_comm_net_positions']

        elif report_type == 'disaggregated':
            columns = ('report_date_as_yyyy_mm_dd, '
                       'pct_change_m_money_net_positions,'
                       'pct_change_prod_merc_net_positions,'
                       'pct_change_swap_net_positions')
            numeric_columns = [
                'report_date_as_yyyy_mm_dd',
                'pct_change_m_money_net_positions',
                'pct_change_prod_merc_net_positions',
                'pct_change_swap_net_positions']

        elif report_type == 'tff':
            columns = ('report_date_as_yyyy_mm_dd, '
                       'pct_change_lev_money_net_positions,'
                       'pct_change_asset_mgr_net_positions,'
                       'pct_change_dealer_net_positions')
            numeric_columns = [
                'report_date_as_yyyy_mm_dd',
                'pct_change_lev_money_net_positions',
                'pct_change_asset_mgr_net_positions',
                'pct_change_dealer_net_positions']

        else:
            raise ValueError(f"Unknown report type: {report_type}")


        query = f"""
        SELECT {columns}
        FROM {table_name}
        WHERE report_date_as_yyyy_mm_dd BETWEEN ? AND ?
        """
        params = (f'{year}-01-01', f'{year}-12-31')
        df = PositionsChangeNetDataFetcher.fetch_data(query, params)

        if not df.empty:
            df['report_date_as_yyyy_mm_dd'] = pd.to_datetime(df['report_date_as_yyyy_mm_dd'])
            # df['Day_of_Year'] = df['report_date_as_yyyy_mm_dd'].dt.dayofyear

            # Convert the relevant columns to numeric, based on report type
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            df['Date'] = df['report_date_as_yyyy_mm_dd']
            df.sort_values(by='Date', inplace=True)
        return df

class Index26WDataFetcher(BaseDataFetcher):
    """
    Data fetcher for 26-Week Index data.
    """

    @staticmethod
    def fetch_26w_index_data(market, year, table_suffix, report_type):
        """
        Fetch 26-Week Index data for a given market and year.

        Args:
            market (str): The market name.
            year (int): The year for which to fetch the 26-Week Index data.
            table_suffix (str): The table suffix indicating combined or futures-only.
            report_type (str): The report type, e.g., 'legacy' or 'disaggregated'.


        Returns:
            pd.DataFrame: DataFrame containing the 26-Week Index data with additional 'Day_of_Year' column.
        """
        table_name = f"{market.lower().replace(' ', '_')}{table_suffix}_calc"

        # Select columns based on the report type
        if report_type == 'legacy':
            columns = 'report_date_as_yyyy_mm_dd, noncomm_26w_index, comm_26w_index'

            numeric_columns = ['report_date_as_yyyy_mm_dd', 'noncomm_26w_index', 'comm_26w_index']

        elif report_type == 'disaggregated':
            columns = ('report_date_as_yyyy_mm_dd, '
                       'm_money_26w_index,'
                       'prod_merc_26w_index,'
                       'swap_26w_index')
            numeric_columns = [
                'report_date_as_yyyy_mm_dd',
                'm_money_26w_index',
                'prod_merc_26w_index',
                'swap_26w_index']

        elif report_type == 'tff':
            columns = ('report_date_as_yyyy_mm_dd, '
                       'lev_money_26w_index,'
                       'asset_mgr_26w_index,'
                       'dealer_26w_index')
            numeric_columns = [
                'report_date_as_yyyy_mm_dd',
                'lev_money_26w_index',
                'asset_mgr_26w_index',
                'dealer_26w_index']

        else:
            raise ValueError(f"Unknown report type: {report_type}")
        # print(f"TABLE: {table_name} COLUMNS: {columns}")
        query = f"""
        SELECT {columns}
        FROM {table_name}
        WHERE report_date_as_yyyy_mm_dd BETWEEN ? AND ?
        """
        params = (f'{year}-01-01', f'{year}-12-31')
        df = Index26WDataFetcher.fetch_data(query, params)

        if not df.empty:
            df['report_date_as_yyyy_mm_dd'] = pd.to_datetime(df['report_date_as_yyyy_mm_dd'])
            # df['Day_of_Year'] = df['report_date_as_yyyy_mm_dd'].dt.dayofyear

            # Convert the relevant columns to numeric, based on report type
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            df['Date'] = df['report_date_as_yyyy_mm_dd']
            df.sort_values(by='Date', inplace=True)
        return df


class CorrelationDataFetcher(BaseDataFetcher):
    """
    Data fetcher for correlation data.
    """

    @staticmethod
    def fetch_correlation_data(table_name):
        """
        Fetch correlation data from the specified table.

        Args:
            table_name (str): The table name (e.g., "correlation_180_days" or "correlation_15_years").

        Returns:
            pd.DataFrame: DataFrame containing the correlation data.
        """
        query = f"SELECT * FROM {table_name}"
        df = CorrelationDataFetcher.fetch_data(query)

        if df.empty:
            print(f"No data found in {table_name}")
        else:
            print(f"Fetched correlation data from {table_name}: {df.head()}")

        return df
