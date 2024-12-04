# config.py
db_path_str = '/Users/kamil/PycharmProjects/MarketsDashboard/app/data/markets_data.db'

COLORS = {
    'open_interest': 'orange',
    'comm_long': 'Red',
    'comm_short': 'Salmon',
    'noncomm_long': 'Blue',
    'noncomm_short': 'CornflowerBlue',
    'other_long': 'Green',
    'other_short': 'Lightgreen',
    'seasonality_colors': {
        15: 'CornFlowerBlue',
        35: 'Salmon',
    },
}

DEFAULT_MARKET = 'SP 500'
DEFAULT_YEAR = 2024

# Market tickers used by yfinance
market_tickers = {
    'Day 30 Fed Fund': 'ZQ=F',
    'Note 2Y': 'ZT=F',
    'Note 5Y': 'ZF=F',
    'Note 10Y': 'ZN=F',
    'Ultra 10Y Note': 'TN=F',
    'US Treasury Bond': 'ZB=F',

    'VIX': '^VIX',
    'SP 500': 'ES=F',
    'Nasdaq 100': 'NQ=F',
    'Russell 2000': 'RTY=F',
    'Dow Jones': 'YM=F',

    'US Dollar Index': 'DX-Y.NYB',
    'Euro FX': '6E=F',
    'Australian Dollar': '6A=F',
    'New Zealand Dollar': '6N=F',
    'British Pound': '6B=F',
    'Canadian Dollar': '6C=F',
    'Japanese Yen': '6J=F',
    'Swiss Franc': '6S=F',
    'Mexican Peso': '6M=F',
    'Brazilian Real': '6L=F',
    'Bitcoin': 'BTC=F',
    'Ethereum': 'ETH=F',

    'Crude Oil': 'CL=F',
    'Henry Hub Natural Gas': 'NG=F',
    'NY Harbor ULSD': 'HO=F',
    'RBOB Gasoline': 'RB=F',

    'Wheat': 'ZW=F',
    'KC HRW Wheat': 'KE=F',
    'Corn': 'ZC=F',
    'Soybeans': 'ZS=F',
    'Soybean Oil': 'ZL=F',
    'Soybean Meal': 'ZM=F',
    'Cocoa': 'CC=F',
    'Coffee': 'KC=F',

    'Live Cattle': 'LE=F',
    'Feeder Cattle': 'GF=F',
    'Lean Hog': 'HE=F',


    'Gold': 'GC=F',
    'Silver': 'SI=F',
    'Copper': 'HG=F',
    # 'Platinum': 'PL=F',


}

# Market codes for COT data
market_codes = {
    'Day 30 Fed Fund': '045601',
    'Note 2Y': '042601',
    'Note 5Y': '044601',
    'Note 10Y': '043602',
    'Ultra 10Y Note': '043607',
    'US Treasury Bond': '020601',

    'VIX': '1170E1',
    'SP 500': '13874A',
    'Nasdaq 100': '209742',
    'Russell 2000': '239742',
    'Dow Jones': '124603',

    'US Dollar Index': '098662',
    'Euro FX': '099741',
    'Australian Dollar': '232741',
    'New Zealand Dollar': '112741',
    'British Pound': '096742',
    'Canadian Dollar': '090741',
    'Japanese Yen': '097741',
    'Swiss Franc': '092741',
    'Mexican Peso': '095741',
    'Brazilian Real': '102741',
    'Bitcoin': '133741',
    'Ethereum': '146021',

    'Crude Oil': '067651',
    'Henry Hub Natural Gas': '023651',
    'NY Harbor ULSD': '022651',
    'RBOB Gasoline': '111659',

    'Wheat': '001602',
    'KC HRW Wheat': '001612',
    'Corn': '002602',
    'Soybeans': '005602',
    'Soybean Oil': '007601',
    'Soybean Meal': '026603',
    'Cocoa': '073732',
    'Coffee': '083731',

    'Live Cattle': '057642',
    'Feeder Cattle': '061641',
    'Lean Hog': '054642',

    'Gold': '088691',
    'Silver': '084691',
    'Copper': '085692',
    'Platinum': '076651',
}

