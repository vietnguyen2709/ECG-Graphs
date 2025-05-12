import pytest
from backend.services.result_vector_service import add_result_vector, validate_result_vector_data
import backend.services.result_vector_service as rvs
from backend.app import app

def test_missing_anonymous_id():
    data = {"leadDataArray": []}
    result = validate_result_vector_data(data)
    assert result[1] == 400
    assert not result[0]["success"]
    assert "anonymous_id" in result[0]["error"]

def test_invalid_lead_data_array():
    data = {"anonymous_id": "123", "leadDataArray": "not_a_list"}
    result = validate_result_vector_data(data)
    assert result[1] == 400
    assert not result[0]["success"]
    assert "leadDataArray" in result[0]["error"]

def test_add_result_vector_validation_error():
    data = {"leadDataArray": []}  # Missing anonymous_id
    with app.app_context():
      response, status_code = add_result_vector(data)
      assert status_code == 400
      assert response.get_json()["success"] is False
      assert "anonymous_id" in response.get_json()["error"]

def test_add_result_vector_success(monkeypatch):
    # Patch DB methods
    monkeypatch.setattr(rvs, "insert_result_vector_into_db", lambda x: None)
    monkeypatch.setattr(rvs, "process_result_vector", lambda x: {"dummy": "data"})

    data = {
        "anonymous_id": "123",
        "leadDataArray": []
    }
    result = add_result_vector(data)
    assert result["success"] is True
    assert result["message"] == "Result vector stored successfully"
