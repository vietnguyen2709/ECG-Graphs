import io
import zipfile
import os
import pytest
from unittest.mock import patch
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../code")))
from backend.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['UPLOAD_FOLDER'] = 'test_uploads'
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    yield app.test_client()
    # Clean up
    for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER'], topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(app.config['UPLOAD_FOLDER'])

def create_test_zip_with_hea():
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, 'w') as zf:
        zf.writestr('patient1.hea', 'mock content')
    mem_zip.seek(0)
    return mem_zip

def test_upload_no_file(client):
    response = client.post('/uploadMultiplePatients', data={})
    assert response.status_code == 200
    assert response.get_json()['error'] == 'No file part'

def test_upload_empty_file(client):
    data = {'file': (io.BytesIO(), '')}
    response = client.post('/uploadMultiplePatients', content_type='multipart/form-data', data=data)
    assert response.status_code == 200
    assert response.get_json()['error'] == 'No selected file'

def test_upload_non_zip(client):
    data = {'file': (io.BytesIO(b'not a zip'), 'file.txt')}
    response = client.post('/uploadMultiplePatients', content_type='multipart/form-data', data=data)
    assert response.status_code == 200
    assert response.get_json()['error'] == 'Please upload a ZIP file containing ECG data.'

def test_upload_bad_zip(client):
    bad_zip = io.BytesIO(b'This is not a real zip file')
    data = {'file': (bad_zip, 'bad.zip')}
    response = client.post('/uploadMultiplePatients', content_type='multipart/form-data', data=data)
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Uploaded file is not a valid ZIP archive.'

@patch('backend.app.get_ecg_data')
@patch('backend.app.store_patient_and_ecg_data')
def test_upload_valid_zip(mock_store, mock_get, client):
    mock_get.return_value = {"ecg": "some data"}
    mock_store.return_value = "success"

    test_zip = create_test_zip_with_hea()
    data = {'file': (test_zip, 'patients.zip')}

    response = client.post('/uploadMultiplePatients', content_type='multipart/form-data', data=data)
    assert response.status_code == 200
    json_data = response.get_json()
    assert "patients" in json_data
    assert len(json_data["patients"]) == 1
    assert json_data["patients"][0]["file"] == "patient1.hea"
    assert json_data["patients"][0]["result"] == "success"


@patch('backend.app.get_ecg_data')
@patch('backend.app.store_patient_and_ecg_data')
def test_upload_valid_zip_with_error_in_ecg(mock_store, mock_get, client):
    mock_get.return_value = {"error": "Invalid ECG format"}

    test_zip = create_test_zip_with_hea()
    data = {'file': (test_zip, 'patients_with_error.zip')}

    response = client.post('/uploadMultiplePatients', content_type='multipart/form-data', data=data)
    assert response.status_code == 200

    json_data = response.get_json()
    assert "patients" in json_data
    assert len(json_data["patients"]) == 1
    assert json_data["patients"][0]["file"] == "patient1.hea"
    assert json_data["patients"][0]["error"] == "Invalid ECG format"
