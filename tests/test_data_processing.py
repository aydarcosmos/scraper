import os
import sys
import pytest
import xml.etree.ElementTree as ET
from datetime import datetime
from unittest.mock import patch, MagicMock, mock_open, call

# Add the project root to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Mock the requests module before importing data_processing
sys.modules['requests'] = MagicMock()

# Mock Airflow imports before importing data_processing
sys.modules['airflow'] = MagicMock()
sys.modules['airflow.providers'] = MagicMock()
sys.modules['airflow.providers.postgres'] = MagicMock()
sys.modules['airflow.providers.postgres.hooks'] = MagicMock()

# Create a mock for the PostgresHook class
mock_postgres_hook = MagicMock()
sys.modules['airflow.providers.postgres.hooks.postgres'] = MagicMock()
sys.modules['airflow.providers.postgres.hooks.postgres'].PostgresHook = mock_postgres_hook

# Now import the module to test
from plugins.helpers import data_processing

def test_download_files_success():
    """Test successful file download"""
    # Mock the requests module at the module level where it's imported
    with patch('requests.get') as mock_get, \
         patch('os.makedirs'), \
         patch('os.path.getsize', return_value=1024), \
         patch('builtins.open', mock_open()) as mock_file:
        
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'test content'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Create a mock context (even though it's not used in the function)
        context = {}
        
        # Call the function
        data_processing.download_files(**context)
        
        # Assert requests.get was called with the correct URLs
        expected_urls = [
            "https://forecast.weather.gov/xml/current_obs/KJFK.xml",
            "https://www.floatrates.com/daily/usd.xml"
        ]
        
        # Check that get was called twice with the expected URLs
        assert mock_get.call_count == 2
        for i, url in enumerate(expected_urls):
            assert mock_get.call_args_list[i][0][0] == url
        
        # Assert the file was written with correct content
        assert mock_file().write.call_count == 2  # Called once for each file
        mock_file().write.assert_called_with(b'test content')

def test_parse_weather_xml():
    """Test parsing weather XML"""
    with patch('plugins.helpers.data_processing.ET.parse') as mock_parse, \
         patch('plugins.helpers.data_processing.os.path.exists', return_value=True), \
         patch('plugins.helpers.data_processing.datetime') as mock_datetime:
        
        # Setup mock datetime
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        # Setup mock XML parse
        mock_root = MagicMock()
        mock_element = MagicMock()
        mock_element.text = '75.0 F (23.9 C)'
        mock_root.find.return_value = mock_element
        mock_tree = MagicMock()
        mock_tree.getroot.return_value = mock_root
        mock_parse.return_value = mock_tree
        
        # Call the function
        result = data_processing.parse_files()
        
        # Assert the result
        assert result['weather']['temperature_c'] == 23.9
        assert result['weather']['timestamp'] == mock_now.isoformat()

def test_parse_currency_xml():
    """Test parsing currency XML"""
    with patch('plugins.helpers.data_processing.ET.parse') as mock_parse, \
         patch('plugins.helpers.data_processing.os.path.exists', return_value=True), \
         patch('plugins.helpers.data_processing.datetime') as mock_datetime:
        
        # Setup mock datetime
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        # Setup mock XML parse for weather file (which will be skipped)
        mock_weather_root = MagicMock()
        mock_weather_root.find.return_value = None  # This will make the weather parsing fail
        mock_weather_tree = MagicMock()
        mock_weather_tree.getroot.return_value = mock_weather_root
        
        # Setup mock XML parse for currency file
        mock_currency_root = MagicMock()
        mock_currency_item = MagicMock()
        
        # Setup the mock item to return our test data
        def mock_find(tag):
            if tag == 'targetCurrency':
                mock = MagicMock()
                mock.text = 'CNY'
                return mock
            elif tag == 'targetName':
                mock = MagicMock()
                mock.text = 'Chinese Yuan Renminbi'
                return mock
            elif tag == 'exchangeRate':
                mock = MagicMock()
                mock.text = '6.5'
                return mock
            return None
            
        mock_currency_item.find.side_effect = mock_find
        
        # Make findall return our mock item for currency parsing
        mock_currency_root.findall.return_value = [mock_currency_item]
        mock_currency_tree = MagicMock()
        mock_currency_tree.getroot.return_value = mock_currency_root
        
        # Make parse return different trees for different files
        def mock_parse_side_effect(filename, *args, **kwargs):
            if 'KJFK.xml' in filename:
                return mock_weather_tree
            elif 'usd.xml' in filename:
                return mock_currency_tree
            return MagicMock()
            
        mock_parse.side_effect = mock_parse_side_effect
        
        # Call the function with a mock context
        context = {}
        result = data_processing.parse_files(**context)
        
        # Assert the result
        assert result['currency'] is not None
        assert result['currency']['usd_to_cny'] == 6.5
        assert result['currency']['timestamp'] == mock_now.isoformat()

def test_save_to_db_success():
    """Test saving data to database"""
    with patch('airflow.providers.postgres.hooks.postgres.PostgresHook') as mock_pg_class:
        # Setup mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_pg_class.return_value.get_conn.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Setup test data
        test_data = {
            'weather': {'temperature_c': 23.9, 'timestamp': '2023-01-01T12:00:00'},
            'currency': {'usd_to_cny': 6.5, 'timestamp': '2023-01-01T12:00:00'}
        }
        
        # Create a mock context
        mock_context = {
            'task_instance': MagicMock()
        }
        mock_context['task_instance'].xcom_pull.return_value = test_data
        
        # Call the function
        data_processing.save_to_db(**mock_context)
        
        # Assert database operations
        assert mock_cursor.execute.call_count == 2  # One for weather, one for currency
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

def test_save_to_db_no_data():
    """Test saving when no data is available"""
    # Create a mock context with no data
    mock_context = {
        'task_instance': MagicMock()
    }
    mock_context['task_instance'].xcom_pull.return_value = {}
    
    # Call the function
    with patch('airflow.providers.postgres.hooks.postgres.PostgresHook') as mock_pg_class:
        data_processing.save_to_db(**mock_context)
        
        # Assert no database operations were performed
        assert not mock_pg_class.called

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
