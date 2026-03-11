class NavigationService:
    """Centralized service for market and year navigation with state validation"""
    
    def __init__(self, market_tickers, initial_market=None, initial_year=2023):
        """
        Initialize navigation service with market configuration.
        
        Args:
            market_tickers (dict): Mapping of market names to tickers
            initial_market (str): Starting market (defaults to first in list)
            initial_year (int): Starting year (defaults to 2023)
        """
        self.market_tickers = market_tickers
        self.markets = list(market_tickers.keys())
        self.current_market = initial_market if initial_market else self.markets[0]
        self.current_year = initial_year if self.validate_year(initial_year) else 2023
        
    def validate_market(self, market):
        """Validate if market exists in configuration"""
        return market in self.market_tickers
        
    def validate_year(self, year):
        """Validate year is within allowed range"""
        from datetime import datetime
        return 1994 <= year <= datetime.now().year
        
    def next_market(self):
        """Move to next market with wrap-around"""
        current_index = self.markets.index(self.current_market)
        new_index = (current_index + 1) % len(self.markets)
        self.current_market = self.markets[new_index]
        return self.current_market, self.market_tickers[self.current_market]
        
    def previous_market(self):
        """Move to previous market with wrap-around"""
        current_index = self.markets.index(self.current_market)
        new_index = (current_index - 1) % len(self.markets)
        self.current_market = self.markets[new_index]
        return self.current_market, self.market_tickers[self.current_market]
        
    def set_market(self, market):
        """Set specific market with validation"""
        if self.validate_market(market):
            self.current_market = market
            return self.current_market, self.market_tickers[self.current_market]
        return None, None
        
    def next_year(self):
        """Increment year with bounds checking"""
        if self.validate_year(self.current_year + 1):
            self.current_year += 1
        return self.current_year
        
    def previous_year(self):
        """Decrement year with bounds checking"""
        if self.validate_year(self.current_year - 1):
            self.current_year -= 1
        return self.current_year
        
    def set_year(self, year):
        """Set specific year with validation"""
        if self.validate_year(year):
            self.current_year = year
            return self.current_year
        return None
        
    def get_current_state(self):
        """Get current market and year state"""
        return {
            'market': self.current_market,
            'ticker': self.market_tickers[self.current_market],
            'year': self.current_year
        }
