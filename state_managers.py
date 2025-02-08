# state_managers.py

import pandas as pd
import numpy as np
from dataclasses import dataclass

class InteractionTracker:
    """Tracks and manages user interactions (hover/click) with chart elements.
    
    Attributes:
        hover_state (dict): Current hover data including position and points
        click_state (dict): Last click data including position and clicked points
    """
    
    def __init__(self):
        self.hover_state = {}
        self.click_state = {}
    
    def configure_hover(self, fig):
        """Configure plotly figure's hover interaction settings."""
        fig.update_layout(
            hovermode="x unified",  # Show unified hover across all subplots
            hoversubplots="axis",    # Enable hover across all subplots along vertical axis
            spikedistance=-1,       # Disable hover text offset
            hoverdistance=100,
            hoverlabel=dict(
                bgcolor="#1e1e1e",
                font_size=12,
                font_family="'Press Start 2P', monospace"
            )
        )
        return fig
    
    def handle_hover(self, hover_data):
        """Process hover events and update hover state."""
        if hover_data:
            self.hover_state = {
                "x": hover_data.get("points", [{}])[0].get("x"),
                "y": hover_data.get("points", [{}])[0].get("y"),
                "points": hover_data.get("points", [])
            }
    
    def handle_click(self, click_data):
        """Process click events and update click state."""
        if click_data:
            self.click_state = {
                "x": click_data.get("points", [{}])[0].get("x"),
                "y": click_data.get("points", [{}])[0].get("y"), 
                "points": click_data.get("points", [])
            }


class ViewportHandler:
    """Centralized handler for chart viewport interactions including zoom and pan.
    
    Coordinates between Plotly relayout events and RangeManager constraints.
    Maintains viewport state between updates and handles reset requests.
    
    Args:
        range_manager (RangeManager): Instance responsible for axis range calculations
    
    Attributes:
        range_manager (RangeManager): The associated range manager
        reset_required (bool): Flag tracking if viewport reset was requested
    """
    
    def __init__(self, range_manager):
        self.range_manager = range_manager
        self.reset_required = False  # Track if reset was requested from external control
    
    def handle_relayout(self, relayout_data, reset_required):
        """
        Process relayout data from plotly interactions.
        Returns clamped x_range and computed y_range.
        """
        self.reset_required = reset_required
        
        if self.reset_required:
            return self.reset_viewport()
            
        if relayout_data:
            return self.update_viewport(relayout_data)
            
        return self.get_current_viewport()
    
    def update_viewport(self, relayout_data):
        """Update viewport based on relayout data"""
        x_range = self.range_manager.update_x_range(relayout_data)
        y_range = self.range_manager.update_y_range(x_range)
        return x_range, y_range
    
    def reset_viewport(self):
        """Reset to initial ranges"""
        self.reset_required = False
        return self.range_manager.get_initial_ranges()
    
    def get_current_viewport(self):
        """Get current compliant viewport ranges per RangeManager constraints
        
        Returns:
            tuple: (x_range, y_range) of valid viewport bounds
        """
        return (
            self.range_manager.initial_x_range,
            self.range_manager.initial_y_range
        )


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

    def compute_y_range(self, filtered_df):
        """Compute y-axis range based on filtered data"""
        return [
            max(self.initial_y_range[0], filtered_df["low"].min()),
            min(self.initial_y_range[1], filtered_df["high"].max())
        ]

    def update_x_range(self, relayout_data):
        """Update x-axis range based on relayout data"""
        if "xaxis.range[0]" in relayout_data and "xaxis.range[1]" in relayout_data:
            x_range_start = pd.Timestamp(relayout_data["xaxis.range[0]"])
            x_range_end = pd.Timestamp(relayout_data["xaxis.range[1]"])
            return self.clamp_x_range(x_range_start, x_range_end)
        return self.initial_x_range

    def update_y_range(self, x_range):
        """Update y-axis range based on the given x_range"""
        filtered_df = self.ohlc_df[(self.ohlc_df['date'] >= x_range[0]) & (self.ohlc_df['date'] <= x_range[1])]
        return self.compute_y_range(filtered_df)
