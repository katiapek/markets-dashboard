import pandas as pd
from typing import Dict, Set
from exceptions import DataProcessingError, DataValidationError


class DataProcessor:
    """Centralized data processing with validation, cleaning and transformation"""
    
    def __init__(self, validation_rules: Dict[str, any] = None):
        """
        Initialize with optional validation rules
        
        Args:
            validation_rules: Dictionary containing:
                - required_columns: Set of required column names
                - date_format: String format for date parsing
                - numeric_columns: List of columns to be treated as numeric
        """
        self.validation_rules = validation_rules or {
            'required_columns': {'date'},
            'date_format': '%Y-%m-%d',
            'numeric_columns': ['open', 'high', 'low', 'close']
        }

    def process(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        Main processing pipeline
        
        Args:
            raw_data: Input DataFrame to process
            
        Returns:
            Processed DataFrame
            
        Raises:
            DataProcessingError: If any processing step fails
        """
        try:
            self.validate_structure(raw_data)
            cleaned_data = self.clean_data(raw_data)
            transformed_data = self.transform_data(cleaned_data)
            return transformed_data
        except Exception as e:
            raise DataProcessingError(f"Data processing failed: {str(e)}")

    def validate_structure(self, data: pd.DataFrame) -> bool:
        """
        Validate data structure and content
        
        Args:
            data: DataFrame to validate
            
        Returns:
            True if validation passes
            
        Raises:
            DataValidationError: If validation fails
        """
        if not isinstance(data, pd.DataFrame):
            raise DataValidationError("Input must be a pandas DataFrame")
            
        missing_columns = set(self.validation_rules['required_columns']) - set(data.columns)
        if missing_columns:
            raise DataValidationError(f"Missing required columns: {missing_columns}")
            
        return True

    def clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Perform data cleaning operations
        
        Args:
            data: DataFrame to clean
            
        Returns:
            Cleaned DataFrame
        """
        # Create a copy to avoid modifying the original
        cleaned_data = data.copy()
        
        # Remove duplicates based on date
        cleaned_data = cleaned_data.drop_duplicates(subset=['date'])
        
        # Convert date format
        cleaned_data['date'] = pd.to_datetime(
            cleaned_data['date'], 
            format=self.validation_rules['date_format'],
            errors='coerce'
        )
        
        # Handle missing values in numeric columns
        for col in self.validation_rules['numeric_columns']:
            if col in cleaned_data.columns:
                cleaned_data[col] = cleaned_data[col].fillna(method='ffill').fillna(method='bfill')
        
        return cleaned_data

    def transform_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Perform data transformation operations
        
        Args:
            data: DataFrame to transform
            
        Returns:
            Transformed DataFrame
        """
        transformed_data = data.copy()
        
        # Calculate additional metrics if required columns exist
        if {'open', 'close'}.issubset(transformed_data.columns):
            transformed_data['daily_return'] = (
                (transformed_data['close'] - transformed_data['open']) / 
                transformed_data['open']
            )
        
        # Sort by date
        transformed_data = transformed_data.sort_values(by='date')
        
        return transformed_data


class OHLCProcessor:
    """Processes OHLC data for chart display and analysis"""
    
    def __init__(self, ohlc_df):
        self.ohlc_df = ohlc_df.copy()
        self.dt_breaks = []
        
    def calculate_date_ranges(self):
        """Calculate complete timeline and date gaps"""
        if self.ohlc_df.empty:
            return self
        
        dates = self.ohlc_df['date']
        self.dt_all = pd.date_range(start=dates.min(), end=dates.max())
        self.dt_obs = dates.dt.strftime("%Y-%m-%d").tolist()
        self.dt_breaks = [d for d in self.dt_all.strftime("%Y-%m-%d").tolist() 
                         if d not in self.dt_obs]
        return self
    
    def get_rangebreaks(self):
        """Get missing dates for plotly axis rangebreaks"""
        return [dict(values=self.dt_breaks)] if self.dt_breaks else []
