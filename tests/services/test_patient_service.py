import pytest
from backend.services import patient_service
from backend.services.patient_service import validate_patient_info, add_patient, store_patient_and_ecg_data
from unittest.mock import patch


@pytest.fixture
def valid_patient_info():
    return {"anonymous_id": 3}


#fixture to test mock db insertion
@pytest.fixture
def patient_data(valid_patient_info):
    return {
        "patient_info": {
            **valid_patient_info,
            "gender": "M",
            "age": 53,
            "heart_rhythm": "Sinus rhythm.",
            "conduction_system_disease": [],
            "cardiac_pacing": [],
            "hypertrophies": ["Left atrial hypertrophy.", "Left ventricular hypertrophy."],
            "ischemia": ["lateral wall.", "inferior wall."],
            "repolarization_abnormalities": None
        },
        "time": [0, 1, 2],
        "signals": [0.1, 0.2, 0.3],
        "maxima_graph_data": [],
        "minima_graph_data": [],
        "baselines_graph_data": [],
    }


def test_validate_patient_info_missing():
    result = validate_patient_info({}) #empty patient info
    assert result["success"] is False
    assert "error" in result


def test_validate_patient_info_success(valid_patient_info):
    result = validate_patient_info(valid_patient_info)
    assert result["success"] is True


def test_add_patient_invalid_info(mocker):
    result = add_patient({})
    assert result["success"] is False
    assert "error" in result


def test_add_patient_already_exists(mocker, valid_patient_info):
    mocker.patch("backend.services.patient_service.patient_exists", return_value=True) #mock that patient already exists
    result = add_patient(valid_patient_info)
    assert result["success"] is False
    assert result["patient_exists"] is True


def test_add_patient_success(mocker, valid_patient_info):
    mocker.patch("backend.services.patient_service.patient_exists", return_value=False)
    mocker.patch("backend.services.patient_service.insert_patient_into_db", return_value=None)
    result = add_patient(valid_patient_info)
    assert result["success"] is True


def test_add_patient_db_exception(mocker, valid_patient_info):
    mocker.patch("backend.services.patient_service.patient_exists", return_value=False)
    mocker.patch("backend.services.patient_service.insert_patient_into_db", side_effect=Exception("DB error"))
    result = add_patient(valid_patient_info)
    assert result["success"] is False
    assert "DB error" in result["error"]


def test_store_patient_and_ecg_patient_exists(mocker, patient_data):
    #test store patient and ecg data
    mocker.patch("backend.services.patient_service.patient_exists", return_value=True)
    mocker.patch("backend.services.patient_service.insert_patient_into_db", return_value=None)
    mocker.patch("backend.services.patient_service.add_ecg_data", return_value={"success": True})

    result = store_patient_and_ecg_data(patient_data)
    assert result["success"] is True
    assert result["message"] == "Patient and ECG data stored successfully"


def test_store_patient_and_ecg_patient_insert_failure(mocker, patient_data):
    mocker.patch("backend.services.patient_service.add_patient", return_value={"success": False, "error": "Insert fail"})
    result = store_patient_and_ecg_data(patient_data)
    assert result["success"] is False
    assert "Insert fail" in result["error"]


def test_store_patient_and_ecg_ecg_exists(mocker, patient_data):
    mocker.patch("backend.services.patient_service.add_patient", return_value={"success": True})
    mocker.patch("backend.services.patient_service.add_ecg_data", return_value={"success": False, "ecg_exists": True})

    result = store_patient_and_ecg_data(patient_data)
    assert result["success"] is False #can not insert if ecg data already exists
    assert result["ecg_exists"] is True


def test_store_patient_and_ecg_success(mocker, patient_data):
    mocker.patch("backend.services.patient_service.add_patient", return_value={"success": True})
    mocker.patch("backend.services.patient_service.add_ecg_data", return_value={"success": True})

    result = store_patient_and_ecg_data(patient_data)
    assert result["success"] is True
    assert result["message"] == "Patient and ECG data stored successfully" # even when patient doesnt exist already we insert the new patient too



@patch('backend.services.patient_service.add_ecg_data')
@patch('backend.services.patient_service.add_patient')
def test_store_patient_and_ecg_data_ecg_failure(mock_add_patient, mock_add_ecg_data):
    # simulate successful patient addition
    mock_add_patient.return_value = {"success": True}

    # simulate ECG failure without ecg_exists
    mock_add_ecg_data.return_value = {
        "success": False,
        "error": "DB insertion failed"
    }

    data = {
        "patient_info": {"anonymous_id": "123"},
    }

    result = store_patient_and_ecg_data(data)
    assert result["success"] is False
    assert result["error"] == "DB insertion failed"


@patch('backend.services.patient_service.add_patient')
def test_store_patient_and_ecg_data_raises_exception(mock_add_patient):
    # simulate exception in add_patient
    mock_add_patient.side_effect = Exception("Simulated unexpected error")

    data = {
        "patient_info": {"anonymous_id": "123"},
    }

    result = store_patient_and_ecg_data(data)
    assert result["success"] is False
    assert "Simulated unexpected error" in result["error"]
