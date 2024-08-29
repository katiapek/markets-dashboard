import os
import sqlite3
import pandas as pd
from scripts.market_mapping import market_name_map

# Set the database path
db_path = os.getenv('DATABASE_PATH', '/Users/kamil/PycharmProjects/MarketsDashboard/app/data/markets_data.db')

class BaseDataFetcher:
    @staticmethod
    def fetch_data(query, params=None):
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
    @staticmethod
    def fetch_seasonal_data(market, years):
        table_name = f"{format_market_name(market)}_seasonality_{years}_years"
        query = f"SELECT * FROM {table_name} ORDER BY Day_of_Year ASC"
        return SeasonalDataFetcher.fetch_data(query)

class OHLCDataFetcher(BaseDataFetcher):
    @staticmethod
    def fetch_ohlc_data(market, year):
        table_name = format_market_name(market)
        print(f"Fetching OHLC from {table_name}")
        query = f"SELECT * FROM {table_name} WHERE Date BETWEEN ? AND ?"
        params = (f'{year}-01-01', f'{year}-12-31')
        df = OHLCDataFetcher.fetch_data(query, params)
        if not df.empty:
            df['Date'] = pd.to_datetime(df['Date'])
            df['Day_of_Year'] = df['Date'].dt.dayofyear
        return df

class OpenInterestDataFetcher(BaseDataFetcher):
    @staticmethod
    def fetch_open_interest_data(market, year):
        table_name = f"{market.lower().replace(' ', '_')}_cot_legacy_combined"
        query = f"""
        SELECT report_date_as_yyyy_mm_dd, open_interest_all
        FROM {table_name}
        WHERE report_date_as_yyyy_mm_dd BETWEEN ? AND ?
        """
        params = (f'{year}-01-01', f'{year}-12-31')
        df = OpenInterestDataFetcher.fetch_data(query, params)
        if not df.empty:
            df['report_date_as_yyyy_mm_dd'] = pd.to_datetime(df['report_date_as_yyyy_mm_dd'])
            df['Day_of_Year'] = df['report_date_as_yyyy_mm_dd'].dt.dayofyear
            df.sort_values(by='Day_of_Year', inplace=True)
        return df

class OpenInterestPercentagesFetcher(BaseDataFetcher):
    @staticmethod
    def fetch_open_interest_percentages(market, year):
        table_name = f"{market.lower().replace(' ', '_')}_cot_legacy_combined"
        query = f"""
        SELECT report_date_as_yyyy_mm_dd, 
               pct_of_oi_noncomm_long_all,
               pct_of_oi_noncomm_short_all,
               pct_of_oi_comm_long_all,
               pct_of_oi_comm_short_all
        FROM {table_name}
        WHERE report_date_as_yyyy_mm_dd BETWEEN ? AND ?
        """
        params = (f'{year}-01-01', f'{year}-12-31')
        df = OpenInterestPercentagesFetcher.fetch_data(query, params)
        if not df.empty:
            df['report_date_as_yyyy_mm_dd'] = pd.to_datetime(df['report_date_as_yyyy_mm_dd'])
            df['Day_of_Year'] = df['report_date_as_yyyy_mm_dd'].dt.dayofyear
            df['pct_of_oi_noncomm_long_all'] = pd.to_numeric(df['pct_of_oi_noncomm_long_all'], errors='coerce')
            df['pct_of_oi_noncomm_short_all'] = pd.to_numeric(df['pct_of_oi_noncomm_short_all'], errors='coerce')
            df['pct_of_oi_comm_long_all'] = pd.to_numeric(df['pct_of_oi_comm_long_all'], errors='coerce')
            df['pct_of_oi_comm_short_all'] = pd.to_numeric(df['pct_of_oi_comm_short_all'], errors='coerce')
            df.sort_values(by='Day_of_Year', inplace=True)
        return df

