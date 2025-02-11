class DataFetcherError(Exception):
    """Base exception class for DataFetcher related errors."""
    pass

class DataFetchFailedError(DataFetcherError):
    """Exception raised when data fetching fails."""
    def __init__(self, message="Data fetching failed.", original_exception=None):
        super().__init__(message)
        self.original_exception = original_exception

class CacheError(DataFetcherError):
    """Exception raised for cache-related errors."""
    pass

class DataProcessingError(Exception):
    """Base exception class for data processing errors."""
    def __init__(self, message="Data processing failed", details=None):
        super().__init__(message)
        self.details = details
        
    def __str__(self):
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message

class DataValidationError(DataProcessingError):
    """Exception raised when data validation fails."""
    def __init__(self, message="Data validation failed", invalid_data=None):
        super().__init__(message)
        self.invalid_data = invalid_data
        
    def __str__(self):
        if self.invalid_data:
            return f"{self.message}: Invalid data - {self.invalid_data}"
        return self.message

class AnalysisError(Exception):
    """Base exception class for analysis related errors."""
    def __init__(self, message="Analysis failed", details=None):
        super().__init__(message)
        self.details = details
        
    def __str__(self):
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message
