import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { populatePatientsTable } from '../../code/frontend/scripts/new_allPatients';

beforeEach(() => {
  // Setup DOM environment
  document.body.innerHTML = `
    <table>
      <tbody id="patients-table-body"></tbody>
    </table>
  `;
  
  // Mock window.location
  Object.defineProperty(window, 'location', {
    value: {
      href: ''
    },
    writable: true
  });
});

afterEach(() => {
  // Cleanup
  vi.restoreAllMocks();
  document.body.innerHTML = '';
});

describe('New All Patients Page Functionality', () => {
  it('should populate the patients table with data', () => {
    // Sample patient data
    const patients = [
      {
        anonymous_id: '123',
        age: 45,
        gender: 'Male',
        heart_rhythm: 'Sinus Rhythm',
        cardiac_pacing: 'None',
        conduction_disease: 'None',
        hypertrophies: 'Left Ventricular Hypertrophy',
        ischemia: 'None',
        repolarization_abnormalities: 'None'
      },
      {
        anonymous_id: '456',
        age: 60,
        gender: 'Female',
        heart_rhythm: 'Atrial Fibrillation',
        cardiac_pacing: 'None',
        conduction_disease: 'Right Bundle Branch Block',
        hypertrophies: 'None',
        ischemia: 'None',
        repolarization_abnormalities: 'ST depression'
      }
    ];
    
    // Call the function
    populatePatientsTable(patients);
    
    // Verify table was populated
    const tableBody = document.getElementById('patients-table-body');
    const rows = tableBody.querySelectorAll('tr');
    
    expect(rows.length).toBe(2);
    expect(rows[0].innerHTML).toContain('123');
    expect(rows[0].innerHTML).toContain('Male');
    expect(rows[0].innerHTML).toContain('45');
    expect(rows[1].innerHTML).toContain('456');
    expect(rows[1].innerHTML).toContain('Female');
    expect(rows[1].innerHTML).toContain('60');
  });
  
  it('should add click handlers to view buttons', () => {
    // Sample patient data with a single patient
    const patients = [
      {
        anonymous_id: '123',
        age: 45,
        gender: 'Male',
        heart_rhythm: 'Sinus Rhythm',
        cardiac_pacing: 'None',
        conduction_disease: 'None',
        hypertrophies: 'None',
        ischemia: 'None',
        repolarization_abnormalities: 'None'
      }
    ];
    
    // Call the function
    populatePatientsTable(patients);
    
    // Find the view button and click it
    const viewButton = document.querySelector('.view-btn');
    viewButton.click();
    
    // Verify navigation occurred to the correct URL
    expect(window.location.href).toBe('/view_patient/123');
  });
});