TRACE_CONFIG = {
    'Open Interest': {
        'legacy': {
            'columns': ['open_interest_all'],
            'names': ['Open Interest'],
            'colors': ['open_interest'],
        },
        'disaggregated': {
            'columns': ['open_interest_all'],
            'names': ['Open Interest'],
            'colors': ['open_interest'],
        },
        'tff': {
            'columns': ['open_interest_all'],
            'names': ['Open Interest'],
            'colors': ['open_interest'],
        },
    },
    'OI Percentages': {
        'legacy': {
            'columns': ['pct_of_oi_noncomm_long_all', 'pct_of_oi_noncomm_short_all',
                        'pct_of_oi_comm_long_all', 'pct_of_oi_comm_short_all'],
            'names': ['% of OI Non-Commercials Long', '% of OI Non-Commercials Short',
                      '% of OI Commercials Long', '% of OI Commercials Short'],
            'colors': ['noncomm_long', 'noncomm_short', 'comm_long', 'comm_short'],
        },
        'disaggregated': {
            'columns': ['pct_of_oi_m_money_long_all', 'pct_of_oi_m_money_short_all',
                        'pct_of_oi_prod_merc_long', 'pct_of_oi_prod_merc_short',
                        'pct_of_oi_swap_long_all', 'pct_of_oi_swap_short_all'],
            'names': ['% of OI Managed Money Long', '% of OI Managed Money Short',
                      '% of OI Producers/Merchants Long', '% of OI Producers/Merchants Short',
                      '% of OI Swap Dealers Long', '% of OI Swap Dealers Short'],
            'colors': ['noncomm_long', 'noncomm_short', 'comm_long', 'comm_short','other_long', 'other_short'],
        },
        'tff': {
            'columns': ['pct_of_oi_lev_money_long', 'pct_of_oi_lev_money_short',
                        'pct_of_oi_asset_mgr_long', 'pct_of_oi_asset_mgr_short',
                        'pct_of_oi_dealer_long_all', 'pct_of_oi_dealer_short_all'],
            'names': ['% of OI Leveraged Money Long', '% of OI Leveraged Money Short',
                      '% of OI Asset Managers Long', '% of OI Asset Managers Short',
                      '% of OI Dealers Long', '% of OI Dealers Short'],
            'colors': ['noncomm_long', 'noncomm_short', 'comm_long', 'comm_short', 'other_long', 'other_short'],
        },
    },
    'Net Positions': {
        'legacy': {
            'columns': ['noncomm_net_positions', 'comm_net_positions'],
            'names': ['Net Positions Non-Commercials', 'Net Positions Commercials'],
            'colors': ['noncomm_long', 'comm_long'],
        },
        'disaggregated': {
            'columns': ['m_money_net_positions', 'prod_merc_net_positions',
                        'swap_net_positions'],
            'names': ['Net Positions Managed Money', 'Net Positions Producers / Merchants',
                      'Net Positions Swap Dealers'],
            'colors': ['noncomm_long', 'comm_long', 'other_long'],
        },
        'tff': {
            'columns': ['lev_money_net_positions', 'asset_mgr_net_positions',
                        'dealer_net_positions'],
            'names': ['Net Positions Managed Money', 'Net Positions Asset Mgrs',
                      'Net Positions Dealers'],
            'colors': ['noncomm_long','comm_long','other_long'],
        },
    },
    '26W Index': {
        'legacy': {
            'columns': ['noncomm_26w_index', 'comm_26w_index'],
            'names': ['Non-Commercials 26W Index', 'Commercials 26W Index'],
            'colors': ['noncomm_long', 'comm_long'],
        },
        'disaggregated': {
            'columns': ['m_money_26w_index', 'prod_merc_26w_index',
                        'swap_26w_index'],
            'names': ['Managed Money 26W Index', 'Producers / Merchants 26W Index',
                      'Swap Dealers 26W Index'],
            'colors': ['noncomm_long', 'comm_long', 'other_long'],
        },
        'tff': {
            'columns': ['lev_money_26w_index', 'asset_mgr_26w_index',
                        'dealer_26w_index'],
            'names': ['Managed Money 26W Index', 'Asset Mgrs 26W Index',
                      'Dealers 26W Index'],
            'colors': ['noncomm_long','comm_long','other_long'],
        },
    },

}
