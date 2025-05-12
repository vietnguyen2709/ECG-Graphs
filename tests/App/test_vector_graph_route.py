import pytest
import io
import numpy as np
import matplotlib.pyplot as plt
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../code")))
from backend.app import app
import io
from unittest.mock import patch, MagicMock


@pytest.fixture
def valid_ecg_data():
    """sample to provide valid ECG data for testing"""
    time = np.linspace(0, 10, 1000)
    signals = np.column_stack([np.sin(time), np.cos(time), np.tan(time)])
    return signals, time

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_valid_vector_graph(valid_ecg_data, client):
    """test vector graph generation with valid ECG data"""
    signals, time = valid_ecg_data

    lead1_value = 5.0
    lead3_value = 7.0
    
    response = client.post('/api/vector-graph', json={
        'lead1': lead1_value,  # taking the first value from lead1
        'lead3': lead3_value   # taking the first value from lead3
    })

    assert response.status_code == 200
    response_json = response.json
    assert "image" in response_json
    assert isinstance(response_json["image"], str)
    assert "magnitude" in response_json
    assert "angle" in response_json
    assert isinstance(response_json["magnitude"], (int, float))
    assert isinstance(response_json["angle"], (int, float))


def test_invalid_vector_graph_missing_leads():
    """test vector graph generation with missing ECG leads"""
    app.config['TESTING'] = True
    client = app.test_client()

    response = client.post('/api/vector-graph', json={
        'lead1': [0.1, 0.2, 0.3],
        'lead2': [0.4, 0.5, 0.6] #missing lead 3
    })

    assert response.status_code == 400  #expected status of 400 for missing data
    assert response.json == {"error": "Missing lead1 or lead3 values"}


def test_invalid_vector_graph_data():
    """test vector graph generation with invalid ECG data"""
    app.config['TESTING'] = True
    client = app.test_client()

    response = client.post('/api/vector-graph', json={
        'lead1': "invalid_data", #invalid format
        'lead2': [0.4, 0.5, 0.6],
        'lead3': [0.7, 0.8, 0.9]
    })
    assert response.status_code == 400  #expecting 400 for invalid data format


@patch("backend.app.Display_Vector", side_effect=Exception("Graphing Error"))
def test_vector_graph_failure(mock_display, client):
    """ Test vector-graph route when Display_Vector fails """
    response = client.post('/api/vector-graph', json={"lead1": 1.0, "lead3": 2.0})
    assert response.status_code == 400
    assert "error" in response.get_json()
    

def test_vector_graph_large_values(client):
    response = client.post('/api/vector-graph', json={"lead1": 1e6, "lead3": -1e6})
    assert response.status_code == 200
    assert "magnitude" in response.json
    assert "angle" in response.json


def test_vector_graph_negative_values(client):
    response = client.post('/api/vector-graph', json={"lead1": -0.5, "lead3": -1.2})
    assert response.status_code == 200
    assert response.json["magnitude"] > 0
    assert "angle" in response.json


test_data = {
    "anonymous_id": "3",
    "leadDataArray": [
        {
            "lead": 1,
            "startTime": "2025-03-25 10:00:00",
            "endTime": "2025-03-25 10:01:00",
            "avgBaseline": 0.2,
            "maxBeat": 0.5,
            "minBeat": 0.1,
            "correctedMaxPeak": 0.4,
            "correctedMinPeak": 0.1,
            "leadVector": [0.1, 0.2, 0.3]
        },
        {
            "lead": 2,
            "startTime": "2025-03-25 10:01:00",
            "endTime": "2025-03-25 10:02:00",
            "avgBaseline": 0.25,
            "maxBeat": 0.55,
            "minBeat": 0.15,
            "correctedMaxPeak": 0.45,
            "correctedMinPeak": 0.15,
            "leadVector": [0.4, 0.5, 0.6]
        },
        {
            "lead": 3,
            "startTime": "2025-03-25 10:02:00",
            "endTime": "2025-03-25 10:03:00",
            "avgBaseline": 0.3,
            "maxBeat": 0.6,
            "minBeat": 0.2,
            "correctedMaxPeak": 0.5,
            "correctedMinPeak": 0.2,
            "leadVector": [0.7, 0.8, 0.9]
        }
    ]
}


