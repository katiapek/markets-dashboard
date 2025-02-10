# data_fetchers.py

import pandas as pd
from app.config import db_path_str
from enum import Enum
from datetime import timedelta
from dateutil import parser
from functools import lru_cache
from sqlalchemy import create_engine, text
import os
from urllib.parse import urlparse
import re

class TableType(Enum):
    OHLC = "ohlc"
    OHLC_SEASONALITY = "ohlc_seasonality"
    COT = "cot"
    CORRELATION = "correlation"

class TableNameFactory:
    """Centralized factory for creating and validating table names"""
    
    @staticmethod
    def get_ohlc_table(market: str) -> str:
        """Generate OHLC table name for a market"""
        base_name = market.lower().replace(' ', '_')
        return f"{base_name}_ohlc"
    
    @staticmethod
    def get_seasonality_table(market: str, years: int) -> str:
        """Generate seasonality table name"""
        base_name = market.lower().replace(' ', '_')
        return f"{base_name}_ohlc_seasonality_{years}_years"
    
    @staticmethod
    def get_cot_table(market: str, report_type: str, table_suffix: str) -> str:
        """Generate COT table name"""
        base_name = market.lower().replace(' ', '_')
        return f"{base_name}_cot_{report_type}_{table_suffix}"
    
    @staticmethod
    def get_correlation_table(timeframe: str, unit: str) -> str:
        """Generate correlation table name"""
        return f"correlation_{timeframe}_{unit}"
    
    @classmethod
    def validate_table_name(cls, table_name: str) -> bool:
        """Validate table name against known patterns"""
        patterns = [
            r'^[a-z0-9_]+_ohlc$',
            r'^[a-z0-9_]+_ohlc_seasonality_\d+_years$',
            r'^[a-z0-9_]+_cot_(disaggregated|legacy|tff)_(combined|futures_only)(_calc)?$',
            r'^correlation_\d+_(days|years)$'
        ]
        return any(re.match(pattern, table_name) for pattern in patterns)

db_url = os.environ.get(db_path_str).replace("postgres://", "postgresql+psycopg2://", 1)
engine = create_engine(db_url)

@lru_cache(maxsize=10)
def fetch_ohlc_data_cached(market, start_date, end_date):
    """
    Fetches and caches OHLC data for a specific market and year.
    """
    return OHLCDataFetcher.fetch_ohlc_data_by_range(market, start_date, end_date)

@lru_cache(maxsize=10)
def fetch_active_subplot_data(market, year, subplot, table_suffix, report_type):
    config = ReportDataFetcher.CONFIG_REGISTRY.get(subplot, {}).get(report_type)
    if not config:
        return pd.DataFrame()
        
    fetcher = ReportDataFetcher(config)
    return fetcher.fetch(market, year, table_suffix, report_type)

@lru_cache(maxsize=5)
def fetch_seasonal_data_cached(market, years, base_year):
    return SeasonalDataFetcher.fetch_seasonal_data(market, years, base_year)

