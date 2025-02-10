import pandas as pd

class RangeFilter:
    """Handles viewport-based data filtering"""
    def __init__(self, full_data: pd.DataFrame):
        self.full_data = full_data
        self.filtered_data = full_data
        self.date_col = 'date'  # Default date column
        
    def set_date_column(self, col_name: str):
        """Set the column name to use for date filtering"""
        self.date_col = col_name
        return self
        
    def apply_viewport_filter(self, date_range: tuple):
        """Apply date range filter to data
        Args:
            date_range: Tuple of (start_date, end_date) as datetime objects
        Returns:
            self for method chaining
        """
        if self.full_data.empty or not date_range:
            return self
            
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        mask = (
            (self.full_data[self.date_col] >= start_date) & 
            (self.full_data[self.date_col] <= end_date)
        )
        self.filtered_data = self.full_data.loc[mask]
        return self
        
    def get_filtered_data(self) -> pd.DataFrame:
        """Get the filtered dataset"""
        return self.filtered_data
        
    def get_valid_date_range(self) -> tuple:
        """Get min/max dates for viewport constraints"""
        if self.full_data.empty:
            return (None, None)
        return (
            self.full_data[self.date_col].min(), 
            self.full_data[self.date_col].max()
        )
