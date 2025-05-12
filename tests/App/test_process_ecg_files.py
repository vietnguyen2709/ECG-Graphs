import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../code")))
from backend.app import process_and_store_ecg_data, extract_patient_info
import pytest
from flask import Flask
from unittest.mock import patch, MagicMock
from flask.wrappers import Response
import numpy as np
from backend.app import app
import tempfile
import shutil

@pytest.fixture
def sample_extracted_folder(tmp_path):
    test_folder = tmp_path / "ecg_test_folder_no_hea"
    data_folder = test_folder / "data"
    test_folder.mkdir()
    data_folder.mkdir(parents=True, exist_ok=True)
    return str(test_folder)

def test_no_hea_file(sample_extracted_folder):
    app = Flask(__name__)
    with app.test_request_context():
        result = process_and_store_ecg_data(sample_extracted_folder)

    assert result.status_code == 200
    assert result.get_json() == {'error': 'No valid ECG files found in the extracted ZIP.'} # update expected result

@pytest.fixture
def sample_extracted_folder_with_hea(tmp_path):
    test_folder = tmp_path / "ecg_test_folder_with_hea"
    data_folder = test_folder / "data"
    data_folder.mkdir(parents=True, exist_ok=True)
    
    hea_file = data_folder / "test.hea"  # dummy hea file
    hea_file.write_text("Dummy ECG header file content")
    
    return str(test_folder)

@patch("backend.app.get_ecg_data", return_value={"error": "Failed to process ECG data"})
def test_process_ecg_files_failure(mock_get_ecg_data, tmp_path):
    test_folder = tmp_path / "ecg_test_folder_with_hea"
    data_folder = test_folder / "data"
    data_folder.mkdir(parents=True, exist_ok=True)
    (data_folder / "test.hea").write_text("Dummy ECG header file content")

    app = Flask(__name__)
    with app.test_request_context():
        result = process_and_store_ecg_data(str(test_folder))

    assert "patient_results" in result.get_json()
    assert result.get_json()["patient_results"][0]["error"] == "Failed to process ECG data"


@patch("backend.app.get_ecg_data", return_value={"error": "No ECG data found"})
def test_process_empty_extracted_folder(mock_get_ecg_data, tmp_path):
    empty_folder = tmp_path / "empty_data_folder"
    empty_folder.mkdir()
    (empty_folder / "data").mkdir()

    app = Flask(__name__)
    with app.test_request_context():
        response = process_and_store_ecg_data(str(empty_folder)) #test processing and extracting operations

    assert response.status_code == 200
    assert response.get_json() == {"error": "No valid ECG files found in the extracted ZIP."}

def test_extract_patient_info_complete(tmp_path):
    base_dir = tmp_path
    base_name = "patient_info_complete"
    base_path = str(base_dir / base_name)

    comments = [
        "<age>: 60",
        "<sex>: M",
        "Rhythm: Normal",
        "<diagnoses>: Hypertension, Diabetes"
    ]

    with open(base_path + ".hea", "w") as f:
        for comment in comments:
            f.write(comment + "\n")

    result = extract_patient_info(base_path + ".hea")

    assert result["age"] == "60"
    assert result["sex"] == "M"
    assert result["rhythm"] == "Normal"
    assert result["diagnoses"] == "Hypertension, Diabetes"

@patch("backend.app.get_ecg_data")
@patch("backend.app.store_patient_and_ecg_data")
@patch("os.listdir")
def test_process_and_store_ecg_data_from_root(mock_listdir, mock_storing, mock_get_ecg_data, sample_extracted_folder_with_hea):
    # mock os.listdir to return a list with a .hea file in the root
    mock_listdir.return_value = ['test_file.hea']

    # mock get_ecg_data to return mock ECG data
    mock_get_ecg_data.return_value = {
        "patient_info": {"anonymous_id": "3"},
        "lead_1": [0.1, 0.2, 0.3],
        "lead_2": [0.4, 0.5, 0.6],
        "lead_3": [0.7, 0.8, 0.9]
    }
    
    #mock store_patient_and_ecg_data to return a success message
    mock_storing.return_value = {"success": True, "message": "Patient and ECG data stored successfully"}

    app = Flask(__name__)
    with app.test_request_context():
        result = process_and_store_ecg_data(sample_extracted_folder_with_hea)

    expected_json = {
        "storage_result": "Multiple patients processed",
        "patient_results": [
            {
                "file": "test_file.hea",
                "storage_result": {"success": True, "message": "Patient and ECG data stored successfully"}
            }
        ]
    }

    assert result.status_code == 200
    response_json = result.get_json()

    assert response_json["storage_result"] == expected_json["storage_result"]
    assert response_json["patient_results"] == expected_json["patient_results"]

    mock_get_ecg_data.assert_called_once_with(os.path.join(sample_extracted_folder_with_hea, 'test_file'))
    mock_storing.assert_called_once_with(mock_get_ecg_data.return_value)


