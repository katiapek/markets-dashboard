# data_fetchers.py

import pandas as pd
from scripts.config import db_path_str
from datetime import timedelta
from dateutil import parser
from functools import lru_cache
from sqlalchemy import create_engine, text
import os
from urllib.parse import urlparse
import re

db_url = os.environ.get(db_path_str).replace("postgres://", "postgresql+psycopg2://", 1)
engine = create_engine(db_url)

@lru_cache(maxsize=10)
def fetch_ohlc_data_cached(market, start_date, end_date):
    """
    Fetches and caches OHLC data for a specific market and year.
    """
    # start_date = f"{year}-01-01"
    # end_date = f"{year}-12-31"
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
    ohlc_columns = ['open', 'high', 'low', 'close']

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
            params (dict, optional): The parameters for the SQL query as a dictionary.

        Returns:
            pd.DataFrame: DataFrame containing the fetched data.

        Raises:
            ValueError: If parameters are not in dictionary format or invalid table/column names
        """
        from sqlalchemy import bindparam

        # Validate parameters
        if params and not isinstance(params, dict):
            raise ValueError("Query parameters must be in dictionary format")

        # Validate table/column names in query
        allowed_tables = {
            '_ohlc', '_ohlc_seasonality_5_years', '_ohlc_seasonality_10_years',
            '_cot_disaggregated_combined', '_cot_legacy_combined', '_cot_tff_combined',
            '_cot_disaggregated_combined_calc', '_cot_legacy_combined_calc', '_cot_tff_combined_calc'
        }
        
        # Check for valid table patterns
        table_pattern = re.compile(r'^([a-z0-9_]+(_ohlc|_cot_(disaggregated|legacy|tff)_(combined|calc))|correlation_\d+_(days|years))$')
        if not table_pattern.search(query.lower()):
            raise ValueError("Invalid table name pattern in query")

        # Fetch data using SQLAlchemy Engine with parameter binding
        with engine.connect() as connection:
            try:
                stmt = text(query)
                if params:
                    stmt = stmt.bindparams(*[bindparam(key, value) for key, value in params.items()])
                df = pd.read_sql(stmt, connection)
            except Exception as e:
                raise RuntimeError(f"Database error: {str(e)}") from e
                
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
            pd.DataFrame: DataFrame containing the seasonal data with an additional 'date' column.
        """
        # Validate and construct table name
        base_name = market.lower().replace(' ', '_')
        table_name = f"{base_name}_ohlc_seasonality_{years}_years"
        
        # Validate table name pattern
        if not re.match(r'^[a-z0-9_]+_ohlc_seasonality_\d+_years$', table_name):
            raise ValueError(f"Invalid table name format: {table_name}")
            
        query = f"SELECT * FROM {table_name} ORDER BY day_of_year ASC"
        df = SeasonalDataFetcher.fetch_data(query)

        if not df.empty:
            # Ensure Day_of_Year is treated as an integer
            df['day_of_year'] = df['day_of_year'].astype(int)

            # Creating base date string for January 1st of the current year
            base_date = parser.parse(f"{current_year}-01-01")

            # Convert Day_of_Year to actual dates within the current year
            df['date'] = df['day_of_year'].apply(lambda x: (base_date + timedelta(days=x - 1)).strftime("%Y-%m-%d"))

            # Convert 'date' column to datetime format explicitly
            df['date'] = pd.to_datetime(df['date'], format="%Y-%m-%d")

            # Sort by the new Date column
            df.sort_values(by='date', inplace=True)

        return df


