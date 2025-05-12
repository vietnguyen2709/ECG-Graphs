import pytest
from backend.services.ecg_service import add_ecg_data, validate_ecg_data

# mock insert_ecg_data_into_db and ecg_data_exists from the backend/db/ecg.py
from backend.db import ecg as ecg_db

@pytest.fixture
def valid_ecg_data():
    return {
        "time": [0, 1, 2],
        "signals": [0.1, 0.2, 0.3],
        "maxima_graph_data": [],
        "minima_graph_data": [],
        "baselines_graph_data": []
    }

def test_validate_ecg_data_success(valid_ecg_data):
    result = validate_ecg_data(valid_ecg_data)
    assert result["success"] is True # using valid ecg data fixture we should get success

def test_validate_ecg_data_missing_key(valid_ecg_data):
    del valid_ecg_data["time"]
    result = validate_ecg_data(valid_ecg_data)
    assert result["success"] is False # removing necessary keys from the data will result in no success
    assert "Missing required key: time" in result["error"]

def test_add_ecg_data_success(valid_ecg_data, mocker):
    # test adding ecg data helper function
    mocker.patch("backend.services.ecg_service.ecg_data_exists", return_value=False)
    mocker.patch("backend.services.ecg_service.insert_ecg_data_into_db", return_value=None)

    result = add_ecg_data("123", valid_ecg_data)
    assert result["success"] is True

def test_add_ecg_data_missing_key(valid_ecg_data, mocker):
    #test trying to add with missing signal key
    del valid_ecg_data["signals"]
    result = add_ecg_data("123", valid_ecg_data)
    assert result["success"] is False
    assert "Missing required key: signals" in result["error"]

def test_add_ecg_data_already_exists(valid_ecg_data, mocker):
    # test when the ecg data already exists in the db
    mocker.patch("backend.services.ecg_service.ecg_data_exists", return_value=True)
    mocker.patch("backend.services.ecg_service.insert_ecg_data_into_db", ...)
    
    result = add_ecg_data("123", valid_ecg_data)
    assert result["success"] is False
    assert result["ecg_exists"] is True

def test_add_ecg_data_db_exception(valid_ecg_data, mocker):
    mocker.patch("backend.services.ecg_service.ecg_data_exists", return_value=False)
    mocker.patch("backend.services.ecg_service.insert_ecg_data_into_db", side_effect=Exception("DB error"))
    result = add_ecg_data("123", valid_ecg_data)
    assert result["success"] is False
    assert "DB error" in result["error"]