@patch("backend.app.get_ecg_data", return_value={"error": "Mocked ECG parsing error"})
@patch("os.listdir", return_value=["test_file.hea"])
def test_process_and_store_ecg_data_error_in_root(mock_listdir, mock_get_ecg_data, tmp_path):
    test_folder = tmp_path / "test_root_error_case"
    test_folder.mkdir()

    app = Flask(__name__)
    with app.test_request_context():
        result = process_and_store_ecg_data(str(test_folder))

    assert result.status_code == 200
    response_json = result.get_json()

    assert "patient_results" in response_json
    assert response_json["patient_results"][0]["file"] == "test_file.hea"
    assert response_json["patient_results"][0]["error"] == "Mocked ECG parsing error"


@patch("backend.app.get_ecg_data", return_value={"error": "Mocked ECG parsing error"})
@patch("os.listdir", return_value=["test_file.hea"])
def test_process_single_patient_with_error_in_result(mock_listdir, mock_get_ecg_data, tmp_path):
    test_folder = tmp_path / "test_single_patient_with_error_in_result"
    test_folder.mkdir()

    # Simulate processing that leads to an error result
    patient_results = [{
        "file": "test_file.hea",
        "error": "Mocked ECG parsing error"
    }]
    
    app = Flask(__name__)
    with app.test_request_context():
        result = process_and_store_ecg_data(str(test_folder))

    assert result.status_code == 200
    response_json = result.get_json()

    # Check if the response contains the error message within patient_results
    assert "patient_results" in response_json
    assert "error" in response_json["patient_results"][0]
    assert response_json["patient_results"][0]["error"] == "Mocked ECG parsing error"


# coverage for lines 270-278 in process_and_store_ecg_data function
@patch("os.listdir")
@patch("backend.app.get_ecg_data")
@patch("backend.app.store_patient_and_ecg_data")
def test_process_multiple_patients_with_hea_files(mock_store, mock_get_ecg_data, mock_listdir):
    # create test folder
    test_folder = "test_folder"

    # patient results have been processed
    mock_listdir.return_value = ["test_patient1.hea", "test_patient2.hea"]
    mock_get_ecg_data.side_effect = [
        {"patient_info": {"anonymous_id": "123", "sex": "M", "age": 45}},
        {"patient_info": {"anonymous_id": "124", "sex": "F", "age": 50}}
    ]
    mock_store.return_value = {"message": "Patient and ECG data stored successfully", "success": True}

    with app.app_context():
        result = process_and_store_ecg_data(test_folder)
    
    # patient results should be returned
    assert result.status_code == 200
    assert "patient_results" in result.json
    assert len(result.json["patient_results"]) == 2
    assert result.json["storage_result"] == "Multiple patients processed"

    test_folder_no_hea = "test_no_hea_file_folder"
    mock_listdir.return_value = []  # Simulate no .hea files found

    with app.app_context():
        result_no_hea = process_and_store_ecg_data(test_folder_no_hea)
    
    # assert no valid ECG files found
    assert result_no_hea.status_code == 200
    assert result_no_hea.json["error"] == "No valid ECG files found in the extracted ZIP."

    test_folder_empty = "test_process_empty_extracted_f_folder"
    mock_listdir.return_value = []  # Simulate no files found
    
    with app.app_context():
        result_empty = process_and_store_ecg_data(test_folder_empty)
    
    # assert empty folder with no .hea files
    assert result_empty.status_code == 200
    assert result_empty.json["error"] == "No valid ECG files found in the extracted ZIP."

    # Folder path with no .hea files and no sub data folder
    test_folder_no_data = "test_no_data_folder"
    mock_listdir.return_value = []  # no hea found

    with app.app_context():
        result_no_data = process_and_store_ecg_data(test_folder_no_data)
    
    # assert missing .hea files and no sub data folder
    assert result_no_data.status_code == 200
    assert result_no_data.json["error"] == "'data' folder not found in extracted ZIP and no .hea files in root."