class PositionsChangeDataFetcher(BaseDataFetcher):
    @staticmethod
    def fetch_positions_change_data(market, year):
        table_name = f"{market.lower().replace(' ', '_')}_cot_legacy_combined_calc"
        query = f"""
        SELECT report_date_as_yyyy_mm_dd, 
               pct_change_noncomm_long,
               pct_change_noncomm_short,
               pct_change_comm_long,
               pct_change_comm_short
        FROM {table_name}
        WHERE report_date_as_yyyy_mm_dd BETWEEN ? AND ?
        """
        params = (f'{year}-01-01', f'{year}-12-31')
        df = PositionsChangeDataFetcher.fetch_data(query, params)
        if not df.empty:
            df['report_date_as_yyyy_mm_dd'] = pd.to_datetime(df['report_date_as_yyyy_mm_dd'])
            df['Day_of_Year'] = df['report_date_as_yyyy_mm_dd'].dt.dayofyear
            df['pct_change_noncomm_long'] = pd.to_numeric(df['pct_change_noncomm_long'], errors='coerce')
            df['pct_change_noncomm_short'] = pd.to_numeric(df['pct_change_noncomm_short'], errors='coerce')
            df['pct_change_comm_long'] = pd.to_numeric(df['pct_change_comm_long'], errors='coerce')
            df['pct_change_comm_short'] = pd.to_numeric(df['pct_change_comm_short'], errors='coerce')
            df.sort_values(by='Day_of_Year', inplace=True)
        return df

class NetPositionsDataFetcher(BaseDataFetcher):
    @staticmethod
    def fetch_net_positions_data(market, year):
        table_name = f"{market.lower().replace(' ', '_')}_cot_legacy_combined_calc"
        query = f"""
        SELECT report_date_as_yyyy_mm_dd, 
               noncomm_net_positions,
               comm_net_positions
        FROM {table_name}
        WHERE report_date_as_yyyy_mm_dd BETWEEN ? AND ?
        """
        params = (f'{year}-01-01', f'{year}-12-31')
        df = NetPositionsDataFetcher.fetch_data(query, params)
        if not df.empty:
            df['report_date_as_yyyy_mm_dd'] = pd.to_datetime(df['report_date_as_yyyy_mm_dd'])
            df['Day_of_Year'] = df['report_date_as_yyyy_mm_dd'].dt.dayofyear
            df['noncomm_net_positions'] = pd.to_numeric(df['noncomm_net_positions'], errors='coerce')
            df['comm_net_positions'] = pd.to_numeric(df['comm_net_positions'], errors='coerce')
            df.sort_values(by='Day_of_Year', inplace=True)
        return df

class PositionsChangeNetDataFetcher(BaseDataFetcher):
    @staticmethod
    def fetch_positions_change_net_data(market, year):
        table_name = f"{market.lower().replace(' ', '_')}_cot_legacy_combined_calc"
        query = f"""
        SELECT report_date_as_yyyy_mm_dd, 
               pct_change_noncomm_net_positions,
               pct_change_comm_net_positions
        FROM {table_name}
        WHERE report_date_as_yyyy_mm_dd BETWEEN ? AND ?
        """
        params = (f'{year}-01-01', f'{year}-12-31')
        df = PositionsChangeNetDataFetcher.fetch_data(query, params)
        if not df.empty:
            df['report_date_as_yyyy_mm_dd'] = pd.to_datetime(df['report_date_as_yyyy_mm_dd'])
            df['Day_of_Year'] = df['report_date_as_yyyy_mm_dd'].dt.dayofyear
            df['pct_change_noncomm_net_positions'] = pd.to_numeric(df['pct_change_noncomm_net_positions'], errors='coerce')
            df['pct_change_comm_net_positions'] = pd.to_numeric(df['pct_change_comm_net_positions'], errors='coerce')
            df.sort_values(by='Day_of_Year', inplace=True)
        return df

class Index26WDataFetcher(BaseDataFetcher):
    @staticmethod
    def fetch_26w_index_data(market, year):
        table_name = f"{market.lower().replace(' ', '_')}_cot_legacy_combined_calc"
        query = f"""
        SELECT report_date_as_yyyy_mm_dd, 
               noncomm_26w_index,
               comm_26w_index
        FROM {table_name}
        WHERE report_date_as_yyyy_mm_dd BETWEEN ? AND ?
        """
        params = (f'{year}-01-01', f'{year}-12-31')
        df = Index26WDataFetcher.fetch_data(query, params)
        if not df.empty:
            df['report_date_as_yyyy_mm_dd'] = pd.to_datetime(df['report_date_as_yyyy_mm_dd'])
            df['Day_of_Year'] = df['report_date_as_yyyy_mm_dd'].dt.dayofyear
            df['noncomm_26w_index'] = pd.to_numeric(df['noncomm_26w_index'], errors='coerce')
            df['comm_26w_index'] = pd.to_numeric(df['comm_26w_index'], errors='coerce')
            df.sort_values(by='Day_of_Year', inplace=True)
        return df

def format_market_name(market_name):
    return market_name_map.get(market_name, market_name.lower().replace(' ', '_') + '_ohlc')
