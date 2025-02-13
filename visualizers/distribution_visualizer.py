import logging
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class DistributionChartVisualizer:
    """Handles rendering and styling of distribution charts in the app."""
    
    def __init__(self):
        """Initialize the visualizer with default settings."""
        self.logger = logging.getLogger(__name__)
        self.default_styles = {
            'plot_bgcolor': "#1e1e1e",
            'paper_bgcolor': "#1e1e1e",
            'font': {
                'family': "'Press Start 2P', monospace",
                'size': 10,
                'color': 'white'
            }
        }

    def _validate_data(self, data):
        """Validate input data for distribution charts.
        
        Args:
            data (pd.DataFrame or list): Data to validate.
            
        Returns:
            bool: True if data is valid, False otherwise.
        """
        if data is None:
            self.logger.warning("Input data is None")
            return False
            
        if isinstance(data, pd.DataFrame):
            if data.empty:
                self.logger.warning("Input DataFrame is empty")
                return False
        elif isinstance(data, list):
            if not data:
                self.logger.warning("Input list is empty")
                return False
        else:
            self.logger.warning(f"Invalid data type: {type(data)}")
            return False
            
        return True

    def _create_empty_chart(self, message="No data available"):
        """Create an empty chart with a message.
        
        Args:
            message (str): Message to display on the empty chart.
            
        Returns:
            go.Figure: Empty figure with the message.
        """
        fig = go.Figure()
        fig.update_layout(**self.default_styles)
        fig.add_annotation(
            text=message,
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=20, color="white")
        )
        return fig

    def calculate_percentiles(self, data, column):
        """Calculate key percentiles for distribution analysis.
        
        Args:
            data (pd.DataFrame): Input data
            column (str): Column name to calculate percentiles on
            
        Returns:
            dict: Percentile values keyed by percentile
        """
        if not self._validate_data(data) or column not in data.columns:
            return {}
            
        return {
            '10': np.percentile(data[column], 10),
            '25': np.percentile(data[column], 25),
            '50': np.percentile(data[column], 50),
            '75': np.percentile(data[column], 75),
            '90': np.percentile(data[column], 90)
        }

    def render_return_distribution(self, data, years=15):
        """Render a return distribution chart.
        
        Args:
            data (pd.DataFrame or list): Data to render.
            years (int): Number of years to include.
            
        Returns:
            go.Figure: The rendered chart.
        """
        if not self._validate_data(data):
            return self._create_empty_chart("Input data is invalid or empty")
            
        # Convert data to DataFrame if it's a list
        if isinstance(data, list):
            try:
                data = pd.DataFrame(data)
                self.logger.info(f"Converted list data to DataFrame with shape: {data.shape}")
            except Exception as e:
                self.logger.error(f"Failed to convert list to DataFrame: {e}")
                return self._create_empty_chart("Data conversion failed")
                
        # Log the received data structure for debugging
        self.logger.info(f"Received data with columns: {data.columns.tolist()}")
        self.logger.info(f"First few rows:\n{data.head()}")
            
        # Determine the correct column name for returns
        return_column = None
        possible_columns = [
            'percent_change', 'returns', 'change', 'pct_change', 
            'close', 'price', 'Closing Percentage', 'closing_percentage'
        ]
        for col in possible_columns:
            if col in data.columns:
                return_column = col
                self.logger.info(f"Using column '{col}' for returns")
                break
                
        if return_column is None:
            self.logger.warning(f"No valid return column found in data. Available columns: {data.columns.tolist()}")
            return self._create_empty_chart(f"No return data found. Available columns: {', '.join(data.columns)}")
            
        # Rename the column to 'returns' for consistency
        if return_column != 'returns':
            data = data.rename(columns={return_column: 'returns'})
            return_column = 'returns'
            
        # Calculate percentiles
        percentiles = self.calculate_percentiles(data, return_column)
        
        # Create figure
        fig = go.Figure()
        
        # Add histogram trace
        fig.add_trace(go.Histogram(
            x=data[return_column],
            marker=dict(color='#4CAF50'),
            opacity=0.75
        ))
        
        # Update layout
        fig.update_layout(
            title=f"{years}-Year Return Distribution",
            title_font_size=12,
            xaxis_title="Return (%)",
            yaxis_title="Frequency",
            plot_bgcolor='#1e1e1e',
            paper_bgcolor='#1e1e1e',
            font=dict(color='white', family="'Press Start 2P', monospace"),
            bargap=0.1
        )
        
        return fig

    def render_stop_loss_distribution(self, data, years=15):
        """Render a stop-loss distribution chart.
        
        Args:
            data (pd.DataFrame): Data to render.
            years (int): Number of years to include.
            
        Returns:
            go.Figure: The rendered chart.
        """
        if not self._validate_data(data):
            return self._create_empty_chart()
        # Placeholder for implementation
        return go.Figure()

    def _calculate_percentiles(self, data, column, day_type, chart_type):
        """Calculate percentiles based on day type and chart type.
        
        Args:
            data (pd.DataFrame): Input data
            column (str): Column name to calculate percentiles on
            day_type (str): Type of day (PD-H, PD-L, PD-HL, D-UP, D-DOWN)
            chart_type (str): Type of chart (open_low, open_high, open_close, low_prev_low, high_prev_high)
            
        Returns:
            dict: Percentile values keyed by percentile
        """
        if not self._validate_data(data) or column not in data.columns:
            return {}
            
        # Define rules for each combination
        rules = {
            'D-UP': {
                'open_low': ['-70', '-95'],
                'open_high': ['70', '95'],
                'open_close': ['70', '95'],
                'low_prev_low': ['-70', '-95', '70', '95'],
                'high_prev_high': ['-70', '-95', '70', '95']
            },
            'D-DOWN': {
                'open_low': ['-70', '-95'],
                'open_high': ['70', '95'],
                'open_close': ['-70', '-95'],
                'low_prev_low': ['-70', '-95', '70', '95'],
                'high_prev_high': ['-70', '-95', '70', '95']
            },
            'PD-H': {
                'open_low': ['-70', '-95'],
                'open_high': ['70', '95'],
                'open_close': ['-70', '-95', '70', '95'],
                'high_prev_high': ['70', '95']
            },
            'PD-L': {
                'open_low': ['-70', '-95'],
                'open_high': ['70', '95'],
                'open_close': ['-70', '-95', '70', '95'],
                'low_prev_low': ['-70', '-95']
            },
            'PD-HL': {
                'open_low': ['-70', '-95'],
                'open_high': ['70', '95'],
                'open_close': ['-70', '-95', '70', '95'],
                'low_prev_low': ['-70', '-95'],
                'high_prev_high': ['70', '95']
            }
        }
        
        # Get the percentiles to calculate
        percentiles_to_calculate = rules.get(day_type, {}).get(chart_type, [])
        
        # Calculate the percentiles
        result = {}
        for pct in percentiles_to_calculate:
            pct_value = float(pct)
            result[pct] = np.percentile(data[column], abs(pct_value))
            
        return result

    def _add_percentile_lines(self, fig, percentiles, day_type):
        """Add percentile lines to the figure based on day type.
        
        Args:
            fig (go.Figure): Figure to add lines to
            percentiles (dict): Percentile values
            day_type (str): Type of day (PD-H, PD-L, PD-HL, D-UP, D-DOWN)
        """
        colors = {
            'PD-H': '#4CAF50',  # Green
            'PD-L': '#FF5252',   # Red
            'PD-HL': '#FFC107',  # Amber
            'D-UP': '#2196F3',   # Blue
            'D-DOWN': '#9C27B0'  # Purple
        }
        
        for pct, value in percentiles.items():
            fig.add_vline(
                x=value,
                line_dash="dot",
                line_color=colors.get(day_type, '#FFFFFF'),
                line_width=1.5,
                annotation_text=f"{pct}%",
                annotation_position="top right" if float(pct) > 0 else "bottom right",
                annotation_font_size=12,
                annotation_font_color=colors.get(day_type, '#FFFFFF'),
                annotation_bgcolor="rgba(0,0,0,0.7)"
            )

    def _apply_day_type_styles(self, fig, day_type, title):
        """Apply consistent styling based on day type.
        
        Args:
            fig (go.Figure): Figure to style
            day_type (str): Type of day (PD-H, PD-L, PD-HL, D-UP, D-DOWN)
            title (str): Chart title
        """
        colors = {
            'PD-H': '#4CAF50',  # Green
            'PD-L': '#FF5252',   # Red
            'PD-HL': '#FFC107',  # Amber
            'D-UP': '#2196F3',   # Blue
            'D-DOWN': '#9C27B0'  # Purple
        }
        
        fig.update_layout(
            title=title,
            title_font_size=12,
            xaxis_title="Return (%)",
            yaxis_title="Frequency",
            plot_bgcolor='#1e1e1e',
            paper_bgcolor='#1e1e1e',
            font=dict(color='white', family="'Press Start 2P', monospace"),
            bargap=0.1,
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        fig.update_traces(
            marker_color=colors.get(day_type, '#FFFFFF'),
            opacity=0.75
        )

    def render_pdh_distribution(self, data, column='percent_change', title="PD-H Distribution"):
        """Render a distribution chart for PD-H days.
        
        Args:
            data (pd.DataFrame): Data to render
            column (str): Column name for distribution data
            title (str): Chart title
            
        Returns:
            go.Figure: The rendered chart
        """
        if not self._validate_data(data):
            return self._create_empty_chart("No PD-H data available")
            
        # Convert data to DataFrame if it's a list
        if isinstance(data, list):
            data = pd.DataFrame(data)
            
        # Calculate percentiles
        percentiles = self._calculate_percentiles(data, column, 'PD-H')
        
        # Create figure
        fig = go.Figure()
        
        # Add histogram trace
        fig.add_trace(go.Histogram(
            x=data[column],
            opacity=0.75
        ))
        
        # Add percentile lines
        self._add_percentile_lines(fig, percentiles, 'PD-H')
        
        # Apply styling
        self._apply_day_type_styles(fig, 'PD-H', title)
        
        return fig

    def render_pdl_distribution(self, data, column='percent_change', title="PD-L Distribution"):
        """Render a distribution chart for PD-L days.
        
        Args:
            data (pd.DataFrame): Data to render
            column (str): Column name for distribution data
            title (str): Chart title
            
        Returns:
            go.Figure: The rendered chart
        """
        if not self._validate_data(data):
            return self._create_empty_chart("No PD-L data available")
            
        # Convert data to DataFrame if it's a list
        if isinstance(data, list):
            data = pd.DataFrame(data)
            
        # Calculate percentiles
        percentiles = self._calculate_percentiles(data, column, 'PD-L')
        
        # Create figure
        fig = go.Figure()
        
        # Add histogram trace
        fig.add_trace(go.Histogram(
            x=data[column],
            opacity=0.75
        ))
        
        # Add percentile lines
        self._add_percentile_lines(fig, percentiles, 'PD-L')
        
        # Apply styling
        self._apply_day_type_styles(fig, 'PD-L', title)
        
        return fig

    def render_pdhl_distribution(self, data, column='percent_change', title="PD-HL Distribution"):
        """Render a distribution chart for PD-HL days.
        
        Args:
            data (pd.DataFrame): Data to render
            column (str): Column name for distribution data
            title (str): Chart title
            
        Returns:
            go.Figure: The rendered chart
        """
        if not self._validate_data(data):
            return self._create_empty_chart("No PD-HL data available")
            
        # Convert data to DataFrame if it's a list
        if isinstance(data, list):
            data = pd.DataFrame(data)
            
        # Calculate percentiles
        percentiles = self._calculate_percentiles(data, column, 'PD-HL')
        
        # Create figure
        fig = go.Figure()
        
        # Add histogram trace
        fig.add_trace(go.Histogram(
            x=data[column],
            opacity=0.75
        ))
        
        # Add percentile lines
        self._add_percentile_lines(fig, percentiles, 'PD-HL')
        
        # Apply styling
        self._apply_day_type_styles(fig, 'PD-HL', title)
        
        return fig

    def render_dup_distribution(self, data, column='percent_change', title="D-UP Distribution"):
        """Render a distribution chart for D-UP days.
        
        Args:
            data (pd.DataFrame): Data to render
            column (str): Column name for distribution data
            title (str): Chart title
            
        Returns:
            go.Figure: The rendered chart
        """
        if not self._validate_data(data):
            return self._create_empty_chart("No D-UP data available")
            
        # Convert data to DataFrame if it's a list
        if isinstance(data, list):
            data = pd.DataFrame(data)
            
        # Calculate percentiles
        percentiles = self._calculate_percentiles(data, column, 'D-UP')
        
        # Create figure
        fig = go.Figure()
        
        # Add histogram trace
        fig.add_trace(go.Histogram(
            x=data[column],
            opacity=0.75
        ))
        
        # Add percentile lines
        self._add_percentile_lines(fig, percentiles, 'D-UP')
        
        # Apply styling
        self._apply_day_type_styles(fig, 'D-UP', title)
        
        return fig

    def render_ddown_distribution(self, data, column='percent_change', title="D-DOWN Distribution"):
        """Render a distribution chart for D-DOWN days.
        
        Args:
            data (pd.DataFrame): Data to render
            column (str): Column name for distribution data
            title (str): Chart title
            
        Returns:
            go.Figure: The rendered chart
        """
        if not self._validate_data(data):
            return self._create_empty_chart("No D-DOWN data available")
            
        # Convert data to DataFrame if it's a list
        if isinstance(data, list):
            data = pd.DataFrame(data)
            
        # Calculate percentiles
        percentiles = self._calculate_percentiles(data, column, 'D-DOWN')
        
        # Create figure
        fig = go.Figure()
        
        # Add histogram trace
        fig.add_trace(go.Histogram(
            x=data[column],
            opacity=0.75
        ))
        
        # Add percentile lines
        self._add_percentile_lines(fig, percentiles, 'D-DOWN')
        
        # Apply styling
        self._apply_day_type_styles(fig, 'D-DOWN', title)
        
        return fig

    def render_open_high_distribution(self, data, day_type, title="Open-High Distribution"):
        """Render an Open-High distribution chart.
        
        Args:
            data (pd.DataFrame): Data to render
            day_type (str): Type of day (PD-H, PD-L, PD-HL, D-UP, D-DOWN)
            title (str): Chart title
            
        Returns:
            go.Figure: The rendered chart
        """
        if not self._validate_data(data):
            return self._create_empty_chart("No data available")
            
        # Convert data to DataFrame if it's a list
        if isinstance(data, list):
            data = pd.DataFrame(data)
            
        # Calculate percentiles
        percentiles = self._calculate_percentiles(data, 'open_high', day_type, 'open_high')
        
        # Create figure
        fig = go.Figure()
        
        # Add histogram trace
        fig.add_trace(go.Histogram(
            x=data['open_high'],
            opacity=0.75
        ))
        
        # Add percentile lines
        self._add_percentile_lines(fig, percentiles, day_type)
        
        # Apply styling
        self._apply_day_type_styles(fig, day_type, title)
        
        return fig

    def render_optimized_distribution(self, data, years=15):
        """Render a distribution chart for optimized trade results (with stop loss and exit).
        
        Args:
            data (pd.DataFrame): Optimized trade results data to render.
            years (int): Number of years to include in the title.
            
        Returns:
            go.Figure: The rendered chart.
        """
        if not self._validate_data(data):
            return self._create_empty_chart("No optimized trade data available")
            
        # Convert data to DataFrame if it's a list
        if isinstance(data, list):
            try:
                data = pd.DataFrame(data)
                self.logger.info(f"Converted list data to DataFrame with shape: {data.shape}")
            except Exception as e:
                self.logger.error(f"Failed to convert list to DataFrame: {e}")
                return self._create_empty_chart("Data conversion failed")
                
        # Determine the correct column name for returns
        return_column = None
        possible_columns = [
            'percent_change', 'returns', 'change', 'pct_change', 
            'close', 'price', 'Closing Percentage', 'closing_percentage',
            'optimized_return'  # Specific column for optimized returns
        ]
        for col in possible_columns:
            if col in data.columns:
                return_column = col
                self.logger.info(f"Using column '{col}' for optimized returns")
                break
                
        if return_column is None:
            self.logger.warning(f"No valid return column found in optimized data. Available columns: {data.columns.tolist()}")
            return self._create_empty_chart(f"No optimized return data found. Available columns: {', '.join(data.columns)}")
            
        # Create figure
        fig = go.Figure()
        
        # Add histogram trace
        fig.add_trace(go.Histogram(
            x=data[return_column],
            marker=dict(color='#FF7F0E'),  # Orange color for optimized results
            opacity=0.75
        ))
        
        # Update layout
        fig.update_layout(
            title=f"{years}-Year Optimized Trade Returns",
            title_font_size=12,
            xaxis_title="Return (%)",
            yaxis_title="Frequency",
            plot_bgcolor='#1e1e1e',
            paper_bgcolor='#1e1e1e',
            font=dict(color='white', family="'Press Start 2P', monospace"),
            bargap=0.1
        )
        
        return fig