class OHLCDataFetcher(BaseDataFetcher):
    """
    Data fetcher for OHLC (Open, High, Low, Close) data.
    """

    @staticmethod
    def fetch_ohlc_data(market, year):
        table_name = f"{market.lower().replace(' ', '_')}_ohlc"
        print(f"Fetching OHLC from table: {table_name} for year: {year}")

        query = f"SELECT * FROM {table_name} WHERE Date BETWEEN %s AND %s"
        params = (f'{year}-01-01 00:00:00', f'{year}-12-31 23:59:59')
        print(f"Running query: {query} with params: {params}")

        df = OHLCDataFetcher.fetch_data(query, params)

        if df.empty:
            print(f"No data found for {market} in {year}")
        else:
            df['date'] = pd.to_datetime(df['date'], format="%Y-%m-%d %H:%M:%S")
            df['day_of_year'] = df['date'].dt.dayofyear
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

        query = f"SELECT * FROM {table_name} WHERE date BETWEEN :start_date AND :end_date"
        params = {'start_date': f'{start_date} 00:00:00', 'end_date': f'{end_date} 23:59:59'}

        df = OHLCDataFetcher.fetch_data(query, params)

        if not df.empty:
            # Parse the 'date' column with the appropriate format
            df['date'] = pd.to_datetime(df['date'], format="%Y-%m-%d %H:%M:%S")
            df['day_of_year'] = df['date'].dt.dayofyear

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

        columns = 'report_date_as_yyyy_mm_dd, open_interest_all'

        query = f"""
        SELECT {columns}
        FROM {table_name}
        WHERE report_date_as_yyyy_mm_dd BETWEEN :start_date AND :end_date
        """
        params = {'start_date': f'{year}-01-01', 'end_date': f'{year+1}-01-01'}
        df = OpenInterestDataFetcher.fetch_data(query, params)
        if not df.empty:
            df['report_date_as_yyyy_mm_dd'] = pd.to_datetime(df['report_date_as_yyyy_mm_dd'], format="%Y-%m-%d %H:%M:%S")
            df['date'] = df['report_date_as_yyyy_mm_dd']
            df.sort_values(by='date', inplace=True)
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
        WHERE report_date_as_yyyy_mm_dd BETWEEN :start_date AND :end_date
        """
        params = {'start_date': f'{year}-01-01', 'end_date': f'{year+1}-01-01'}
        df = OpenInterestPercentagesFetcher.fetch_data(query, params)

        if not df.empty:
            df['report_date_as_yyyy_mm_dd'] = pd.to_datetime(df['report_date_as_yyyy_mm_dd'])
            # df['Day_of_Year'] = df['report_date_as_yyyy_mm_dd'].dt.dayofyear

            # Convert numeric columns more efficiently
            df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors='coerce')

            df['date'] = df['report_date_as_yyyy_mm_dd']
            df.sort_values(by='date', inplace=True)

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
        WHERE report_date_as_yyyy_mm_dd BETWEEN :start_date AND :end_date
        """
        params = {'start_date': f'{year}-01-01', 'end_date': f'{year+1}-01-01'}
        df = PositionsChangeDataFetcher.fetch_data(query, params)

        if not df.empty:
            df['report_date_as_yyyy_mm_dd'] = pd.to_datetime(df['report_date_as_yyyy_mm_dd'])

            # Convert the relevant columns to numeric, based on report type
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            df['date'] = df['report_date_as_yyyy_mm_dd']
            df.sort_values(by='date', inplace=True)
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
        WHERE report_date_as_yyyy_mm_dd BETWEEN :start_date AND :end_date
        """
        params = {'start_date': f'{year}-01-01', 'end_date': f'{year+1}-01-01'}
        df = NetPositionsDataFetcher.fetch_data(query, params)

        if not df.empty:
            df['report_date_as_yyyy_mm_dd'] = pd.to_datetime(df['report_date_as_yyyy_mm_dd'])
            # df['Day_of_Year'] = df['report_date_as_yyyy_mm_dd'].dt.dayofyear

            # Convert the relevant columns to numeric, based on report type
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            df['date'] = df['report_date_as_yyyy_mm_dd']
            df.sort_values(by='date', inplace=True)
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
        WHERE report_date_as_yyyy_mm_dd BETWEEN :start_date AND :end_date
        """
        params = {'start_date': f'{year}-01-01', 'end_date': f'{year+1}-01-01'}
        df = PositionsChangeNetDataFetcher.fetch_data(query, params)

        if not df.empty:
            df['report_date_as_yyyy_mm_dd'] = pd.to_datetime(df['report_date_as_yyyy_mm_dd'])
            # df['Day_of_Year'] = df['report_date_as_yyyy_mm_dd'].dt.dayofyear

            # Convert the relevant columns to numeric, based on report type
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            df['date'] = df['report_date_as_yyyy_mm_dd']
            df.sort_values(by='date', inplace=True)
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

        query = f"""
        SELECT {columns}
        FROM {table_name}
        WHERE report_date_as_yyyy_mm_dd BETWEEN :start_date AND :end_date
        """
        params = {'start_date': f'{year}-01-01', 'end_date': f'{year+1}-01-01'}
        df = Index26WDataFetcher.fetch_data(query, params)

        if not df.empty:
            df['report_date_as_yyyy_mm_dd'] = pd.to_datetime(df['report_date_as_yyyy_mm_dd'])

            # Convert the relevant columns to numeric, based on report type
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            df['date'] = df['report_date_as_yyyy_mm_dd']
            df.sort_values(by='date', inplace=True)
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
