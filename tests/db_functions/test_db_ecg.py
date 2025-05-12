import pytest
import json
from unittest.mock import patch, MagicMock
import pymysql
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../code")))

from backend.db.ecg import (
    ecg_data_exists, insert_ecg_data_into_db, fetch_all_ecg_data, fetch_ecg_data_by_patient_id
)
from backend.db.utils import execute_query, fetch_from_db


@pytest.fixture(autouse=True)
def mock_db_functions():
    with patch("backend.db.ecg.execute_query") as mock_execute_query, \
         patch("backend.db.ecg.fetch_from_db") as mock_fetch_from_db:
        yield mock_execute_query, mock_fetch_from_db

def test_ecg_data_exists(mock_db_functions):
    mock_execute_query, _ = mock_db_functions

    #simulate a record found for patient_id 3
    mock_execute_query.return_value = [(1,)]
    assert ecg_data_exists(3) is True

    #simulate no record found for patient_id 999 returning None
    mock_execute_query.return_value = None
    assert ecg_data_exists(999) is False

def test_insert_ecg_data_into_db(mock_db_functions):
    mock_execute_query, _ = mock_db_functions

    ecg_data = {
        "time": [1, 2, 3],
        "signals": [0.1, 0.2, 0.3],
        "maxima_graph_data": [0.3, 0.4],
        "minima_graph_data": [0.1, 0.2],
        "baselines_graph_data": [0.15, 0.25]
    }

    insert_ecg_data_into_db(1, ecg_data)

    expected_query = """
        INSERT INTO ecg_data (
            patient_id, time_data, signal_raw_data, maxima_data,
            minima_data, baseline_data
        ) VALUES (%s, %s, %s, %s, %s, %s)
    """

    expected_values = (
        1,
        json.dumps([1, 2, 3]), # expected json dumps from db
        json.dumps([0.1, 0.2, 0.3]),
        json.dumps([0.3, 0.4]),
        json.dumps([0.1, 0.2]),
        json.dumps([0.15, 0.25])
    )

    mock_execute_query.assert_called_once_with(expected_query, expected_values)

#test failure inserting ECG data due to foreign key constraint when patient id doesnt exist
def test_insert_ecg_data_into_db_failure(mock_db_functions):
    mock_execute_query, _ = mock_db_functions
    mock_execute_query.side_effect = pymysql.err.IntegrityError(1216, "Foreign key constraint fails")

    ecg_data = {
        "time": [1, 2, 3],
        "signals": [0.1, 0.2, 0.3],
        "maxima_graph_data": [0.3, 0.4],
        "minima_graph_data": [0.1, 0.2],
        "baselines_graph_data": [0.15, 0.25]
    }

    with pytest.raises(pymysql.err.IntegrityError): # raise db error
        insert_ecg_data_into_db(1234, ecg_data)

#test fetching all ECG data
def test_fetch_all_ecg_data(mock_db_functions):
    _, mock_fetch_from_db = mock_db_functions
    mock_fetch_from_db.return_value = {
        "success": True,
        "data": [
            (1, json.dumps({
                "time": [1, 2],
                "signals": [0.1, 0.2],
                "maxima_graph_data": [0.3, 0.4],
                "minima_graph_data": [0.1, 0.2],
                "baselines_graph_data": [0.15, 0.25]
            }))
        ]
    }
    expected_result = mock_fetch_from_db.return_value
    assert fetch_all_ecg_data() == expected_result

#test for fetching ECG data by patient_id
@patch('backend.db.ecg.execute_query')
def test_fetch_ecg_data_by_patient_id(mock_execute_query):
    mock_execute_query.return_value = { 
        "time_data": json.dumps([1, 2]), # mock patients ecg data
        "signal_raw_data": json.dumps([0.1, 0.2]),
        "maxima_data": json.dumps([0.3, 0.4]),
        "minima_data": json.dumps([0.5, 0.6]),
        "baseline_data": json.dumps([0.7, 0.8])
    }

    expected_result = {
        "time": [1, 2],
        "signals": [0.1, 0.2],
        "maxima_graph_data": [0.3, 0.4],
        "minima_graph_data": [0.5, 0.6],
        "baselines_graph_data": [0.7, 0.8]
    }

    result = fetch_ecg_data_by_patient_id(123)
    assert result == expected_result


#test failure when fetching ECG data by patient_id but no data is found
@patch('backend.db.ecg.execute_query')
def test_fetch_ecg_data_by_patient_id_failure(mock_execute_query):
    mock_execute_query.return_value = None  # Simulate no data found

    assert fetch_ecg_data_by_patient_id(123) is None # no result patient ecg data
