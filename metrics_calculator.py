
import numpy as np
import pandas as pd

class MetricsCalculator:
    """Centralized financial metrics calculations with validation and vectorized operations"""
    
    @staticmethod
    def calculate_sharpe_ratio(daily_returns: pd.Series, risk_free_rate: float = 0) -> float:
        """Calculate annualized Sharpe ratio with empty check and div-by-zero protection"""
        if daily_returns.empty or daily_returns.std() == 0:
            return 0.0
        return (daily_returns.mean() - risk_free_rate) / daily_returns.std() * np.sqrt(252)

    @staticmethod
    def calculate_sortino_ratio(daily_returns: pd.Series, risk_free_rate: float = 0) -> float:
        """Calculate annualized Sortino ratio using downside deviation"""
        negative_returns = daily_returns[daily_returns < risk_free_rate]
        if negative_returns.empty or negative_returns.std() == 0:
            return 0.0
        return (daily_returns.mean() - risk_free_rate) / negative_returns.std() * np.sqrt(252)

    @staticmethod
    def calculate_maximum_drawdown(cumulative_returns: pd.Series) -> float:
        """Calculate maximum drawdown from cumulative returns series"""
        cumulative_max = cumulative_returns.cummax()
        drawdown = cumulative_returns - cumulative_max
        return abs(drawdown.min())

    @staticmethod
    def calculate_volatility(daily_returns: pd.Series) -> float:
        """Calculate annualized volatility"""
        return daily_returns.std() * np.sqrt(252)

    @staticmethod
    def calculate_calmar_ratio(daily_returns: pd.Series, max_drawdown: float) -> float:
        """Calculate Calmar ratio using annualized returns and max drawdown"""
        annualized_return = daily_returns.mean() * 252  # 252 trading days
        return annualized_return / abs(max_drawdown)

    @classmethod
    def calculate_risk_metrics(cls, daily_returns: pd.Series, cumulative_returns: pd.Series) -> dict:
        """Calculate comprehensive risk metrics package"""
        return {
            'Sharpe Ratio': cls.calculate_sharpe_ratio(daily_returns),
            'Sortino Ratio': cls.calculate_sortino_ratio(daily_returns),
            'Max Drawdown': cls.calculate_maximum_drawdown(cumulative_returns),
            'Volatility': cls.calculate_volatility(daily_returns),
            'Calmar Ratio': cls.calculate_calmar_ratio(daily_returns, 
                cls.calculate_maximum_drawdown(cumulative_returns))
        }
