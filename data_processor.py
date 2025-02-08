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
