from typing import Dict, Any, Optional
from pydantic import BaseModel, field_validator, ValidationError, ConfigDict
from datetime import datetime
import pandas as pd
import numpy as np
import json
from pydantic_core import core_schema

class FetchingContract(BaseModel):
    """Standardized contract for data fetching stage with enhanced debugging"""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_default=True,
        extra='forbid',
        str_strip_whitespace=True,
        str_min_length=1
    )
    
    market: str
    start_date: datetime
    end_date: datetime
    raw_data: Optional[pd.DataFrame] = None
    metadata: Dict[str, Any] = {}
    
    def __init__(self, **data):
        print("\n=== FetchingContract Initialization ===")
        print("Input data keys:", data.keys())
        try:
            super().__init__(**data)
            print("Contract created successfully!")
            self._debug_print()
        except Exception as e:
            print(f"Error creating contract: {str(e)}")
            raise

    def _debug_print(self):
        """Print detailed contract information for debugging"""
        print("\n=== Contract Details ===")
        print(f"Market: {self.market}")
        print(f"Start Date: {self.start_date}")
        print(f"End Date: {self.end_date}")
        print(f"Metadata: {self.metadata}")
        if self.raw_data is not None:
            print("\nRaw Data Summary:")
            print(f"Type: {type(self.raw_data)}")
            print(f"Shape: {self.raw_data.shape}")
            print("Columns:", self.raw_data.columns.tolist())
            print("Sample Data:")
            print(self.raw_data.head(2))
        else:
            print("Raw Data: None")
        print("=======================\n")

    @field_validator('market')
    @classmethod
    def validate_market(cls, value: str) -> str:
        """Validate and normalize market name"""
        if not value:
            raise ValueError("Market cannot be empty")
        return value.upper().strip()

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def parse_dates(cls, value) -> datetime:
        """Parse and validate dates"""
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError as e:
                raise ValueError(f"Invalid date format: {value}. Expected ISO format (YYYY-MM-DD)")
        return value

    @field_validator('raw_data', mode='before')
    @classmethod
    def validate_raw_data(cls, value) -> Optional[pd.DataFrame]:
        """Validate and convert raw data to DataFrame"""
        print("\n=== Raw Data Validation ===")
        
        if value is None:
            print("Raw data is None")
            return None
            
        # Handle serialized DataFrame
        if isinstance(value, dict) and value.get('_is_dataframe'):
            print("Deserializing DataFrame from dict")
            try:
                value = pd.DataFrame(**{
                    'data': value['data'],
                    'index': value['index'],
                    'columns': value['columns']
                })
                if 'index' in value:
                    value = value.set_index('index')
                return value
            except Exception as e:
                print(f"DataFrame deserialization failed: {str(e)}")
                raise ValueError(f"Could not deserialize DataFrame: {str(e)}")
            
        # Convert dict to DataFrame
        if isinstance(value, dict):
            print("Converting dict to DataFrame")
            try:
                # Handle nested dicts
                if all(isinstance(v, dict) for v in value.values()):
                    value = pd.DataFrame.from_dict(value, orient='index')
                # Handle list values
                elif all(isinstance(v, (list, pd.Series)) for v in value.values()):
                    value = pd.DataFrame(value)
                # Handle scalar values
                else:
                    value = pd.DataFrame([value], index=[0])
            except Exception as e:
                print(f"Dict conversion failed: {str(e)}")
                raise ValueError(f"Could not convert dict to DataFrame: {str(e)}")
                
        # Validate DataFrame type
        if not isinstance(value, pd.DataFrame):
            print(f"Invalid type: {type(value)}")
            raise ValueError(f"raw_data must be a pandas DataFrame, got {type(value)}")
            
        # Validate required columns
        required_columns = {'date', 'open', 'high', 'low', 'close'}
        if not required_columns.issubset(value.columns):
            missing = required_columns - set(value.columns)
            print(f"Missing required columns: {missing}")
            
            # Try to create missing columns with default values
            print("Attempting to create missing columns with default values")
            for col in missing:
                if col == 'date':
                    value['date'] = value.index if isinstance(value.index, pd.DatetimeIndex) else pd.to_datetime(value.index)
                else:
                    value[col] = 0.0  # Default value for OHLC columns
                    
            # Re-check if we now have all required columns
            if not required_columns.issubset(value.columns):
                raise ValueError(f"Could not create missing columns: {missing}")
                
        # Convert date column
        if 'date' in value.columns and not pd.api.types.is_datetime64_any_dtype(value['date']):
            print("Converting date column to datetime")
            try:
                value['date'] = pd.to_datetime(value['date'])
            except Exception as e:
                print(f"Date conversion failed: {str(e)}")
                raise ValueError(f"Could not convert 'date' column to datetime: {str(e)}")
                
        print("Raw data validation successful")
        return value

    def to_dict(self) -> dict:
        """Convert contract to dict with DataFrame serialization"""
        data = self.model_dump()
        # Handle special types
        if isinstance(self.start_date, datetime):
            data['start_date'] = self.start_date.isoformat()
        if isinstance(self.end_date, datetime):
            data['end_date'] = self.end_date.isoformat()
        
        # Serialize DataFrame with numpy types converted to native Python types
        if isinstance(self.raw_data, pd.DataFrame):
            data['raw_data'] = self.raw_data.reset_index().to_dict(orient='split')
            data['raw_data']['_is_dataframe'] = True
            
        # Convert numpy types to native Python types
        return json.loads(json.dumps(data, default=self._json_serializer))

    @staticmethod
    def _json_serializer(obj):
        """Handle non-serializable types"""
        if isinstance(obj, (datetime, pd.Timestamp)):
            return obj.isoformat()
        if isinstance(obj, pd.DataFrame):
            return obj.reset_index().to_dict(orient='split')
        if isinstance(obj, np.generic):
            return obj.item()
        raise TypeError(f"Type {type(obj)} not serializable")

    def __setstate__(self, state):
        """Custom deserialization for stored state"""
        # Convert ISO strings back to datetimes
        state['start_date'] = datetime.fromisoformat(state['start_date'])
        state['end_date'] = datetime.fromisoformat(state['end_date'])
        
        # Convert dict back to DataFrame if needed
        raw_data = state.get('raw_data')
        if isinstance(raw_data, dict) and raw_data.get('_is_dataframe'):
            state['raw_data'] = pd.DataFrame(**{
                'data': raw_data['data'],
                'index': raw_data['index'],
                'columns': raw_data['columns']
            })
            if 'index' in state['raw_data']:
                state['raw_data'] = state['raw_data'].set_index('index')
        super().__setstate__(state)

    @classmethod
    def from_dict(cls, data: dict) -> 'FetchingContract':
        """Create contract from dict with DataFrame deserialization"""
        if 'raw_data' in data and isinstance(data['raw_data'], list):
            data['raw_data'] = pd.DataFrame(data['raw_data'])
        return cls(**data)

