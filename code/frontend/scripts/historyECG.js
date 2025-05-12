window.addEventListener("DOMContentLoaded", () => {
    const patientId = localStorage.getItem("selectedPatientId");
    if (patientId) {
        fetch(`/api/load_ecg_data/${patientId}`)
            .then(res => res.json())
            .then(data => {
                if (!data.error) {
                    plotECGHighcharts(data); // your existing function
                } else {
                    console.error("ECG data not found for patient:", patientId);
                }
            });
    }
});

function getPatientIdFromURL() {
    const path = window.location.pathname; // Get the current route (e.g., "/ecgHistory/1")
    const segments = path.split('/'); // Split the route into segments
    return segments[segments.length - 1]; // Get the last segment (the patientId)
}

async function fetchECGData(patientId) {
    try {
        const response = await fetch(`/api/ecg_data/${patientId}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch ECG data: ${response.statusText}`);
        }

        const data = await response.json();

        // Check if the backend indicates the patient doesn't exist
        if (!data.success || !data.data) {
            throw new Error(`Patient with ID ${patientId} does not exist.`);
        }

        const ecgData = data.data;
        console.log("ECG Raw Data from Backend:", ecgData);

        // Add logic to display the ECG data on the page
    } catch (error) {
        console.error("Error fetching ECG data:", error);

        // Display an error message to the user
        const errorMessage = document.createElement('p');
        errorMessage.textContent = `Error: ${error.message}`;
        errorMessage.style.color = 'red';
        document.body.appendChild(errorMessage);
    }
}

function plotECGHighcharts(ecgData) {
    // Add logic to plot the ECG data using Highcharts
    const data = ecgData.data;

    let standardLeadOrder = ["i", "ii", "iii"]; // Reduced for testing
    let leadColors = {
        "i": "red", "ii": "blue", "iii": "green",
    };

    let patientID = data.patient_id ? data.patient_id : "Unknown";
    let yAxes = [];
    let ecgSeries = [];
    let numLeads = standardLeadOrder.length;
    
    // Create a series for each lead
    standardLeadOrder.forEach((lead, index) => {
        if (!data.values || !data.values[index]) {
            console.warn(`Warning: Lead ${lead} values not found in data`);
            return;
        }

        yAxes.push({
            id: `y-axis-${index}`,
            title: { text: lead.toUpperCase() },
            height: '30%',
            top: index * 33 + '%'
        });

        // Create data points for this lead
        const points = [];
        if (data.time && Array.isArray(data.time)) {
            data.time.forEach((t, i) => {
                if (data.values[index] && data.values[index][i] !== undefined) {
                    points.push([t, data.values[index][i]]);
                }
            });
        } else {
            // If no time provided, use indices
            data.values[index].forEach((val, i) => {
                points.push([i, val]);
            });
        }

        ecgSeries.push({
            name: lead.toUpperCase(),
            data: points,
            color: leadColors[lead],
            yAxis: index
        });
    });

    // Call Highcharts to create the chart
    Highcharts.chart('ecg-container', {
        chart: {
            type: 'line',
            zoomType: 'x'
        },
        title: {
            text: `ECG Data for Patient ${patientID}`
        },
        xAxis: {
            title: {
                text: 'Time (s)'
            }
        },
        yAxis: yAxes,
        tooltip: {
            shared: true,
            crosshairs: true
        },
        series: ecgSeries
    });
}

const patientId = getPatientIdFromURL();
fetchECGData(patientId);

// Export functions for testing
if (typeof module !== 'undefined') {
    module.exports = {
        getPatientIdFromURL,
        fetchECGData,
        plotECGHighcharts
    };
}