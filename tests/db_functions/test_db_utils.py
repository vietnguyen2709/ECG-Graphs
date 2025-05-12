import pytest
from unittest.mock import patch, MagicMock
from backend.db.utils import fetch_from_db, execute_query

def test_fetch_from_db_exception():
    with patch('backend.db.utils.get_db_connection_safe', side_effect=Exception("DB connection failed")):
        result = fetch_from_db("SELECT * FROM patients")
        assert not result["success"]
        assert "DB connection failed" in result["error"]

def test_execute_query_fetch_all(): # test fetching all patients
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
                {
            "patient_id": 1,
            "gender": "F",
            "age": 51,
            "heart_rhythm": "Sinus bradycardia",
            "conduction_system_disease": "[]",
            "cardiac_pacing": "[]",
            "hypertrophies": '["Left ventricular hypertrophy"]',
            "ischemia": "[]",
            "repolarization_abnormalities": "posterior wall"
        },
        {
            "patient_id": 2,
            "gender": "M",
            "age": 64,
            "heart_rhythm": "Sinus rhythm",
            "conduction_system_disease": "[]",
            "cardiac_pacing": "[]",
            "hypertrophies": '["Left atrial hypertrophy", "Left ventricular hypertrophy"]',
            "ischemia": "[]",
            "repolarization_abnormalities": "posterior wall"
        }
    ]

    with patch('backend.db.utils.get_db_connection_safe', return_value=mock_connection):
        result = execute_query("SELECT * FROM patients")
        assert result == mock_cursor.fetchall.return_value


def test_execute_query_fetch_one():
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {
        "patient_id": 1,
        "gender": "F",
        "age": 51,
        "heart_rhythm": "Sinus bradycardia",
        "conduction_system_disease": "[]",
        "cardiac_pacing": "[]",
        "hypertrophies": '["Left ventricular hypertrophy"]',
        "ischemia": "[]",
        "repolarization_abnormalities": "posterior wall"
    }

    with patch('backend.db.utils.get_db_connection_safe', return_value=mock_connection):
        result = execute_query("SELECT * FROM patients WHERE patient_id = 1", fetch_one=True)
        assert result == mock_cursor.fetchone.return_value

def test_execute_query_commit():
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

    with patch('backend.db.utils.get_db_connection_safe', return_value=mock_connection):
        # simulate inserting a patient record
        query = """
            INSERT INTO patients (
                patient_id, gender, age, heart_rhythm,
                conduction_system_disease, cardiac_pacing,
                hypertrophies, ischemia, repolarization_abnormalities
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            999, "F", 45, "Sinus rhythm",
            "[]", "[]",
            '["Left ventricular hypertrophy"]', "[]", "posterior wall"
        )
        execute_query(query, params)
        mock_connection.commit.assert_called_once()

#test exception case
def test_execute_query_exception():
    with patch('backend.db.utils.get_db_connection_safe', side_effect=Exception("DB error")):
        with pytest.raises(Exception) as excinfo:
            execute_query("SELECT * FROM patients")
        assert "DB error" in str(excinfo.value)