class ProcessingContract(BaseModel):
    """Standardized contract for data processing stage with enhanced debugging"""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_default=True,
        extra='forbid',
        str_strip_whitespace=True,
        str_min_length=1
    )
    
    raw_data: pd.DataFrame
    processed_data: Optional[pd.DataFrame] = None
    validation_rules: Dict[str, Any] = {}
    cleaning_steps: Dict[str, Any] = {}
    transformation_steps: Dict[str, Any] = {}
    
    def __init__(self, **data):
        print("\n=== ProcessingContract Initialization ===")
        print("Input data keys:", data.keys())
        try:
            super().__init__(**data)
            print("Contract created successfully!")
            self._debug_print()
        except Exception as e:
            print(f"Error creating contract: {str(e)}")
            raise

    def _debug_print(self):
        """Print detailed contract information for debugging"""
        print("\n=== Contract Details ===")
        print(f"Validation Rules: {self.validation_rules}")
        print(f"Cleaning Steps: {self.cleaning_steps}")
        print(f"Transformation Steps: {self.transformation_steps}")
        if self.raw_data is not None:
            print("\nRaw Data Summary:")
            print(f"Type: {type(self.raw_data)}")
            print(f"Shape: {self.raw_data.shape}")
            print("Columns:", self.raw_data.columns.tolist())
            print("Sample Data:")
            print(self.raw_data.head(2))
        else:
            print("Raw Data: None")
        print("=======================\n")

    @field_validator('raw_data', mode='before')
    @classmethod
    def validate_raw_data(cls, value) -> Optional[pd.DataFrame]:
        """Validate and convert raw data to DataFrame"""
        print("\n=== Raw Data Validation ===")
        
        if value is None:
            print("Raw data is None")
            return None
            
        # Handle serialized DataFrame
        if isinstance(value, dict) and value.get('_is_dataframe'):
            print("Deserializing DataFrame from dict")
            try:
                value = pd.DataFrame(**{
                    'data': value['data'],
                    'index': value['index'],
                    'columns': value['columns']
                })
                if 'index' in value:
                    value = value.set_index('index')
                return value
            except Exception as e:
                print(f"DataFrame deserialization failed: {str(e)}")
                raise ValueError(f"Could not deserialize DataFrame: {str(e)}")
            
        # Convert dict to DataFrame
        if isinstance(value, dict):
            print("Converting dict to DataFrame")
            try:
                # Handle nested dicts
                if all(isinstance(v, dict) for v in value.values()):
                    value = pd.DataFrame.from_dict(value, orient='index')
                # Handle list values
                elif all(isinstance(v, (list, pd.Series)) for v in value.values()):
                    value = pd.DataFrame(value)
                # Handle scalar values
                else:
                    value = pd.DataFrame([value], index=[0])
            except Exception as e:
                print(f"Dict conversion failed: {str(e)}")
                raise ValueError(f"Could not convert dict to DataFrame: {str(e)}")
                
        # Validate DataFrame type
        if not isinstance(value, pd.DataFrame):
            print(f"Invalid type: {type(value)}")
            raise ValueError(f"raw_data must be a pandas DataFrame, got {type(value)}")
            
        # Validate required columns
        required_columns = {'date', 'open', 'high', 'low', 'close'}
        if not required_columns.issubset(value.columns):
            missing = required_columns - set(value.columns)
            print(f"Missing required columns: {missing}")
            
            # Try to create missing columns with default values
            print("Attempting to create missing columns with default values")
            for col in missing:
                if col == 'date':
                    value['date'] = value.index if isinstance(value.index, pd.DatetimeIndex) else pd.to_datetime(value.index)
                else:
                    value[col] = 0.0  # Default value for OHLC columns
                    
            # Re-check if we now have all required columns
            if not required_columns.issubset(value.columns):
                raise ValueError(f"Could not create missing columns: {missing}")
                
        # Convert date column
        if 'date' in value.columns and not pd.api.types.is_datetime64_any_dtype(value['date']):
            print("Converting date column to datetime")
            try:
                value['date'] = pd.to_datetime(value['date'])
            except Exception as e:
                print(f"Date conversion failed: {str(e)}")
                raise ValueError(f"Could not convert 'date' column to datetime: {str(e)}")
                
        print("Raw data validation successful")
        return value

    def to_dict(self) -> dict:
        """Convert contract to dict with DataFrame serialization"""
        data = self.model_dump()
        
        # Serialize DataFrame with numpy types converted to native Python types
        if isinstance(self.raw_data, pd.DataFrame):
            data['raw_data'] = self.raw_data.reset_index().to_dict(orient='split')
            data['raw_data']['_is_dataframe'] = True
            
        # Convert numpy types to native Python types
        return json.loads(json.dumps(data, default=self._json_serializer))

    @staticmethod
    def _json_serializer(obj):
        """Handle non-serializable types"""
        if isinstance(obj, (datetime, pd.Timestamp)):
            return obj.isoformat()
        if isinstance(obj, pd.DataFrame):
            return obj.reset_index().to_dict(orient='split')
        if isinstance(obj, np.generic):
            return obj.item()
        raise TypeError(f"Type {type(obj)} not serializable")

    def __setstate__(self, state):
        """Custom deserialization for stored state"""
        # Convert dict back to DataFrame if needed
        raw_data = state.get('raw_data')
        if isinstance(raw_data, dict) and raw_data.get('_is_dataframe'):
            state['raw_data'] = pd.DataFrame(**{
                'data': raw_data['data'],
                'index': raw_data['index'],
                'columns': raw_data['columns']
            })
            if 'index' in state['raw_data']:
                state['raw_data'] = state['raw_data'].set_index('index')
        super().__setstate__(state)

    @classmethod
    def from_dict(cls, data: dict) -> 'ProcessingContract':
        """Create contract from dict with DataFrame deserialization"""
        if 'raw_data' in data and isinstance(data['raw_data'], list):
            data['raw_data'] = pd.DataFrame(data['raw_data'])
        return cls(**data)

