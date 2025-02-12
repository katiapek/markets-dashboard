import logging
from typing import Dict, Any
import pandas as pd
from dash import dash_table

class TableVisualizer:
    """
    Handles rendering and styling of data tables in the app.
    
    Attributes:
        table_styles (Dict[str, Any]): Predefined styles for tables.
        logger (logging.Logger): Logger for tracking table generation steps.
    """

    def __init__(self):
        """
        Initialize the TableVisualizer with default styles and logging.
        """
        self.table_styles = {}
        self.logger = logging.getLogger(__name__)
        self._setup_logging()

    def _setup_logging(self):
        """
        Configure logging for the TableVisualizer.
        """
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

    def render_yearly_analysis(self, data: pd.DataFrame) -> dash_table.DataTable:
        """
        Render the yearly analysis table.
        
        Args:
            data (pd.DataFrame): Processed data for the table.
            
        Returns:
            dash_table.DataTable: Rendered table component.
        """
        self.logger.info("Rendering yearly analysis table")
        
        try:
            if not self.validate_data(data, "yearly_analysis"):
                return self.generate_fallback_table("yearly_analysis")
            
            table = dash_table.DataTable(
                data=data.to_dict("records"),
                columns=[{"name": col, "id": col} for col in data.columns]
            )
            return self.apply_styles(table)
        except Exception as e:
            return self._handle_error(e, "yearly_analysis")

    def render_day_trading_stats(self, data: pd.DataFrame) -> dash_table.DataTable:
        """
        Render the day trading stats table.
        
        Args:
            data (pd.DataFrame): Processed data for the table.
            
        Returns:
            dash_table.DataTable: Rendered table component.
        """
        self.logger.info("Rendering day trading stats table")
        
        try:
            if not self.validate_data(data, "day_trading_stats"):
                return self.generate_fallback_table("day_trading_stats")
            
            table = dash_table.DataTable(
                data=data.to_dict("records"),
                columns=[{"name": col, "id": col} for col in data.columns]
            )
            return self.apply_styles(table)
        except Exception as e:
            return self._handle_error(e, "day_trading_stats")

    def render_correlation_table(self, data: pd.DataFrame) -> dash_table.DataTable:
        """
        Render the correlation table.
        
        Args:
            data (pd.DataFrame): Processed data for the table.
            
        Returns:
            dash_table.DataTable: Rendered table component.
        """
        self.logger.info("Rendering correlation table")
        
        try:
            if not self.validate_data(data, "correlation_table"):
                return self.generate_fallback_table("correlation_table")
            
            table = dash_table.DataTable(
                data=data.to_dict("records"),
                columns=[{"name": col, "id": col} for col in data.columns]
            )
            return self.apply_styles(table)
        except Exception as e:
            return self._handle_error(e, "correlation_table")

    def apply_styles(self, table: dash_table.DataTable) -> dash_table.DataTable:
        """
        Apply consistent styling to a table.
        
        Args:
            table (dash_table.DataTable): Table to style.
            
        Returns:
            dash_table.DataTable: Styled table.
        """
        self.logger.debug("Applying styles to table")
        
        table.style_data_conditional = [
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "rgb(248, 248, 248)"
            }
        ]
        table.style_header = {
            "backgroundColor": "rgb(230, 230, 230)",
            "fontWeight": "bold"
        }
        return table

    def validate_data(self, data: pd.DataFrame, table_type: str) -> bool:
        """
        Validate data for a specific table type.
        
        Args:
            data (pd.DataFrame): Data to validate.
            table_type (str): Type of table (e.g., 'yearly_analysis').
            
        Returns:
            bool: True if data is valid, False otherwise.
        """
        self.logger.debug(f"Validating data for {table_type}")
        
        if data.empty:
            self.logger.warning(f"Empty data for {table_type}")
            return False
        
        if not isinstance(data, pd.DataFrame):
            self.logger.warning(f"Invalid data type for {table_type}")
            return False
        
        return True

    def generate_fallback_table(self, table_type: str) -> dash_table.DataTable:
        """
        Generate a fallback table for invalid or missing data.
        
        Args:
            table_type (str): Type of table to generate.
            
        Returns:
            dash_table.DataTable: Fallback table with error message.
        """
        self.logger.warning(f"Generating fallback table for {table_type}")
        
        fallback_data = pd.DataFrame({
            "Error": ["Data not available"],
            "Details": [f"Could not generate {table_type} table"]
        })
        
        return dash_table.DataTable(
            data=fallback_data.to_dict("records"),
            columns=[{"name": col, "id": col} for col in fallback_data.columns],
            style_cell={"textAlign": "center"},
            style_header={
                "backgroundColor": "lightgray",
                "fontWeight": "bold"
            }
        )

    def _handle_error(self, error: Exception, table_type: str) -> dash_table.DataTable:
        """
        Handle errors during table generation.
        
        Args:
            error (Exception): The error that occurred.
            table_type (str): Type of table being generated.
            
        Returns:
            dash_table.DataTable: Fallback table with error details.
        """
        self.logger.error(f"Error generating {table_type} table: {str(error)}")
        return self.generate_fallback_table(table_type)
