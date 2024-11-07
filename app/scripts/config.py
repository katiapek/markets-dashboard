# config.py
db_path_str = '/Users/kamil/PycharmProjects/MarketsDashboard/app/data/markets_data.db'

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

# Market codes for filtering
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

