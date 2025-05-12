function populatePatientsTable(patients) {
    const tableBody = document.getElementById("patients-table-body");
    tableBody.innerHTML = "";

    patients.forEach(patient => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${patient.anonymous_id}</td>
            <td>${patient.age}</td>
            <td>${patient.gender}</td>
            <td>${patient.heart_rhythm}</td>
            <td>${patient.cardiac_pacing}</td>
            <td>${patient.conduction_disease}</td>
            <td>${patient.hypertrophies}</td>
            <td>${patient.ischemia}</td>
            <td>${patient.repolarization_abnormalities}</td>
            <td><button class="view-btn" data-id="${patient.anonymous_id}">View</button></td>
        `;

        tableBody.appendChild(row);
    });

    // Add click listener to each button
    document.querySelectorAll(".view-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const patientId = btn.dataset.id;
            window.location.href = `/view_patient/${patientId}`;
        });
    });
}

// Export functions for testing
if (typeof module !== 'undefined') {
    module.exports = {
        populatePatientsTable
    };
}
