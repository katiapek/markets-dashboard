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
