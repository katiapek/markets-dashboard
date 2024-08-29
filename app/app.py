# app.py
import dash
from layout_definitions import create_layout
from callbacks import register_callbacks

# Initialize Dash app
app = dash.Dash(__name__)

# Set the app layout
create_layout(app)

# Register callbacks
register_callbacks(app)

if __name__ == '__main__':
    app.run_server(debug=True)

