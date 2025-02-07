import pandas as pd
import numpy as np
from dataclasses import dataclass

class RangeManager:
    """Manages chart axis ranges and constraints"""
    
    def __init__(self, ohlc_df):
        self.ohlc_df = ohlc_df
        self.buffer_days = 2
        self._init_ranges()
        
    def _init_ranges(self):
        """Initialize base ranges from OHLC data"""
        if len(self.ohlc_df) < 30:
            end_date = pd.Timestamp(f"{self.ohlc_df['date'].dt.year[0]}-03-31")
        elif len(self.ohlc_df) < 60:
            end_date = pd.Timestamp(f"{self.ohlc_df['date'].dt.year[0]}-06-30")
        else:
            end_date = self.ohlc_df['date'].iloc[-1]
            
        self.initial_x_range = [
            self.ohlc_df['date'].iloc[0] - pd.DateOffset(days=self.buffer_days),
            end_date + pd.DateOffset(days=self.buffer_days)
        ]
        self.initial_y_range = [self.ohlc_df["low"].min(), self.ohlc_df["high"].max()]
        
    def get_initial_ranges(self):
        return self.initial_x_range, self.initial_y_range
        
    def clamp_x_range(self, x_range_start, x_range_end):
        """Keep zoom range within sane bounds"""
        return [
            max(self.initial_x_range[0], x_range_start),
            min(self.initial_x_range[1], x_range_end)
        ]
