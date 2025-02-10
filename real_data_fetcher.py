from data_fetcher_interface import IDataFetcher
from data_fetchers import BaseDataFetcher
import logging
import time
from exceptions import DataFetchFailedError, CacheError, DataFetcherError

class RealDataFetcher(IDataFetcher):
    def clear_cache(self):
        """
        Clears the cached data by emptying the cache and cache timestamps.
        """
        try:
            self.cache.clear()
            self.cache_timestamps.clear()
            logging.info("Cache has been cleared.")
        except Exception as e:
            logging.error(f"Failed to clear cache: {e}")
            raise CacheError("Failed to clear cache.") from e

    def __init__(self, cache_duration=300, max_retries=3, retry_delay=2):
        """
        Initializes the RealDataFetcher with an empty cache, sets cache duration,
        and configures retry parameters.
        
        Args:
            cache_duration (int): Duration in seconds before cache expires. Default is 300 seconds (5 minutes).
            max_retries (int): Maximum number of retry attempts for transient errors.
            retry_delay (int): Delay in seconds between retry attempts.
        """
        self.cache = {}
        self.cache_timestamps = {}
        self.cache_duration = cache_duration  # Cache duration in seconds
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        logging.info(f"RealDataFetcher initialized with cache duration of {self.cache_duration} seconds, "
                     f"max_retries={self.max_retries}, retry_delay={self.retry_delay} seconds.")

    def fetch_data(self, params):
        """
        Fetches data from the actual data source based on provided parameters.
        Utilizes caching to store and retrieve data, with cache invalidation based on time.
        Implements retry mechanism for transient errors.
        
        Args:
            params (dict): Parameters required to fetch the data.
        
        Returns:
            data: The fetched data.
        
        Raises:
            DataFetchFailedError: If data fetching fails after retries.
            DataFetcherError: If an unexpected error occurs.
            CacheError: If there is an issue with caching.
        """
        logging.debug(f"Fetching data with params: {params}")
        cache_key = self._generate_cache_key(params)
        current_time = time.time()
        
        try:
            # Check if data is in cache and not expired
            if cache_key in self.cache:
                cached_time = self.cache_timestamps.get(cache_key, 0)
                if (current_time - cached_time) < self.cache_duration:
                    logging.debug("Data found in cache and is still valid.")
                    return self.cache[cache_key]
                else:
                    # Cache expired
                    logging.debug("Cached data has expired. Removing from cache.")
                    self.cache.pop(cache_key, None)
                    self.cache_timestamps.pop(cache_key, None)
            
            # Fetch data with retry mechanism
            data = self._fetch_with_retries(params)
            self.cache[cache_key] = data
            self.cache_timestamps[cache_key] = current_time
            logging.debug("Data fetched from source and cached.")
            return data

        except DataFetchFailedError as e:
            logging.error(f"Failed to fetch data for params {params}: {e}")
            raise
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            raise DataFetcherError("An unexpected error occurred while fetching data.") from e

    def _fetch_with_retries(self, params):
        """
        Attempts to fetch data from the source with retries for transient errors.
        
        Args:
            params (dict): Parameters required to fetch the data.
        
        Returns:
            data: The fetched data.
        
        Raises:
            DataFetchFailedError: If all retry attempts fail.
        """
        attempts = 0
        while attempts < self.max_retries:
            try:
                return self._fetch_from_source(params)
            except (ConnectionError, TimeoutError) as e:
                attempts += 1
                logging.warning(f"Attempt {attempts} failed with error: {e}. Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
        raise DataFetchFailedError(f"Failed to fetch data after {self.max_retries} attempts.")

    def _fetch_from_source(self, params):
        """
        Internal method to fetch data from the actual data source.
        
        Args:
            params (dict): Parameters required to fetch the data.
        
        Returns:
            data: The fetched data.
        
        Raises:
            ConnectionError: If there is a network issue.
            TimeoutError: If the data source times out.
            Exception: For other unforeseen errors.
        """
        try:
            # Actual database query implementation
            table_name = params.get('table_name')
            if not table_name:
                raise ValueError("Table name not specified in params")
            
            query = f"SELECT * FROM {table_name}"
            df = BaseDataFetcher.fetch_data(query)
            return df.to_dict('records')
        except (ConnectionError, TimeoutError) as e:
            logging.error(f"Transient error occurred: {e}")
            raise e  # These will be caught by the retry mechanism
        except Exception as e:
            logging.error(f"An error occurred while fetching data: {e}")
            raise e  # These will be caught and re-raised as DataFetcherError

    def _generate_cache_key(self, params):
        """
        Generates a unique cache key based on the provided parameters.
        Assumes that params is a dictionary with hashable values.
        
        Args:
            params (dict): Parameters used to fetch data.
        
        Returns:
            tuple: A hashable tuple representing the cache key.
        """
        # Convert the params dictionary into a sorted tuple of key-value pairs
        # This ensures that the cache key is consistent for the same parameters
        return tuple(sorted(params.items()))

class SubplotFetcher(RealDataFetcher):
    """Specialized fetcher for COT subplot data"""
    def _fetch_from_source(self, params):
        try:
            return BaseDataFetcher.fetch_active_subplot_data(
                params['market'],
                params['year'],
                params['subplot_type'],
                params['table_suffix'],
                params['report_type']
            )
        except Exception as e:
            logging.error(f"Subplot fetch failed: {e}")
            raise DataFetchFailedError("Failed to fetch subplot data") from e

class SeasonalityFetcher(RealDataFetcher):
    """Specialized fetcher for seasonality data"""
    def _fetch_from_source(self, params):
        try:
            return fetch_seasonal_data_cached(
                params['market'],
                params['years'],
                params['base_year']
            )
        except Exception as e:
            logging.error(f"Seasonality fetch failed: {e}")
            raise DataFetchFailedError("Failed to fetch seasonality data") from e
        """
        Generates a unique cache key based on the provided parameters.
        Assumes that params is a dictionary with hashable values.
        
        Args:
            params (dict): Parameters used to fetch data.
        
        Returns:
            tuple: A hashable tuple representing the cache key.
        """
        # Convert the params dictionary into a sorted tuple of key-value pairs
        # This ensures that the cache key is consistent for the same parameters
        return tuple(sorted(params.items()))
