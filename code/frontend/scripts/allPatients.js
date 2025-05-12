document.addEventListener("DOMContentLoaded", function() {
    // Check if we need to bypass cache (when coming from upload page)
    const bypassCache = window.location.search.includes('refresh=');
    
    // Fetch patient data with appropriate caching options
    fetch('/api/patients_info', {
        // Add cache control headers if we're refreshing the page
        headers: bypassCache ? {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        } : {}
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch patient data');
            }
            return response.json();
        })
        .then(data => {
            if (data.success && Array.isArray(data.data)) {
                const patients = data.data;
                console.log(patients);
                const tableBody = document.getElementById('patients-table-body');
                // Clear existing rows to avoid duplicates when refreshing
                tableBody.innerHTML = '';
                
                patients.forEach(patient => {
                    const row = document.createElement('tr');
                    
                    const patientId = patient.patient_id;
                    const age = patient.age;
                    const gender = patient.gender;
                    const heart_rhythm = patient.heart_rhythm;
                    const hypertrophies = Array.isArray(patient.hypertrophies)
                        ? patient.hypertrophies
                        : patient.hypertrophies
                        ? JSON.parse(patient.hypertrophies)
                        : [];
                    const ischemia = Array.isArray(patient.ischemia)
                        ? patient.ischemia
                        : patient.ischemia
                        ? JSON.parse(patient.ischemia)
                        : [];
                    const conductionSystemDisease = Array.isArray(patient.conduction_system_disease)
                        ? patient.conduction_system_disease
                        : patient.conduction_system_disease
                        ? JSON.parse(patient.conduction_system_disease)
                        : [];
                    const cardiacPacing = Array.isArray(patient.cardiac_pacing)
                        ? patient.cardiac_pacing
                        : patient.cardiac_pacing
                        ? JSON.parse(patient.cardiac_pacing)
                        : [];
                    const repolarization_abnormalities = patient.repolarization_abnormalities || 'None';

                    // Format the parsed data for display
                    const hypertrophiesDisplay = hypertrophies.length > 0 ? hypertrophies.join('<br><br>') : 'None';
                    const ischemiaDisplay = ischemia.length > 0 ? ischemia.join('<br><br>') : 'None';
                    const conductionDisplay =
                        conductionSystemDisease.length > 0 ? conductionSystemDisease.join('<br><br>') : 'None';
                    const pacingDisplay = cardiacPacing.length > 0 ? cardiacPacing.join('<br><br>') : 'None';
                    row.innerHTML = `
                        <td class="patient-id">${patientId}</td>
                        <td>${age}</td>
                        <td>${gender}</td>
                        <td>${heart_rhythm}</td>
                        <td>${pacingDisplay}</td>
                        <td>${conductionDisplay}</td>
                        <td>${hypertrophiesDisplay}</td>
                        <td>${ischemiaDisplay}</td>
                        <td>${repolarization_abnormalities}</td>
                        <td class="actions">
                            <div class="buttons-container">
                                <button class="button view-button" onclick="viewECG(${patient.patient_id})">View ECG</button>
                                <button class="button delete-button" onClick="deletePatient(${patient.patient_id})">Delete</button>
                            </div>
                            
                        </td>
                    `;
                    tableBody.appendChild(row);
                });
            } else {
                throw new Error('Invalid data format');
            }
        })
        .catch(error => {
            console.error('Error fetching patient data:', error);
            alert('Failed to load patient data. Please try again later.');
        });
});

function viewECG(patientId) {
    localStorage.setItem("selectedPatientId", patientId); // ✅ Save patient ID
    
    // For tests, set the location directly
    if (typeof process !== 'undefined' && process.env.NODE_ENV === 'test') {
        window.location.href = `/patients/${patientId}`;
    } else {
        // In production, open in a new tab
        window.open(`/patients/${patientId}`, '_blank');
    }
}

function deletePatient(patientId) {
    if (confirm("Are you sure you want to delete this patient?")) {
        fetch(`/api/delete_patient/${patientId}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to delete patient');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                alert(data.message || 'Patient deleted successfully!'); 

                // Dynamically remove the row from the table
                const tableBody = document.getElementById('patients-table-body');
                const rows = tableBody.querySelectorAll('tr');
                rows.forEach(row => {
                    const idCell = row.querySelector('.patient-id');
                    if (idCell && parseInt(idCell.textContent) === patientId) {
                        row.remove(); // Remove the row from the table
                    }
                });
            } else {
                alert(data.error || 'Failed to delete patient. Please try again later.');
            }
        })
        .catch(error => {
            console.error('Error deleting patient:', error);
            alert('Failed to delete patient. Please try again later.');
        });
    }
}

// Export functions for testing
if (typeof module !== 'undefined') {
    module.exports = {
        viewECG,
        deletePatient
    };
}