class AnalysisContract(BaseModel):
    """Standardized contract for analysis stage"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    processed_data: pd.DataFrame
    analysis_results: Dict[str, Any] = {}
    metrics: Dict[str, float] = {}
    optimal_values: Dict[str, float] = {}
    risk_metrics: Dict[str, float] = {}
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        return core_schema.no_info_after_validator_function(
            cls.validate_dataframe,
            handler(pd.DataFrame)
        )
        
    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Validate DataFrame structure"""
        if df is not None:
            if df.empty:
                raise ValueError("Processed data cannot be empty")
            required_columns = {'date', 'open', 'high', 'low', 'close'}
            if not required_columns.issubset(df.columns):
                missing = required_columns - set(df.columns)
                raise ValueError(f"Missing required columns: {missing}")
        return df

class VisualizationContract(BaseModel):
    """Standardized contract for visualization stage"""
    analysis_results: Dict[str, Any]
    charts: Dict[str, Any] = {}
    tables: Dict[str, Any] = {}
    summaries: Dict[str, str] = {}
    layout_config: Dict[str, Any] = {}
    
    @field_validator('analysis_results')
    def validate_analysis_results(cls, value):
        if not value:
            raise ValueError("Analysis results cannot be empty")
        return value

class UIRenderingContract(BaseModel):
    """Standardized contract for UI rendering stage"""
    visual_components: Dict[str, Any]
    layout: Dict[str, Any]
    interaction_config: Dict[str, Any] = {}
    
    @field_validator('visual_components')
    def validate_visual_components(cls, value):
        if not value:
            raise ValueError("Visual components cannot be empty")
        return value

