# app.py
import dash
import dash_bootstrap_components as dbc
from layout_definitions import create_layout
from callbacks import register_callbacks


# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, '/assets/styles.css'])
app.title = "ClockTrades"
server = app.server

# Set the app layout
create_layout(app)

# Register callbacks
register_callbacks(app)


@app.server.route("/disclaimer")
def disclaimer():
    return """
    <html>
    <head>
        <title>Disclaimer - ClockTrades</title>
        <style>
            body {
                background-color: #1e1e1e;
                color: white;
                font-family: 'Press Start 2P', monospace;
                padding: 20px;
                line-height: 1.6;
            }
            a {
                color: #4CAF50;
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <h1>ClockTrades Disclaimer</h1>
        <p>Trading involves substantial risk, and the risk of loss can be significant. The information provided on ClockTrades is for educational purposes only. ClockTrades is not a Commodity Trading Advisor (CTA), does not offer financial advice, and does not receive any fees or commissions related to trading activity.</p>
        <h2>Risk of Trading Futures, Options, Equities, and Forex</h2>
        <p>There is a significant risk of loss in trading futures, forex, equities, and options—including trades executed online. Trade only with capital you can afford to lose. Past performance is not necessarily indicative of future results. The information on ClockTrades is not a recommendation to buy or sell any instrument.</p>
        <h2>Hypothetical Performance Disclosure</h2>
        <p>Hypothetical performance results presented on ClockTrades have inherent limitations. No representation is made that any account will or is likely to achieve results similar to those shown. Hypothetical trading does not involve financial risk, and no hypothetical record can fully account for the impact of financial risk in actual trading. Factors such as market liquidity, slippage, and adherence to a strategy during drawdowns can significantly affect real-world trading outcomes.
        ClockTrades does not trade or manage client accounts. Be cautious when interpreting hypothetical performance data.</p>
        <h2>CFTC RULE 4.41</h2>
        <p>HYPOTHETICAL OR SIMULATED PERFORMANCE RESULTS HAVE CERTAIN LIMITATIONS. UNLIKE AN ACTUAL PERFORMANCE RECORD, SIMULATED RESULTS DO NOT REPRESENT ACTUAL TRADING. ALSO, SINCE THE TRADES HAVE NOT BEEN EXECUTED, THE RESULTS MAY HAVE UNDER-OR-OVER-COMPENSATED FOR THE IMPACT OF CERTAIN MARKET FACTORS, SUCH AS LACK OF LIQUIDITY. SIMULATED TRADING PROGRAMS IN GENERAL ARE SUBJECT TO THE FACT THAT THEY ARE DESIGNED WITH THE BENEFIT OF HINDSIGHT. NO REPRESENTATION IS BEING MADE THAT ANY ACCOUNT WILL OR IS LIKELY TO ACHIEVE PROFITS OR LOSSES SIMILAR TO THOSE DISCUSSED.</p>
        <h2>Educational Purpose</h2>
        <p>ClockTrades is designed as an educational platform for analyzing trading data. We provide tools for exploring historical market behavior, not advice or guidance on executing trades. Any decision to invest or trade based on information from this app is solely at your discretion and risk.</p>
    </body>
    </html>
    """


if __name__ == '__main__':
    app.run_server(debug=True)