class BaseDataFetcher:
    """
    Base class for fetching data from an SQLite database.
    """

    @staticmethod
    def fetch_active_subplot_data(market, year, subplot, table_suffix, report_type):
        """Fetch subplot data from cache or source"""
        config = ReportDataFetcher.CONFIG_REGISTRY.get(subplot, {}).get(report_type)
        if not config:
            return pd.DataFrame()
            
        fetcher = ReportDataFetcher(config)
        return fetcher.fetch(market, year, table_suffix, report_type)

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

        # Validate table name pattern using helper method
        BaseDataFetcher.validate_table_name_from_query(query.lower())

        # Fetch data using SQLAlchemy Engine with parameter binding
        with engine.connect() as connection:
            try:
                stmt = text(query)
                if params:
                    stmt = stmt.bindparams(*[bindparam(key, value) for key, value in params.items()])
                df = pd.read_sql(stmt, connection)
            except Exception as e:
                raise RuntimeError(f"Database error: {str(e)}") from e

        # Apply common processing pipeline
        df = BaseDataFetcher.common_processing(df)

        return df

    @staticmethod
    def common_processing(df):
        """
        Apply common processing steps to the fetched DataFrame.

        Args:
            df (pd.DataFrame): The DataFrame to process.

        Returns:
            pd.DataFrame: The processed DataFrame.
        """
        if df.empty:
            print("Fetched DataFrame is empty.")
            return df

        # Example: Parse date columns if they exist
        date_columns = ['date', 'report_date_as_yyyy_mm_dd']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # Example: Sort by date if 'date' column exists
        if 'date' in df.columns:
            df.sort_values(by='date', inplace=True)

        if 'report_date_as_yyyy_mm_dd' in df.columns:
            df.sort_values(by='report_date_as_yyyy_mm_dd', inplace=True)

        # Example: Clean OHLC data if relevant columns exist
        ohlc_columns = ['open', 'high', 'low', 'close']
        for col in ohlc_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '').astype(float)

        # Additional common processing steps can be added here

        return df

    @staticmethod
    def validate_table_name(table_name):
        """Validate table name against safe pattern"""
        table_pattern = re.compile(
            r'^[a-z0-9_]+_ohlc$|'  # Base OHLC tables
            r'^[a-z0-9_]+_ohlc_seasonality_\d+_years$|'  # Seasonality tables
            r'^[a-z0-9_]+_cot_(disaggregated|legacy|tff)_(combined|futures_only)(_calc)?$|'  # COT tables
            r'^correlation_\d+_(days|years)$'  # Correlation tables
        )

        if not table_pattern.match(table_name):
            raise ValueError(f"Invalid table name: {table_name}")
        return True

    @staticmethod
    def validate_table_name_from_query(query):
        """Extract and validate table names from SQL query"""
        table_pattern = re.compile(r'\b(from|join)\s+([a-z0-9_]+)', re.IGNORECASE)
        matches = table_pattern.findall(query)
        for _, table in matches:
            BaseDataFetcher.validate_table_name(table)


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
        # Construct and validate table name
        table_name = TableNameFactory.get_seasonality_table(market, years)
        BaseDataFetcher.validate_table_name(table_name)
        
        # Use safe query construction
        query = "SELECT * FROM {} ORDER BY day_of_year ASC".format(table_name)
        df = SeasonalDataFetcher.fetch_data(query)

        if not df.empty:
            # Ensure Day_of_Year is treated as an integer
            df['day_of_year'] = df['day_of_year'].astype(int)

            # Creating base date string for January 1st of the current year
            base_date = parser.parse(f"{current_year}-01-01")

            # Convert Day_of_Year to actual dates within the current year
            df['date'] = df['day_of_year'].apply(lambda x: (base_date + timedelta(days=x - 1)).strftime("%Y-%m-%d"))

            # The following steps are now handled by the common_processing pipeline
            # df['date'] = pd.to_datetime(df['date'], format="%Y-%m-%d")
            # df.sort_values(by='date', inplace=True)

        return df


class OHLCDataFetcher(BaseDataFetcher):
    """
    Data fetcher for OHLC (Open, High, Low, Close) data.
    """

    @staticmethod
    def fetch_ohlc_data(market, year):
        table_name = TableNameFactory.get_ohlc_table(market)
        print(f"Fetching OHLC from table: {table_name} for year: {year}")

        BaseDataFetcher.validate_table_name(table_name)
        query = "SELECT * FROM {} WHERE Date BETWEEN :start_date AND :end_date".format(table_name)
        params = {
            'start_date': f'{year}-01-01 00:00:00',
            'end_date': f'{year}-12-31 23:59:59'
        }
        print(f"Running query: {query} with params: {params}")

        df = OHLCDataFetcher.fetch_data(query, params)

        # The following steps are now handled by the common_processing pipeline
        # if df.empty:
        #     print(f"No data found for {market} in {year}")
        # else:
        #     df['date'] = pd.to_datetime(df['date'], format="%Y-%m-%d %H:%M:%S")
        #     df['day_of_year'] = df['date'].dt.dayofyear
        #     print(f"Fetched data for {year}: {df.head()}")
        # df = clean_ohlc_data(df)

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

        return df


