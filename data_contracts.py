from typing import Dict, Any, Optional
from pydantic import BaseModel, validator, ConfigDict
from datetime import datetime
import pandas as pd
from pydantic_core import core_schema

class FetchingContract(BaseModel):
    """Standardized contract for data fetching stage"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    market: str
    start_date: datetime
    end_date: datetime
    raw_data: Optional[pd.DataFrame] = None
    metadata: Dict[str, Any] = {}
    
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
            required_columns = {'date', 'open', 'high', 'low', 'close'}
            if not required_columns.issubset(df.columns):
                missing = required_columns - set(df.columns)
                raise ValueError(f"Missing required columns: {missing}")
        return df
    
    @validator('start_date', 'end_date', pre=True)
    def parse_dates(cls, value):
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        return value
        
    @validator('market')
    def validate_market(cls, value):
        if not value or not isinstance(value, str):
            raise ValueError("Market must be a non-empty string")
        return value.strip().upper()

class ProcessingContract(BaseModel):
    """Standardized contract for data processing stage"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    raw_data: pd.DataFrame
    processed_data: Optional[pd.DataFrame] = None
    validation_rules: Dict[str, Any] = {}
    cleaning_steps: Dict[str, Any] = {}
    transformation_steps: Dict[str, Any] = {}
    
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
                raise ValueError("DataFrame cannot be empty")
        return df
    
    @validator('raw_data')
    def validate_raw_data(cls, value):
        if value is None:
            return None
        required_columns = {'date', 'open', 'high', 'low', 'close'}
        if not required_columns.issubset(value.columns):
            missing = required_columns - set(value.columns)
            raise ValueError(f"Missing required columns: {missing}")
        return value

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
    
    @validator('analysis_results')
    def validate_analysis_results(cls, value):
        if not value:
            raise ValueError("Analysis results cannot be empty")
        return value

class UIRenderingContract(BaseModel):
    """Standardized contract for UI rendering stage"""
    visual_components: Dict[str, Any]
    layout: Dict[str, Any]
    interaction_config: Dict[str, Any] = {}
    
    @validator('visual_components')
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