@patch("os.listdir")
@patch("backend.app.get_ecg_data")
@patch("backend.app.store_patient_and_ecg_data")
def test_process_valid_and_invalid_ecg_data(mock_store, mock_get_ecg_data, mock_listdir):
    # mock test floder
    test_folder = "test_folder"

    mock_listdir.return_value = ["test_patient1.hea"]
    
    # valid ECG data with patient info
    mock_get_ecg_data.return_value = {
        "patient_info": {"anonymous_id": "123", "sex": "M", "age": 45},
        "signals": {"lead1": [1, 2, 3], "lead2": [4, 5, 6]}
    }
    mock_store.return_value = {"message": "Patient and ECG data stored successfully", "success": True}

    with app.app_context():
        result = process_and_store_ecg_data(test_folder)
    
    # assert the result for valid ECG data
    assert result.status_code == 200
    assert "storage_result" in result.json
    assert "patient_results" in result.json
    assert result.json["patient_results"][0]["storage_result"]["success"] == True
    
    # Test valid .hea file with "test_valid_hea_file" in the folder path
    test_folder_valid = "test_valid_hea_file_folder"
    mock_listdir.return_value = ["test_patient1.hea"]

    # simulate return of get_ecg_data
    mock_get_ecg_data.return_value = {
        "patient_info": {"anonymous_id": "124", "sex": "F", "age": 30},
        "signals": {"lead1": [1, 2, 3], "lead2": [4, 5, 6]}
    }
    mock_store.return_value = {"message": "Patient and ECG data stored successfully", "success": True}

    with app.app_context():
        result_valid_hea = process_and_store_ecg_data(test_folder_valid)
    
    # assert the result for the test_valid_hea_file
    assert result_valid_hea.status_code == 200
    assert "ecg_data" in result_valid_hea.json
    assert "patient_info" in result_valid_hea.json["ecg_data"]
    assert result_valid_hea.json["storage_result"]["success"] == True
    
    # Test process failure with invalid folder path
    test_folder_failure = "test_process_ecg_files_failure_folder"
    mock_listdir.return_value = ["test_patient1.hea"]

    # simulate return of get_ecg_data for invalid folder path
    mock_get_ecg_data.return_value = {"error": "Invalid data"}
    
    with app.app_context():
        result_failure = process_and_store_ecg_data(test_folder_failure)
    
    # assert the result for the test_process_ecg_files_failure
    assert result_failure.status_code == 200
    assert "error" in result_failure.json
    assert result_failure.json["error"] == "Invalid data"
    
    # folder with no valid ECG files
    test_folder_no_hea = "test_no_hea_file_folder"
    mock_listdir.return_value = []  # Simulate no .hea files found

    with app.app_context():
        result_no_hea = process_and_store_ecg_data(test_folder_no_hea)
    
    #assert the result for no .hea files in the folder
    assert result_no_hea.status_code == 200
    assert result_no_hea.json["error"] == "No valid ECG files found in the extracted ZIP."


def test_process_ecg_data_in_data_folder():
    # make temp folder
    with tempfile.TemporaryDirectory() as temp_dir:
        data_dir = os.path.join(temp_dir, 'data')
        os.makedirs(data_dir)
        
        # Create dummy .hea file in the data sub-folder
        hea_file_path = os.path.join(data_dir, '1.hea')
        with open(hea_file_path, 'w') as f:
            f.write('Dummy header content')

        #mock get_ecg_data and store_patient_and_ecg_data
        with patch('backend.app.get_ecg_data') as mock_get_ecg_data, \
             patch('backend.app.store_patient_and_ecg_data') as mock_store_data:
            
            mock_get_ecg_data.return_value = {
                "time": [0, 0.004, 0.008],  # Example small time array
                "signals": {
                    "I": [0.1, 0.2, 0.3],
                    "II": [0.2, 0.3, 0.4]
                },
                "maxima_graph_data": {
                    "I": {
                        "maximas": [1],
                        "maxima_values": [0.2]
                    },
                    "II": {
                        "maximas": [1],
                        "maxima_values": [0.3]
                    }
                },
                "minima_graph_data": {
                    "I": {
                        "minimas": [2],
                        "minima_values": [0.1]
                    },
                    "II": {
                        "minimas": [2],
                        "minima_values": [0.2]
                    }
                },
                "baselines_graph_data": {
                    "I": 0.2,
                    "II": 0.3
                },
                "patient_info": {
                    "age": 45,
                    "sex": "M",
                    "rhythm": "Normal",
                    "anonymous_id": "123",
                    "hypertrophies": [],
                    "repolarization_abnormalities": None,
                    "ischemia": [],
                    "conduction_system_disease": [],
                    "cardiac_pacing": [],
                }
            }
            mock_store_data.return_value = "Data stored successfully"

            # create a new test_valid_hea_file folder inside temp_dir
            test_folder_path = os.path.join(temp_dir, "test_valid_hea_file")
            os.makedirs(test_folder_path)

            shutil.move(data_dir, test_folder_path)

            with app.app_context():
                response = process_and_store_ecg_data(test_folder_path)

                assert response.status_code == 200
                data = response.get_json()
                assert "storage_result" in data
                assert "ecg_data" in data
                assert data["storage_result"] == "Data stored successfully"
                assert data["ecg_data"]["patient_info"]["anonymous_id"] == "123"
                assert data["ecg_data"]["patient_info"]["age"] == 45