# Conversion utilities
def convert_fetching_to_processing(fetching_contract: FetchingContract) -> ProcessingContract:
    """Convert fetching contract to processing contract"""
    return ProcessingContract(
        raw_data=fetching_contract.raw_data,
        validation_rules={},
        cleaning_steps={},
        transformation_steps={}
    )

def convert_processing_to_analysis(processing_contract: ProcessingContract) -> AnalysisContract:
    """Convert processing contract to analysis contract"""
    return AnalysisContract(
        processed_data=processing_contract.processed_data,
        analysis_results={},
        metrics={},
        optimal_values={},
        risk_metrics={}
    )

def convert_analysis_to_visualization(analysis_contract: AnalysisContract) -> VisualizationContract:
    """Convert analysis contract to visualization contract"""
    return VisualizationContract(
        analysis_results=analysis_contract.analysis_results,
        charts={},
        tables={},
        summaries={},
        layout_config={}
    )

def convert_visualization_to_ui(visualization_contract: VisualizationContract) -> UIRenderingContract:
    """Convert visualization contract to UI rendering contract"""
    return UIRenderingContract(
        visual_components={
            'charts': visualization_contract.charts,
            'tables': visualization_contract.tables,
            'summaries': visualization_contract.summaries
        },
        layout=visualization_contract.layout_config
    )
