import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../code")))
from backend.app import app
from unittest.mock import patch

@patch("backend.app.fetch_all_result_vectors")
def test_get_all_result_vectors_success(mock_fetch):
    mock_fetch.return_value = [{"id": 1, "vector": [1, 2, 3]}]  # mock return

    with app.test_client() as client:
        response = client.get("/api/all_result_vectors")

    assert response.status_code == 200
    assert response.json == [{"id": 1, "vector": [1, 2, 3]}]


@patch("backend.app.fetch_all_result_vectors")
def test_get_all_result_vectors_exception(mock_fetch):
    mock_fetch.side_effect = Exception("Database failure")  # simulate exception

    with app.test_client() as client:
        response = client.get("/api/all_result_vectors")

    assert response.status_code == 500
    assert "error" in response.json
    assert response.json["error"] == "Database failure" # database error message in response
