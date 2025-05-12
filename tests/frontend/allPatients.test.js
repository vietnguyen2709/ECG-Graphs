import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { viewECG, deletePatient } from '../../code/frontend/scripts/allPatients';

beforeEach(() => {
  // Setup DOM environment
  document.body.innerHTML = `
    <table id="patients-table">
      <tbody id="patients-table-body"></tbody>
    </table>
  `;
  
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
  
  // Mock window.location
  Object.defineProperty(window, 'location', {
    value: {
      href: '',
      search: ''
    },
    writable: true
  });

  // Reset fetch mock between tests
  global.fetch = vi.fn();
});

afterEach(() => {
  // Cleanup
  vi.restoreAllMocks();
  document.body.innerHTML = '';
});

describe('All Patients Page Functionality', () => {
  it('should save patient ID and navigate to patient page', () => {
    // Call the function with a test ID
    viewECG(123);
    
    // Verify localStorage was updated and navigation occurred
    expect(window.localStorage.setItem).toHaveBeenCalledWith('selectedPatientId', 123);
    expect(window.location.href).toBe('/patients/123');
  });
  
  it('should call deletePatient function', async () => {
    // Mock window.confirm to return true
    const originalConfirm = window.confirm;
    window.confirm = vi.fn(() => true);
    
    // Setup test table with a patient row
    const tableBody = document.getElementById('patients-table-body');
    tableBody.innerHTML = `
      <tr>
        <td class="patient-id">123</td>
        <td>45</td>
        <td>Male</td>
        <td>Normal</td>
        <td>None</td>
        <td>None</td>
        <td>None</td>
        <td>None</td>
        <td>None</td>
        <td class="actions">
          <div class="buttons-container">
            <button class="button view-button">View ECG</button>
            <button class="button delete-button">Delete</button>
          </div>
        </td>
      </tr>
    `;
    
    // Mock successful API response
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        success: true,
        message: 'Patient deleted successfully!'
      })
    });
    
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
    
    // Call the delete function
    deletePatient(123);
    
    // Check that confirm was called
    expect(window.confirm).toHaveBeenCalledWith("Are you sure you want to delete this patient?");
    
    // Need to wait for promises to resolve
    await new Promise(resolve => setTimeout(resolve, 0));
    
    // Verify alert was shown with success message
    expect(alertSpy).toHaveBeenCalledWith('Patient deleted successfully!');
    
    // Verify the row was removed from the table
    expect(tableBody.children.length).toBe(0);
    
    // Restore original confirm
    window.confirm = originalConfirm;
  });
  
  it('should handle errors when deleting a patient', async () => {
    // Mock window.confirm to return true
    const originalConfirm = window.confirm;
    window.confirm = vi.fn(() => true);
    
    // Mock failed API response
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        success: false,
        error: 'Database error'
      })
    });
    
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
    const consoleSpy = vi.spyOn(console, 'error');
    
    // Call the delete function
    deletePatient(123);
    
    // Need to wait for promises to resolve
    await new Promise(resolve => setTimeout(resolve, 0));
    
    // Verify alert was shown with error message
    expect(alertSpy).toHaveBeenCalledWith('Database error');
    
    // Restore original confirm
    window.confirm = originalConfirm;
  });
  
  it('should handle API errors when deleting a patient', async () => {
    // Mock window.confirm to return true
    const originalConfirm = window.confirm;
    window.confirm = vi.fn(() => true);
    
    // Mock network error
    global.fetch.mockRejectedValueOnce(new Error('Network error'));
    
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
    const consoleSpy = vi.spyOn(console, 'error');
    
    // Call the delete function
    deletePatient(123);
    
    // Need to wait for promises to resolve
    await new Promise(resolve => setTimeout(resolve, 0));
    
    // Verify console.error was called
    expect(consoleSpy).toHaveBeenCalled();
    
    // Verify alert was shown with generic error message
    expect(alertSpy).toHaveBeenCalledWith('Failed to delete patient. Please try again later.');
    
    // Restore original confirm
    window.confirm = originalConfirm;
  });
  
  it('should do nothing when user cancels deletion', () => {
    // Mock window.confirm to return false (user cancels)
    const originalConfirm = window.confirm;
    window.confirm = vi.fn(() => false);
    
    // Spy on fetch to ensure it's not called
    const fetchSpy = vi.spyOn(global, 'fetch');
    
    // Call the delete function
    deletePatient(123);
    
    // Verify fetch was not called since user canceled
    expect(fetchSpy).not.toHaveBeenCalled();
    
    // Restore original confirm
    window.confirm = originalConfirm;
  });

  it('should fetch and display patient data on page load', () => {
    // Create a mock DOM event
    const domContentLoadedEvent = new Event('DOMContentLoaded');
    
    // Mock successful API response
    const mockPatients = {
      success: true,
      data: [
        {
          patient_id: 123,
          age: 45,
          gender: 'Male',
          heart_rhythm: 'Normal',
          hypertrophies: JSON.stringify(['Left Ventricular']),
          ischemia: JSON.stringify(['Anterior']),
          conduction_system_disease: JSON.stringify(['First-degree AV block']),
          cardiac_pacing: JSON.stringify(['Dual-chamber']),
          repolarization_abnormalities: 'Present'
        },
        {
          patient_id: 456,
          age: 60,
          gender: 'Female',
          heart_rhythm: 'Irregular',
          hypertrophies: [],
          ischemia: [],
          conduction_system_disease: [],
          cardiac_pacing: [],
          repolarization_abnormalities: 'None'
        }
      ]
    };
    
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockPatients)
    });
    
    // Spy on console.log and console.error
    const consoleSpy = vi.spyOn(console, 'log');
    const errorSpy = vi.spyOn(console, 'error');
    
    // Dispatch the event to trigger the DOMContentLoaded handler
    document.dispatchEvent(domContentLoadedEvent);
    
    // Check that fetch was called
    expect(global.fetch).toHaveBeenCalledWith('/api/patients_info', { headers: {} });
    
    // Need to use an async approach to wait for promises to resolve
    return new Promise(resolve => {
      setTimeout(() => {
        const tableBody = document.getElementById('patients-table-body');
        expect(tableBody.children.length).toBe(2); // Two patients should be displayed
        
        // Check first patient's data is displayed correctly
        const firstRow = tableBody.children[0];
        expect(firstRow.querySelector('.patient-id').textContent).toBe('123');
        
        // Check that the buttons exist
        expect(firstRow.querySelector('.view-button')).not.toBeNull();
        expect(firstRow.querySelector('.delete-button')).not.toBeNull();
        
        resolve();
      }, 0);
    });
  });
  
  it('should handle API errors when fetching patient data', () => {
    // Create a mock DOM event
    const domContentLoadedEvent = new Event('DOMContentLoaded');
    
    // Mock failed API response
    global.fetch.mockRejectedValueOnce(new Error('API error'));
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
    const errorSpy = vi.spyOn(console, 'error');
    
    // Dispatch the event to trigger the DOMContentLoaded handler
    document.dispatchEvent(domContentLoadedEvent);
    
    // Need to use an async approach to wait for promises to resolve
    return new Promise(resolve => {
      setTimeout(() => {
        expect(errorSpy).toHaveBeenCalled();
        expect(alertSpy).toHaveBeenCalledWith('Failed to load patient data. Please try again later.');
        resolve();
      }, 0);
    });
  });
  
  it('should handle invalid data format from API', () => {
    // Create a mock DOM event
    const domContentLoadedEvent = new Event('DOMContentLoaded');
    
    // Mock invalid data response
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ success: false })
    });
    
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
    const errorSpy = vi.spyOn(console, 'error');
    
    // Dispatch the event to trigger the DOMContentLoaded handler
    document.dispatchEvent(domContentLoadedEvent);
    
    // Need to use an async approach to wait for promises to resolve
    return new Promise(resolve => {
      setTimeout(() => {
        expect(errorSpy).toHaveBeenCalled();
        expect(alertSpy).toHaveBeenCalledWith('Failed to load patient data. Please try again later.');
        resolve();
      }, 0);
    });
  });
  
  it('should use no-cache headers when refresh parameter is present', () => {
    // Set refresh parameter
    window.location.search = '?refresh=true';
    
    // Create a mock DOM event
    const domContentLoadedEvent = new Event('DOMContentLoaded');
    
    // Mock successful API response
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ 
        success: true, 
        data: [] 
      })
    });
    
    // Dispatch the event to trigger the DOMContentLoaded handler
    document.dispatchEvent(domContentLoadedEvent);
    
    // Check that fetch was called with no-cache headers
    expect(global.fetch).toHaveBeenCalledWith('/api/patients_info', { 
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      } 
    });
    
    return Promise.resolve();
  });
  
  it('should handle different types of data arrays', () => {
    // Create a mock DOM event
    const domContentLoadedEvent = new Event('DOMContentLoaded');
    
    // Mock successful API response with different data types
    const mockPatients = {
      success: true,
      data: [
        {
          patient_id: 123,
          age: 45,
          gender: 'Male',
          heart_rhythm: 'Normal',
          // Test Array
          hypertrophies: ['Left Ventricular'],
          // Test JSON string
          ischemia: JSON.stringify(['Anterior']),
          // Test null value
          conduction_system_disease: null,
          // Test undefined
          cardiac_pacing: undefined,
          repolarization_abnormalities: 'Present'
        }
      ]
    };
    
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockPatients)
    });
    
    // Dispatch the event to trigger the DOMContentLoaded handler
    document.dispatchEvent(domContentLoadedEvent);
    
    // Need to use an async approach to wait for promises to resolve
    return new Promise(resolve => {
      setTimeout(() => {
        const tableBody = document.getElementById('patients-table-body');
        expect(tableBody.children.length).toBe(1);
        
        // The test passes if no errors are thrown when processing different data types
        resolve();
      }, 0);
    });
  });
});