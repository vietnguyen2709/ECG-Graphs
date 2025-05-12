import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../code")))
from backend.app import app
import pytest
from unittest.mock import patch, MagicMock
import io
import tempfile
import zipfile

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


def test_index_route(client):
    """test that the index page loads successfully"""
    response = client.get('/')
    assert response.status_code == 200
    assert b"<!DOCTYPE html>" in response.data  #HTML returned

def test_all_patients_route(client):
    """/allPatients route renders the allPatients html page"""
    response = client.get('/allPatients')
    assert response.status_code == 200
    assert b'<h1>Patient History</h1>' in response.data
    assert b'<title>History</title>' in response.data

@patch('backend.app.fetch_patient_by_id')
def test_ecg_history_route_with_valid_patient_id(mock_fetch_patient, client):
    """/ecgHistory route renders the historyECG html page with a existing patient_id"""
    mock_fetch_patient.return_value = {
        "patient_id": 3,
        "name": "John Doe"
    }

    patient_id = 3
    response = client.get(f'/ecgHistory/{patient_id}')

    assert response.status_code == 200
    assert b'<title>Cardio Vision</title>' in response.data


def test_ecg_history_route_with_invalid_patient_id(client):
    """/ecgHistory route handles an invalid or non-existent patient_id"""
    invalid_patient_id = 99999
    response = client.get(f'/ecgHistory/{invalid_patient_id}')
    assert response.status_code == 404  
    assert b"Patient not found" in response.data

def test_db_connection_success(client):
    """mock get_db_connection to return a successful connection"""
    with patch('backend.app.get_db_connection_safe') as mock_db_connection:
        mock_conn = MagicMock()
        mock_db_connection.return_value = mock_conn

        response = client.get('/api/test_db_connection')

        assert response.status_code == 200
        assert response.json == {"success": True}

def test_db_connection_failure(client):
    """mock get_db_connection to raise exception"""
    with patch('backend.app.get_db_connection_safe') as mock_db_connection:
        mock_db_connection.side_effect = Exception("Database connection failed")
        
        response = client.get('/api/test_db_connection')

        assert response.status_code == 500
        assert response.json == {"error": "Database connection failed"}


def test_all_patients_page(client):
    response = client.get('/allPatients')
    assert response.status_code == 200
    assert b'<title>History</title>' in response.data
    assert b'<h1>Patient History</h1>' in response.data


def test_upload_many_page(client):
    response = client.get('/uploadPatients')
    assert response.status_code == 200
    assert b'<title>ECG Uploads</title>' in response.data
    assert b'<h1>Upload One or Mutliple Zip Files</h1>' in response.data
    
    

def test_upload_multiple_patients_page(client):
    response = client.get('/uploadPatientsOneZip')
    assert response.status_code == 200
    assert b'<title>ECG Upload</title>' in response.data
    assert b'<h1>Upload a ZIP File for a dataset</h1>' in response.data

def test_get_all_patients_route_empty(client, mocker):
    mocker.patch("backend.app.fetch_all_patients", return_value=[])
    response = client.get("/api/patients_info")
    assert response.status_code == 200
    assert response.json == []

def test_get_all_patients_route_non_empty(client, mocker):
    # Mock patient data
    mocker.patch("backend.app.fetch_all_patients", return_value=[
        {"patient_id": 1, "name": "John Doe", "age": 45},
        {"patient_id": 2, "name": "Jane Smith", "age": 50}
    ])
    response = client.get("/api/patients_info")

    assert response.status_code == 200
    assert response.json == [
        {"patient_id": 1, "name": "John Doe", "age": 45},
        {"patient_id": 2, "name": "Jane Smith", "age": 50}
    ]


def test_get_patient_info_route(client, mocker):
    mocker.patch("backend.app.fetch_patient_by_id", return_value={"name": "Test Patient"})
    response = client.get("/api/patients_info/1")
    assert response.status_code == 200
    assert response.json["name"] == "Test Patient"
    

def test_get_patient_ecg_data_route(client, mocker):
    mocker.patch("backend.app.fetch_ecg_data_by_patient_id", return_value={"signals": {}})
    response = client.get("/api/ecg_data/1")
    assert response.status_code == 200
    assert "signals" in response.json


@patch('backend.app.fetch_ecg_data_by_patient_id')
@patch('backend.app.fetch_patient_by_id')
def test_api_load_ecg_success(mock_fetch_patient, mock_fetch_ecg, client):
    # mock data
    mock_fetch_ecg.return_value = [{"timestamp": "2024-01-01", "value": 1.23}]
    mock_fetch_patient.return_value = {
        "data": [{"id": 1, "name": "John Doe", "age": 50}]
    }

    response = client.get("/api/load_ecg_data/1")
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["success"] is True
    assert "ecg_data" in json_data
    assert "patient_info" in json_data
    assert json_data["patient_info"]["name"] == "John Doe"


# test when ecg is not found
@patch('backend.app.fetch_ecg_data_by_patient_id')
def test_api_load_ecg_not_found(mock_fetch_ecg, client):
    mock_fetch_ecg.return_value = None  # simulate no data

    response = client.get("/api/load_ecg_data/999")
    assert response.status_code == 404
    json_data = response.get_json()
    assert "error" in json_data