class ReportDataFetcher(BaseDataFetcher):
    """
    Generic data fetcher for report data with configurable metrics.
    """
    CONFIG_REGISTRY = {
        # Metric Type: {Report Type: {config}}
        'Open Interest': {
            'legacy': {'columns': 'report_date_as_yyyy_mm_dd, open_interest_all'},
            'disaggregated': {'columns': 'report_date_as_yyyy_mm_dd, open_interest_all'},
            'tff': {'columns': 'report_date_as_yyyy_mm_dd, open_interest_all'}
        },
        'OI Percentages': {
            'legacy': {
                'columns': ('report_date_as_yyyy_mm_dd, pct_of_oi_noncomm_long_all, '
                            'pct_of_oi_noncomm_short_all, pct_of_oi_comm_long_all, '
                            'pct_of_oi_comm_short_all'),
                'numeric_cols': [
                    'pct_of_oi_noncomm_long_all', 'pct_of_oi_noncomm_short_all',
                    'pct_of_oi_comm_long_all', 'pct_of_oi_comm_short_all'
                ]
            },
            'disaggregated': {
                'columns': ('report_date_as_yyyy_mm_dd, pct_of_oi_m_money_long_all, '
                            'pct_of_oi_m_money_short_all, pct_of_oi_prod_merc_long, '
                            'pct_of_oi_prod_merc_short, pct_of_oi_swap_long_all, '
                            'pct_of_oi_swap_short_all'),
                'numeric_cols': [
                    'pct_of_oi_m_money_long_all', 'pct_of_oi_m_money_short_all',
                    'pct_of_oi_prod_merc_long', 'pct_of_oi_prod_merc_short',
                    'pct_of_oi_swap_long_all', 'pct_of_oi_swap_short_all'
                ]
            },
            'tff': {
                'columns': ('report_date_as_yyyy_mm_dd, pct_of_oi_lev_money_long, '
                            'pct_of_oi_lev_money_short, pct_of_oi_asset_mgr_long, '
                            'pct_of_oi_asset_mgr_short, pct_of_oi_dealer_long_all, '
                            'pct_of_oi_dealer_short_all'),
                'numeric_cols': [
                    'pct_of_oi_lev_money_long', 'pct_of_oi_lev_money_short',
                    'pct_of_oi_asset_mgr_long', 'pct_of_oi_asset_mgr_short',
                    'pct_of_oi_dealer_long_all', 'pct_of_oi_dealer_short_all'
                ]
            }
        },
        'Positions Change': {
            'legacy': {
                'columns': ('report_date_as_yyyy_mm_dd, pct_change_noncomm_long, '
                            'pct_change_noncomm_short, pct_change_comm_long, '
                            'pct_change_comm_short'),
                'numeric_cols': [
                    'pct_change_noncomm_long', 'pct_change_noncomm_short',
                    'pct_change_comm_long', 'pct_change_comm_short'
                ]
            },
            'disaggregated': {
                'columns': ('report_date_as_yyyy_mm_dd, pct_change_m_money_long, '
                            'pct_change_m_money_short, pct_change_prod_merc_long, '
                            'pct_change_prod_merc_short, pct_change_swap_long, '
                            'pct_change_swap_short'),
                'numeric_cols': [
                    'pct_change_m_money_long', 'pct_change_m_money_short',
                    'pct_change_prod_merc_long', 'pct_change_prod_merc_short',
                    'pct_change_swap_long', 'pct_change_swap_short'
                ]
            },
            'tff': {
                'columns': ('report_date_as_yyyy_mm_dd, pct_change_lev_money_long, '
                            'pct_change_lev_money_short, pct_change_asset_mgr_long, '
                            'pct_change_asset_mgr_short, pct_change_dealer_long, '
                            'pct_change_dealer_short'),
                'numeric_cols': [
                    'pct_change_lev_money_long', 'pct_change_lev_money_short',
                    'pct_change_asset_mgr_long', 'pct_change_asset_mgr_short',
                    'pct_change_dealer_long', 'pct_change_dealer_short'
                ]
            }
        },

        'Net Positions': {
            'legacy': {
                'columns': 'report_date_as_yyyy_mm_dd, noncomm_net_positions, comm_net_positions',
                'numeric_cols': ['report_date_as_yyyy_mm_dd', 'noncomm_net_positions', 'comm_net_positions']
            },
            'disaggregated': {
                'columns': ('report_date_as_yyyy_mm_dd, '
                            'm_money_net_positions,'
                            'prod_merc_net_positions,'
                            'swap_net_positions'),
                'numeric_cols': [
                    'report_date_as_yyyy_mm_dd',
                    'm_money_net_positions',
                    'prod_merc_net_positions',
                    'swap_net_positions']
            },
            'tff': {
                'columns': ('report_date_as_yyyy_mm_dd, '
                            'lev_money_net_positions,'
                            'asset_mgr_net_positions,'
                            'dealer_net_positions'),
                'numeric_cols': [
                    'report_date_as_yyyy_mm_dd',
                    'lev_money_net_positions',
                    'asset_mgr_net_positions',
                    'dealer_net_positions']
            }
        },

        'Net Positions Change': {
            'legacy': {
                'columns': 'report_date_as_yyyy_mm_dd, pct_change_noncomm_net_positions, pct_change_comm_net_positions',
                'numeric_cols': ['report_date_as_yyyy_mm_dd', 'pct_change_noncomm_net_positions',
                                 'pct_change_comm_net_positions']
            },
            'disaggregated': {
                'columns': ('report_date_as_yyyy_mm_dd, '
                            'pct_change_m_money_net_positions,'
                            'pct_change_prod_merc_net_positions,'
                            'pct_change_swap_net_positions'),
                'numeric_cols': [
                    'report_date_as_yyyy_mm_dd',
                    'pct_change_m_money_net_positions',
                    'pct_change_prod_merc_net_positions',
                    'pct_change_swap_net_positions']
            },
            'tff': {
                'columns': ('report_date_as_yyyy_mm_dd, '
                            'pct_change_lev_money_net_positions,'
                            'pct_change_asset_mgr_net_positions,'
                            'pct_change_dealer_net_positions'),
                'numeric_cols': [
                    'report_date_as_yyyy_mm_dd',
                    'pct_change_lev_money_net_positions',
                    'pct_change_asset_mgr_net_positions',
                    'pct_change_dealer_net_positions']
            }
        },

        '26W Index': {
            'legacy': {
                'columns': 'report_date_as_yyyy_mm_dd, noncomm_26w_index, comm_26w_index',
                'numeric_cols': ['report_date_as_yyyy_mm_dd', 'noncomm_26w_index', 'comm_26w_index']
            },
            'disaggregated': {
                'columns': ('report_date_as_yyyy_mm_dd, '
                            'm_money_26w_index,'
                            'prod_merc_26w_index,'
                            'swap_26w_index'),
                'numeric_cols': [
                    'report_date_as_yyyy_mm_dd',
                    'm_money_26w_index',
                    'prod_merc_26w_index',
                    'swap_26w_index']
            },
            'tff': {
                'columns': ('report_date_as_yyyy_mm_dd, '
                            'lev_money_26w_index,'
                            'asset_mgr_26w_index,'
                            'dealer_26w_index'),
                'numeric_cols': [
                    'report_date_as_yyyy_mm_dd',
                    'lev_money_26w_index',
                    'asset_mgr_26w_index',
                    'dealer_26w_index']
            }
        },
    }

    def __init__(self, config):
        self.config = config

    def fetch(self, market, year, table_suffix, report_type):
        """
        Generic fetch method that uses configuration to determine query parameters.
        """
        table_name = TableNameFactory.get_cot_table(market, report_type, table_suffix)
        
        query = f"""
        SELECT {self.config['columns']}
        FROM {table_name}
        WHERE report_date_as_yyyy_mm_dd BETWEEN :start_date AND :end_date
        """
        params = {'start_date': f'{year}-01-01', 'end_date': f'{year+1}-01-01'}
        df = self.fetch_data(query, params)

        if not df.empty:
            # Ensure 'date' column exists by mapping 'report_date_as_yyyy_mm_dd' to 'date'
            if 'report_date_as_yyyy_mm_dd' in df.columns:
                df['date'] = df['report_date_as_yyyy_mm_dd']
            else:
                print("Warning: 'report_date_as_yyyy_mm_dd' column missing; 'date' column not created.")

            # Additional processing specific to ReportDataFetcher can be added here if needed

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
