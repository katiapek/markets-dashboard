import pytest
from unittest.mock import patch
from real_data_fetcher import RealDataFetcher
import time

@pytest.fixture
def real_data_fetcher():
    # Initialize RealDataFetcher with a short cache duration for testing
    return RealDataFetcher(cache_duration=2)  # 2 seconds for quick expiration

def test_cache_hit(real_data_fetcher):
    params = {'key': 'param1'}

    with patch.object(RealDataFetcher, '_fetch_from_source', return_value={'data': 'fetched_data'}) as mock_fetch:
        # First fetch should call _fetch_from_source
        data1 = real_data_fetcher.fetch_data(params)
        mock_fetch.assert_called_once_with(params)
        assert data1 == {'data': 'fetched_data'}

        # Second fetch within cache duration should not call _fetch_from_source
        data2 = real_data_fetcher.fetch_data(params)
        mock_fetch.assert_called_once()  # No additional calls
        assert data2 == {'data': 'fetched_data'}

def test_cache_miss(real_data_fetcher):
    params = {'key': 'param2'}

    with patch.object(RealDataFetcher, '_fetch_from_source', return_value={'data': 'fetched_data'}) as mock_fetch:
        # Fetch data which is not in cache
        data = real_data_fetcher.fetch_data(params)
        mock_fetch.assert_called_once_with(params)
        assert data == {'data': 'fetched_data'}

def test_cache_expiration(real_data_fetcher):
    params = {'key': 'param3'}

    with patch.object(RealDataFetcher, '_fetch_from_source', return_value={'data': 'fetched_data'}) as mock_fetch:
        # First fetch should call _fetch_from_source
        data1 = real_data_fetcher.fetch_data(params)
        mock_fetch.assert_called_once_with(params)
        assert data1 == {'data': 'fetched_data'}

        # Wait for cache to expire
        time.sleep(3)  # Sleep longer than cache_duration

        # Second fetch should call _fetch_from_source again due to cache expiration
        data2 = real_data_fetcher.fetch_data(params)
        assert mock_fetch.call_count == 2
        assert data2 == {'data': 'fetched_data'}

def test_clear_cache(real_data_fetcher):
    params = {'key': 'param4'}

    with patch.object(RealDataFetcher, '_fetch_from_source', return_value={'data': 'fetched_data'}) as mock_fetch:
        # Fetch data to populate cache
        data1 = real_data_fetcher.fetch_data(params)
        mock_fetch.assert_called_once_with(params)
        assert data1 == {'data': 'fetched_data'}

        # Clear the cache
        real_data_fetcher.clear_cache()

        # Fetch data again, should call _fetch_from_source again
        data2 = real_data_fetcher.fetch_data(params)
        assert mock_fetch.call_count == 2
        assert data2 == {'data': 'fetched_data'}

def test_generate_cache_key(real_data_fetcher):
    params = {'b': 2, 'a': 1}
    expected_key = (('a', 1), ('b', 2))
    cache_key = real_data_fetcher._generate_cache_key(params)
    assert cache_key == expected_key

def test_fetch_data_with_different_params(real_data_fetcher):
    params1 = {'key': 'param5'}
    params2 = {'key': 'param6'}

    with patch.object(RealDataFetcher, '_fetch_from_source', side_effect=[{'data': 'data5'}, {'data': 'data6'}]) as mock_fetch:
        # Fetch first set of params
        data1 = real_data_fetcher.fetch_data(params1)
        mock_fetch.assert_called_once_with(params1)
        assert data1 == {'data': 'data5'}

        # Fetch second set of params
        data2 = real_data_fetcher.fetch_data(params2)
        assert mock_fetch.call_count == 2
        mock_fetch.assert_called_with(params2)
        assert data2 == {'data': 'data6'}

        # Fetch first set again; should use cache
        data3 = real_data_fetcher.fetch_data(params1)
        assert mock_fetch.call_count == 2  # No additional call
        assert data3 == {'data': 'data5'}
