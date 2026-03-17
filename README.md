# Markets Dashboard

An interactive web dashboard for analyzing futures markets through **Commitment of Traders (COT) reports**, **OHLC price data**, **seasonality patterns**, and **day-trading statistics**. Built with Dash/Plotly and backed by PostgreSQL.

![OHLC with Seasonality Overlays](screenshots/1.png)
*OHLC candlestick chart with 15-year and 35-year seasonal pattern overlays*

## Features

### COT Report Analysis
- **Three report formats:** Legacy, Disaggregated, and Traders in Financial Futures (TFF)
- **Combined and Futures-Only** variants for each format
- Metrics: Open Interest, % of OI by trader type, Net Positions, Position Changes, 26-Week Index

### Price & Seasonality
- Interactive candlestick charts with OHLC data (via Yahoo Finance)
- 15-year and 35-year seasonal pattern overlays
- Custom date range analysis

### Day Trading Statistics

![Day Trading Statistics](screenshots/7.png)
*Yearly day-type breakdown: D-UP/D-DN days, PD-H, PD-L, PD-HL, PD-nHL patterns*

- Day type classification (D-UP, D-DN)
- Previous-day relationship patterns (PD-H, PD-L, PD-HL, PD-nHL)
- Advanced patterns: CaPD, CbPD, BISI, SIBI

### Distribution & Scatter Analysis

![D-UP Day Distribution](screenshots/8.png)
*Distribution charts with 70th and 95th percentile markers for Open-Low, Open-High, and Open-Close % changes*

![Scatter Analysis with Optimal Levels](screenshots/9.png)
*Previous-day distributions and scatter plots showing optimal stop-loss and exit levels*

### Drawdown & Gain Analysis

![Yearly Drawdown & Gain Analysis](screenshots/2.png)
*Per-year max drawdown, max gain, and closing performance breakdown*

### Risk Metrics & Cumulative Returns

![Risk Metrics Summary](screenshots/3.png)
*15-year and 30-year summary: win rate, optimal stop-loss/exit, and points gained*

![Return Distribution](screenshots/4.png)
*Return distribution histograms with and without optimized stop-loss*

![Cumulative Returns](screenshots/5.png)
*Cumulative return curves with Sharpe, Sortino, Calmar ratios and max drawdown metrics*

### Market Correlation

![180-Day Correlation Matrix](screenshots/6.png)
*Cross-market correlation matrix across 40+ futures contracts*

## Supported Markets (44)

| Category | Markets |
|---|---|
| **Fixed Income** | 30-Day Fed Fund, 2Y Note, 5Y Note, 10Y Note, Ultra 10Y, US Treasury Bond |
| **Equity Indices** | S&P 500, Nasdaq 100, Russell 2000, Dow Jones, VIX |
| **Forex** | USD Index, EUR, AUD, NZD, GBP, CAD, JPY, CHF, MXN, BRL |
| **Crypto** | Bitcoin, Ethereum |
| **Energy** | Crude Oil, Natural Gas, ULSD, RBOB Gasoline |
| **Agriculture** | Wheat, KC HRW Wheat, Corn, Soybeans, Soybean Oil, Soybean Meal, Cocoa, Coffee |
| **Livestock** | Live Cattle, Feeder Cattle, Lean Hog |
| **Metals** | Gold, Silver, Copper |

## Tech Stack

- **Framework:** Dash 2.18 / Flask / Gunicorn
- **Database:** PostgreSQL (via SQLAlchemy)
- **Data Sources:** CFTC Public Reporting API, Yahoo Finance (yfinance)
- **Visualization:** Plotly, Dash Bootstrap Components
- **Data Processing:** Pandas, NumPy, scikit-learn
- **Python:** 3.12

## Setup

### Prerequisites
- Python 3.12+
- PostgreSQL

### Installation

```bash
git clone https://github.com/katiapek/markets-dashboard.git
cd markets-dashboard

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Configuration

Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

Required environment variables:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `CFTC_TOKEN` | CFTC Socrata API app token ([register here](https://publicreporting.cftc.gov)) |

### Populate the Database

Run the data pipeline scripts:

```bash
# 1. Fetch OHLC price data
python scripts/Fetch_OHLC.py

# 2. Fetch COT data (run each variant)
python scripts/Fetch_COT_Legacy_Combined.py
python scripts/Fetch_COT_Legacy_Futures_Only.py
python scripts/Fetch_COT_Disaggregated_Combined.py
python scripts/Fetch_COT_Disaggregated_Futures_Only.py
python scripts/Fetch_COT_TFF_Combined.py
python scripts/Fetch_COT_TFF_Futures_Only.py

# 3. Calculate derived COT metrics
python scripts/Calc_COT_Legacy.py
python scripts/Calc_COT_Disaggregated.py
python scripts/Calc_COT_TFF.py
```

### Run

```bash
python app.py
```

Open [http://localhost:8050](http://localhost:8050)

## Deployment (Heroku)

The app is configured for Heroku deployment via `Procfile` and `runtime.txt`.

```bash
heroku config:set DATABASE_URL=postgresql://...
heroku config:set CFTC_TOKEN=your-token
git push heroku main
```

## Project Structure

```
├── app.py                  # Dash app entry point
├── callbacks.py            # Dash callbacks (UI interactivity)
├── callback_helpers.py     # Callback utilities & chart helpers
├── layout_definitions.py   # UI component factories
├── data_fetchers.py        # Database queries (OHLC, COT, correlations)
├── scripts/
│   ├── config.py           # Market codes, tickers, trace config
│   ├── Fetch_OHLC.py       # Yahoo Finance -> PostgreSQL
│   ├── Fetch_COT_*.py      # CFTC API -> PostgreSQL (6 variants)
│   └── Calc_COT_*.py       # Derived metric calculations (3 variants)
├── assets/                 # CSS, JS, favicon
├── Procfile                # Heroku process definition
├── runtime.txt             # Python version
└── requirements.txt        # Dependencies
```

## Data Sources

- **CFTC Commitment of Traders:** [publicreporting.cftc.gov](https://publicreporting.cftc.gov) -- weekly trader positioning data for regulated futures markets
- **Yahoo Finance:** Historical OHLC price data via [yfinance](https://github.com/ranaroussi/yfinance)

## Disclaimer

This application is for **educational and informational purposes only**. It is not a registered Commodity Trading Advisor (CTA) and does not provide investment advice. All data and analysis are presented as-is with no guarantees. Trading futures involves substantial risk of loss. See the in-app `/disclaimer` page for full CFTC Rule 4.41 disclosure.

## License

All rights reserved.
