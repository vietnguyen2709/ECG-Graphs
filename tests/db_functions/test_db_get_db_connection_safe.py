import pytest
from unittest.mock import MagicMock, patch
from backend.db.connection import get_db_connection_safe

# test succesfull database connection
@patch("backend.db.connection.get_db_connection")
def test_get_db_connection_safe_success(mock_get_db_connection):
    mock_db_connection = MagicMock()
    mock_get_db_connection.return_value = mock_db_connection

    connection = get_db_connection_safe()

    assert connection == mock_db_connection
    mock_get_db_connection.assert_called_once()

# test failed connection
@patch("backend.db.connection.get_db_connection")
def test_get_db_connection_safe_failure(mock_get_db_connection):
    mock_get_db_connection.side_effect = Exception("Database connection error") # raise exception

    with pytest.raises(Exception) as excinfo:
        get_db_connection_safe()

    assert "Database connection error" in str(excinfo.value)
