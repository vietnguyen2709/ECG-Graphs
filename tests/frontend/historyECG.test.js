import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { getPatientIdFromURL, fetchECGData, plotECGHighcharts } from '../../code/frontend/scripts/historyECG';

beforeEach(() => {
  // Setup DOM environment
  document.body.innerHTML = `
    <div id="ecg-container"></div>
    <div id="patient-info"></div>
  `;
  
  // Mock window.location
  Object.defineProperty(window, 'location', {
    value: {
      pathname: '/ecgHistory/123',
      href: '/ecgHistory/123'
    },
    writable: true
  });

  // Mock Highcharts for the plotting function
  global.Highcharts = {
    chart: vi.fn().mockReturnValue({
      renderer: {
        text: vi.fn().mockReturnValue({
          css: vi.fn().mockReturnValue({
            add: vi.fn()
          })
        })
      },
      xAxis: [{}],
      yAxis: [{}]
    })
  };

  // Mock fetch
  global.fetch = vi.fn();

  // Mock localStorage
  Object.defineProperty(window, 'localStorage', {
    value: {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn()
    },
    writable: true
  });
});

afterEach(() => {
  // Cleanup
  vi.restoreAllMocks();
  document.body.innerHTML = '';
});

describe('ECG History Page Functionality', () => {
  it('should extract patient ID from the URL', () => {
    const patientId = getPatientIdFromURL();
    expect(patientId).toBe('123');
  });
  
  it('should fetch ECG data for a patient', async () => {
    // Mock successful fetch response with proper ok property
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({ 
        success: true, 
        data: { 
          patient_id: '123',
          leads: ['i', 'ii', 'iii'],
          values: [[1,2,3], [4,5,6], [7,8,9]]
        } 
      })
    });
    
    // Call the function
    await fetchECGData('123');
    
    // Verify fetch was called with correct URL
    expect(global.fetch).toHaveBeenCalledWith('/api/ecg_data/123');
  });
  
  it('should handle errors when fetching ECG data', async () => {
    // Mock failed fetch response with proper ok property
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: false,
      statusText: 'Not Found'
    });
    
    // Mock console.error and document.createElement
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const mockErrorElement = {
      textContent: '',
      style: { color: '' }
    };
    vi.spyOn(document, 'createElement').mockReturnValue(mockErrorElement);
    vi.spyOn(document.body, 'appendChild').mockImplementation(() => {});
    
    // Call the function and expect it to handle the error
    await fetchECGData('999');
    
    // Verify error was logged
    expect(consoleErrorSpy).toHaveBeenCalled();
    expect(mockErrorElement.textContent).toContain('Error: Failed to fetch ECG data');
  });
  
  it('should handle missing data in API response', async () => {
    // Mock successful fetch with empty data
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({ 
        success: false
      })
    });
    
    // Mock console.error and document.createElement
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const mockErrorElement = {
      textContent: '',
      style: { color: '' }
    };
    vi.spyOn(document, 'createElement').mockReturnValue(mockErrorElement);
    vi.spyOn(document.body, 'appendChild').mockImplementation(() => {});
    
    // Call the function
    await fetchECGData('123');
    
    // Verify error was logged
    expect(consoleErrorSpy).toHaveBeenCalled();
    expect(mockErrorElement.textContent).toContain('Error: Patient with ID 123 does not exist');
  });
  
  it('should plot ECG data with Highcharts', () => {
    // Prepare test data
    const ecgData = {
      data: {
        patient_id: '123',
        leads: ['i', 'ii', 'iii'],
        time: [0, 0.1, 0.2],
        values: [[1,2,3], [4,5,6], [7,8,9]]
      }
    };
    
    // Call the function
    plotECGHighcharts(ecgData);
    
    // Verify Highcharts was called
    expect(global.Highcharts.chart).toHaveBeenCalled();
  });

  it('should handle DOMContentLoaded event with patient ID in localStorage', async () => {
    // Mock localStorage to return a patient ID
    window.localStorage.getItem.mockReturnValue('456');
    
    // Mock fetch response
    global.fetch = vi.fn().mockResolvedValueOnce({
      json: async () => ({
        data: {
          patient_id: '456',
          leads: ['i', 'ii', 'iii'],
          values: [[1,2,3], [4,5,6], [7,8,9]]
        }
      })
    });
    
    // Create spy for console.error
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    // Manually trigger the DOMContentLoaded event
    const event = new Event('DOMContentLoaded');
    window.dispatchEvent(event);
    
    // Verify localStorage was accessed
    expect(window.localStorage.getItem).toHaveBeenCalledWith('selectedPatientId');
    
    // Verify fetch was called with the correct URL
    expect(global.fetch).toHaveBeenCalledWith('/api/load_ecg_data/456');
  });
  
  it('should handle DOMContentLoaded event with error in ECG data', async () => {
    // Mock localStorage to return a patient ID
    window.localStorage.getItem.mockReturnValue('789');
    
    // Mock fetch response with an error
    global.fetch = vi.fn().mockResolvedValueOnce({
      json: async () => ({
        error: 'Patient not found'
      })
    });
    
    // Create spy for console.error
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    // Manually trigger the DOMContentLoaded event
    const event = new Event('DOMContentLoaded');
    window.dispatchEvent(event);
    
    // Wait for all promises to resolve
    await new Promise(resolve => setTimeout(resolve, 0));
    
    // Verify localStorage was accessed
    expect(window.localStorage.getItem).toHaveBeenCalledWith('selectedPatientId');
    
    // Verify fetch was called
    expect(global.fetch).toHaveBeenCalledWith('/api/load_ecg_data/789');
    
    // Verify error was logged
    expect(consoleErrorSpy).toHaveBeenCalledWith('ECG data not found for patient:', '789');
  });
  
  it('should plot ECG data without time array', () => {
    // Prepare test data without time array
    const ecgData = {
      data: {
        patient_id: '123',
        leads: ['i', 'ii', 'iii'],
        // No time array provided
        values: [[1,2,3], [4,5,6], [7,8,9]]
      }
    };
    
    // Call the function
    plotECGHighcharts(ecgData);
    
    // Verify Highcharts was called with correct data
    expect(global.Highcharts.chart).toHaveBeenCalled();
    
    // Check that the chart was called with index-based points since no time array was provided
    const chartCall = global.Highcharts.chart.mock.calls[0][1];
    expect(chartCall.series[0].data).toBeDefined();
  });
  
  it('should handle missing lead values in ECG data', () => {
    // Mock console.warn
    const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    
    // Prepare test data with missing values for some leads
    const ecgData = {
      data: {
        patient_id: '123',
        leads: ['i', 'ii', 'iii'],
        time: [0, 0.1, 0.2],
        values: [
          [1,2,3], // Lead i has values
          undefined, // Lead ii has no values
          [7,8,9]  // Lead iii has values
        ]
      }
    };
    
    // Call the function
    plotECGHighcharts(ecgData);
    
    // Verify warning was logged about missing values
    expect(consoleWarnSpy).toHaveBeenCalledWith(expect.stringContaining('Warning: Lead ii values not found in data'));
    
    // Verify Highcharts was still called with available data
    expect(global.Highcharts.chart).toHaveBeenCalled();
  });
  
  it('should handle missing patient ID in ECG data', () => {
    // Prepare test data without a patient ID
    const ecgData = {
      data: {
        // No patient_id provided
        leads: ['i', 'ii', 'iii'],
        time: [0, 0.1, 0.2],
        values: [[1,2,3], [4,5,6], [7,8,9]]
      }
    };
    
    // Call the function
    plotECGHighcharts(ecgData);
    
    // Verify Highcharts was called
    expect(global.Highcharts.chart).toHaveBeenCalled();
    
    // Check that the title contains "Unknown" for the patient ID
    const chartCall = global.Highcharts.chart.mock.calls[0][1];
    expect(chartCall.title.text).toContain('Unknown');
  });
});