# @patch('backend.app.get_db_connection_safe')
# def test_post_result_vector_success(mock_db_connection, client):
#     mock_conn = MagicMock()
#     mock_cursor = MagicMock()
#     mock_cursor.fetchone.return_value = {"patient_id": "12345"}
#     mock_cursor.execute.return_value = None
#     mock_conn.cursor.return_value = mock_cursor
#     mock_conn.commit = MagicMock()

#     mock_db_connection.return_value = mock_conn
    
#     response = client.post('/api/post_result_vector', json=test_data)

#     assert response.status_code == 200
#     assert response.json == {"success": True, "message": "Result vector stored successfully"}


def test_post_result_vector_missing_anonymous_id(client):
    test_data = {
        "beat_data": {
            "Lead 1": [0.1, 0.2, 0.3],
            "Lead 2": [0.4, 0.5, 0.6],
            "Lead 3": [0.7, 0.8, 0.9]
        }
    }
    
    response = client.post('/api/post_result_vector', json=test_data)

    assert response.status_code == 400
    assert response.json == {"success": False, "error": "Missing anonymous_id"}


def test_post_result_vector_db_error(client):
    test_data = {
        "anonymous_id": "3",
        "leadDataArray": [
            {
                "lead": 1,
                "startTime": "2025-03-25 10:00:00",
                "endTime": "2025-03-25 10:01:00",
                "avgBaseline": 0.2,
                "maxBeat": 0.5,
                "minBeat": 0.1,
                "correctedMaxPeak": 0.4,
                "correctedMinPeak": 0.1,
                "leadVector": [0.1, 0.2, 0.3]
            }
        ]
    }
    with patch('backend.db.result_vector.execute_query') as mock_execute_query:
        mock_execute_query.side_effect = Exception("Database connection error")
        
        response = client.post('/api/post_result_vector', json=test_data)
        print(response.json)
        assert response.status_code == 500
        assert response.json == {"error": "Database connection error", "success": False} # exception error



@patch('backend.app.add_result_vector')
def test_post_result_vector_success(mock_add_result_vector, client):
    mock_add_result_vector.return_value = {"success": True, "message": "Stored successfully"}

    data = {
        "anonymous_id": "123",
        "vector": [0.1, 0.2, 0.3]
    }

    response = client.post('/api/post_result_vector', json=data)
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["success"] is True


@patch('backend.app.add_result_vector')
def test_post_result_vector_exception(mock_add_result_vector, client):
    #simulate exception
    mock_add_result_vector.side_effect = Exception("Something broke")

    data = {
        "anonymous_id": "123",
        "vector": [0.1, 0.2, 0.3]
    }

    response = client.post('/api/post_result_vector', json=data)
    assert response.status_code == 500 # error code
    json_data = response.get_json()
    assert json_data["success"] is False
    assert "error" in json_data


# test get_result_vectors_by_patient_id_route
@patch("backend.app.fetch_result_vectors_by_patient_id")
def test_get_result_vectors_by_patient_id_success(mock_fetch):
    mock_fetch.return_value = [{"vector": [1, 2, 3], "patient_id": "123"}]

    with app.test_client() as client:
        response = client.get("/api/result_vectors/123")
    
    assert response.status_code == 200
    assert response.json == [{"vector": [1, 2, 3], "patient_id": "123"}]

@patch("backend.app.fetch_result_vectors_by_patient_id")
def test_get_result_vectors_by_patient_id_exception(mock_fetch):
    mock_fetch.side_effect = Exception("Something went wrong")

    with app.test_client() as client:
        response = client.get("/api/result_vectors/123")

    assert response.status_code == 500
    assert "error" in response.json
    assert response.json["error"] == "Something went wrong"
