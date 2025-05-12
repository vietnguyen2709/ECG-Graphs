import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../code")))
from backend.app import app
import pytest
import io
import zipfile
from unittest.mock import patch

@pytest.fixture
def client():
    """ Set up the Flask test client. """
    app.config['TESTING'] = True  # Enable test mode
    app.config['UPLOAD_FOLDER'] = "test_uploads"  # Use a test directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Ensure test directory exists
    return app.test_client()

def test_upload_no_file(client):
    """ Test uploading without a file """
    response = client.post('/upload', data={})
    assert response.status_code == 200 
    assert response.json == {"error": "No file part"}


def test_upload_empty_file(client):
    """ Test uploading with an empty file field. """
    data = {'file': (io.BytesIO(b''), '')} #empty file
    response = client.post('/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 200 
    assert response.json == {"error": "No selected file"}

@patch("backend.app.process_and_store_ecg_data")
def test_upload_valid_zip(mock_process_ecg, client):
    """ Test uploading with valid zip"""
    mock_process_ecg.return_value.json = {"storage_result": "success", "ecg_data": {"i": [0.1, 0.2, 0.3], "ii": [0.2, 0.3, 0.4], "iii": [0.3, 0.4, 0.5]}}

    zip_buffer = io.BytesIO()  # Create an in-memory ZIP file
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        zip_file.writestr('data/sample.hea', 'ECG data header content')  # Add a sample file
    
    zip_buffer.seek(0)

    data = {'file': (zip_buffer, 'test_ecg.zip')} # Simulate file upload

    response = client.post('/upload', data=data, content_type='multipart/form-data')

    assert "ecg_data" in response.json
    assert "i" in response.json["ecg_data"]  
    assert "ii" in response.json["ecg_data"]
    assert "iii" in response.json["ecg_data"]

    assert isinstance(response.json["ecg_data"]["i"], list)
    assert isinstance(response.json["ecg_data"]["ii"], list)
    assert isinstance(response.json["ecg_data"]["iii"], list)
    
    # Cleanup test folder
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER'], topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(app.config['UPLOAD_FOLDER'])


def test_upload_non_zip(client):
    """ Test uploading a non zipped file"""
    data = {'file': (io.BytesIO(b'Not zip file'), 'example.txt')}
    response = client.post('/upload', data=data, content_type='multipart/form-data')
    
    assert response.status_code == 200
    assert response.json == {"error": "Please upload a ZIP file containing ECG data."}


def test_upload_corrupted_zip(client):
    corrupt_zip = io.BytesIO(b'corrupt data')
    response = client.post('/upload', data={'file': (corrupt_zip, 'corrupt.zip')}, content_type='multipart/form-data')
    assert response.status_code == 400
    assert response.json == {"error": "Uploaded file is not a valid ZIP archive."}
