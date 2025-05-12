import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../code")))
from backend.app import get_ecg_data
import pytest
import numpy as np
import wfdb
from unittest.mock import patch


@pytest.fixture
def sample_ecg_data(tmp_path):
  """Create a temporary WFDB record with only i, ii, and iii lead"""
  base_dir = tmp_path
  base_name = "sample_ecg"
  base_path = base_path = str(base_dir / base_name)

  sampling_rate = 500
  time = np.linspace(0, 10, 5000)
  signals = np.array([
    np.sin(2 * np.pi * 1 * time), #simulation lead 1
    np.sin(2 * np.pi * 1.2 * time), #simulation lead 2
    np.sin(2 * np.pi * 1.5 * time) #simulation lead 3
  ]).T

  #save record
  wfdb.wrsamp(
    record_name=base_name,
    fs=sampling_rate,
    units=['mV', 'mV', 'mV'],
    sig_name=['i', 'ii', 'iii'],
    p_signal=signals,
    write_dir=str(base_dir)
  )
  return base_path


def test_get_ecg_data_valid(sample_ecg_data):
    """Test that get_ecg_data processes the valid ECG record that we made above"""
    result = get_ecg_data(sample_ecg_data)

    assert "time" in result
    assert "signals" in result
    assert "maxima_graph_data" in result
    assert "minima_graph_data" in result
    assert "baselines_graph_data" in result
    assert "patient_info" in result

    assert len(result["time"]) > 0
    assert all(lead in result["signals"] for lead in ["i", "ii", "iii"])
    assert isinstance(result["maxima_graph_data"], dict)
    assert isinstance(result["minima_graph_data"], dict)
    assert isinstance(result["baselines_graph_data"], dict)



def test_get_ecg_data_missing_leads(tmp_path):
  """Test handling of missing leads"""
  base_dir = tmp_path
  base_name = "missing_lead3_ecg"
  base_path = str(base_dir / base_name)

  sampling_rate = 500
  time = np.linspace(0, 10, 5000)
  #not including simulated lead 3
  signals = np.array([
    np.sin(2 * np.pi * 1 * time), #simulation lead 1
    np.sin(2 * np.pi * 1.2 * time), #simulation lead 2
  ]).T

  #save record
  wfdb.wrsamp(
    record_name=base_name,
    fs=sampling_rate,
    units=['mV', 'mV'],
    sig_name=['i', 'ii'],
    p_signal=signals,
    write_dir=str(base_dir)
  )
  res = get_ecg_data(base_path)

  #if we are missing leads we should not continue processing
  assert "error" in res
  assert res["message"] == "Required leads missing: iii"


def test_get_ecg_data_invalid_file(tmp_path):
  """Test handling of an invalid file"""
  base_path = tmp_path / "invalid_ecg"

  # Create an empty file
  with open(base_path, "w") as f:
    f.write("Invalid data")
  
  result = get_ecg_data(str(base_path))

  assert "error" in result
  assert "message" in result
  assert result["message"] == "Failed to process ECG data"


def test_get_ecg_data_no_file():
    """Test handling of a non existent file"""
    result = get_ecg_data("non_existent_path")
    assert "error" in result
    assert "message" in result
    assert result["message"] == "Failed to process ECG data"

@patch("backend.app.wfdb.rdrecord", side_effect=Exception("File read error"))
def test_get_ecg_data_read_failure(mock_wfdb):
    """test handling of a failure in reading ECG data"""
    result = get_ecg_data("invalid_path")
    assert "error" in result
    assert "Failed to process ECG data" in result["message"]


def test_get_ecg_data_unexpected_leads(tmp_path):
    base_name = "unexpected_leads_ecg"
    base_path = str(tmp_path / base_name)
    
    sampling_rate = 500
    time = np.linspace(0, 10, 5000)
    signals = np.array([
        np.sin(time),  
        np.cos(time),  
        np.tan(time)  
    ]).T
    
    wfdb.wrsamp(
        record_name=base_name,
        fs=sampling_rate,
        units=['mV', 'mV', 'mV'],
        sig_name=['p1', 'p2', 'p3'],  # unexpected lead names
        p_signal=signals,
        write_dir=str(tmp_path)
    )
    result = get_ecg_data(base_path)
    
    assert "error" in result


def test_get_ecg_data_missing_patient_info(tmp_path):
    """Test handling of missing patient information in a valid ECG record"""
    base_dir = tmp_path
    base_name = "missing_patient_info"
    base_path = str(base_dir / base_name)

    sampling_rate = 500
    time = np.linspace(0, 10, 5000)
    signals = np.array([
        np.sin(2 * np.pi * 1 * time),  # simulation lead 1
        np.sin(2 * np.pi * 1.2 * time),  # simulation lead 2
        np.sin(2 * np.pi * 1.5 * time)  # simulation lead 3
    ]).T

    wfdb.wrsamp(
        record_name=base_name,
        fs=sampling_rate,
        units=['mV', 'mV', 'mV'],
        sig_name=['i', 'ii', 'iii'],
        p_signal=signals,
        write_dir=str(base_dir)
    )

    result = get_ecg_data(base_path)

    assert "patient_info" in result
    assert result["patient_info"]["age"] is None
    assert result["patient_info"]["sex"] is None
    assert result["patient_info"]["rhythm"] is None #should keep default none value


def test_get_ecg_data_with_patient_info(tmp_path):
    """Test extracting patient info from the ECG record"""
    base_dir = tmp_path
    base_name = "patient_info_ecg"
    base_path = str(base_dir / base_name)

    sampling_rate = 500
    time = np.linspace(0, 10, 5000)
    signals = np.array([
        np.sin(2 * np.pi * 1 * time),  #simulation lead 1
        np.sin(2 * np.pi * 1.2 * time),  #simulation lead 2
        np.sin(2 * np.pi * 1.5 * time)  #simulation lead 3
    ]).T

    #create .hea file with patient info
    comments = [
        "<age>: 45",
        "<sex>: M",
        "Rhythm: Normal",
        "Hypertrophy: Left ventricular hypertrophy",
        "Non-specific repolarization abnormalities: None",
        "Ischemia: Anterior wall ischemia",
        "Undefined ischemia/scar/supp.NSTEMI: No",
        "Conduction block: AV block",
        "Pacing: Pacemaker implanted"
    ]

    wfdb.wrsamp(
        record_name=base_name,
        fs=sampling_rate,
        units=['mV', 'mV', 'mV'],
        sig_name=['i', 'ii', 'iii'],
        p_signal=signals,
        write_dir=str(base_dir),
        comments=comments
    )

    result = get_ecg_data(base_path)

    #extract patient info correctly
    assert result["patient_info"]["age"] == "45"
    assert result["patient_info"]["sex"] == "M"
    assert result["patient_info"]["rhythm"] == "Normal"
    assert "hypertrophies" in result["patient_info"]
    assert "repolarization_abnormalities" in result["patient_info"]
    assert "ischemia" in result["patient_info"]
    assert "conduction_system_disease" in result["patient_info"]
    assert "cardiac_pacing" in result["patient_info"]
