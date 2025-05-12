from unittest.mock import patch
from backend.db import result_vector

def test_fetch_all_result_vectors():
    with patch('backend.db.result_vector.fetch_from_db') as mock_fetch:
        mock_fetch.return_value = [{"id": 1, "patient_id": "123"}]
        result = result_vector.fetch_all_result_vectors()
        assert result == [{"id": 1, "patient_id": "123"}]
        mock_fetch.assert_called_once_with('SELECT * FROM ecg_beat_selection')

def test_fetch_result_vectors_by_patient_id():
    with patch('backend.db.result_vector.fetch_from_db') as mock_fetch:
        mock_fetch.return_value = [{"id": 1, "patient_id": "123"}]
        result = result_vector.fetch_result_vectors_by_patient_id("123")
        assert result == [{"id": 1, "patient_id": "123"}]
        mock_fetch.assert_called_once_with('SELECT * FROM ecg_beat_selection WHERE patient_id = %s', ('123',))
