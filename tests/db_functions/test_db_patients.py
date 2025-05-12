import pytest
from backend.db import patient
from unittest.mock import patch

@pytest.fixture
def sample_patient_info():
    return {
        "anonymous_id": "12345",
        "sex": "Male",
        "age": 45,
        "rhythm": "Normal",
        "conduction_system_disease": ["LBBB"],
        "cardiac_pacing": ["Pacemaker"],
        "hypertrophies": ["LVH"],
        "ischemia": ["Anterior"],
        "repolarization_abnormalities": "None"
    }

@patch("backend.db.patient.execute_query")
def test_patient_exists_true(mock_execute):
    mock_execute.return_value = {"patient_id": "12345"}
    assert patient.patient_exists("12345") is True

@patch("backend.db.patient.execute_query")
def test_patient_exists_false(mock_execute):
    mock_execute.return_value = None
    assert patient.patient_exists("99999") is False #correctly labels this patient as not existing

@patch("backend.db.patient.execute_query")
#test inserting sample patient
def test_insert_patient_into_db(mock_execute, sample_patient_info):
    patient.insert_patient_into_db(sample_patient_info)
    assert mock_execute.called

@patch("backend.db.patient.fetch_from_db")
def test_fetch_all_patients(mock_fetch):
    mock_fetch.return_value = [{"patient_id": "12345"}, {"patient_id": "67890"}, {"patient_id": "11223"}] # pass a few sample patients we will fetch
    result = patient.fetch_all_patients()
    assert isinstance(result, list)
    assert len(result) == 3
    assert result[0]["patient_id"] == "12345" # check that they are in the result of fetch
    assert result[1]["patient_id"] == "67890"
    assert result[2]["patient_id"] == "11223"


@patch("backend.db.patient.fetch_from_db")
def test_fetch_patient_by_id_found(mock_fetch):
    mock_fetch.return_value = {"data": {"patient_id": "12345"}} # mock return
    result = patient.fetch_patient_by_id("12345")
    assert "error" not in result # returning the patient info

@patch("backend.db.patient.fetch_from_db")
def test_fetch_patient_by_id_not_found(mock_fetch):
    mock_fetch.return_value = {}
    result = patient.fetch_patient_by_id("99999") #non existing id
    assert result == {"error": "Patient not found"}


#test deleting patient by id success case
def test_delete_patient_by_id_success():
    patient_id = "123"

    with patch('backend.db.patient.patient_exists') as mock_patient_exists, \
         patch('backend.db.patient.execute_query') as mock_execute_query:

        mock_patient_exists.return_value = True
        mock_execute_query.return_value = None

        result = patient.delete_patient_by_id(patient_id)

        assert result == {"success": True, "message": "Patient deleted successfully"}
        mock_patient_exists.assert_called_once_with(patient_id)
        mock_execute_query.assert_called_once_with('DELETE FROM patients WHERE patient_id = %s', (patient_id,))


# raise exception to make sure we hit that exception error
def test_delete_patient_by_id_exception():
    patient_id = "789"

    with patch('backend.db.patient.patient_exists') as mock_patient_exists, \
         patch('backend.db.patient.execute_query') as mock_execute_query:

        mock_patient_exists.return_value = True
        mock_execute_query.side_effect = Exception("Database error")

        result = patient.delete_patient_by_id(patient_id)

        assert result["success"] is False
        assert "An error occurred" in result["error"]
        assert "Database error" in result["error"]
        mock_patient_exists.assert_called_once_with(patient_id)
        mock_execute_query.assert_called_once_with('DELETE FROM patients WHERE patient_id = %s', (patient_id,))


# base case where patient is not found
def test_delete_patient_by_id_not_found():
    patient_id = "456"

    with patch('backend.db.patient.patient_exists') as mock_patient_exists:
        mock_patient_exists.return_value = False

        result = patient.delete_patient_by_id(patient_id)

        assert result == {"success": False, "error": "Patient not found"}
        mock_patient_exists.assert_called_once_with(patient_id)
