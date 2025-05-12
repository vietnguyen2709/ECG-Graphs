let graphDiv;
let beatSelectionPoints = [];
let flatSelectionPoints = [];
let selectedBeatShapes = [];
let selectedFlatShapes = [];
let originalTraces = [];
let maxMinAnnotations = [];
let avgFlatAnnotations = [];
let selectedBeatTraces = [];  // Stores red-highlighted beat selections
let selectedFlatTraces = [];  // Stores magenta-highlighted flat selections

let beatMode = false;  
let flatMode = false;  
let ecgData = {}; // Stores the ECG data for api and front end purposes
let selectedBeatData = null;
let selectedFlatData = null;

window.addEventListener("DOMContentLoaded", () => {
    const path = window.location.pathname;
    if (path.startsWith("/patients/")) {
      const patientId = path.split("/").pop();
      fetch(`/api/load_ecg_data/${patientId}`)
        .then(res => res.json())
        .then(data => {
          if (!data.error) {
            window.patientInfo = data.patient_info; // Save globally
            updatePatientInfo(data.patient_info);
            plotECGHighcharts({
                ...data.ecg_data,
                patient_info: data.patient_info
            });
            
          }
        });
    }
  });
  
function plotECGHighcharts(data) {
    let standardLeadOrder = ["i", "ii", "iii", "avr", "avl", "avf", "v1", "v2", "v3", "v4", "v5", "v6"];
    let leadColors = {
        "i": "white", "ii": "white", "iii": "white",
        "avr": "white", "avl": "white", "avf": "white",
        "v1": "white", "v2": "white", "v3": "white",
        "v4": "white", "v5": "white", "v6": "white"
    };

    let patientID = data.patient_info?.anonymous_id || data.patient_info?.patient_id || "Unknown";

    let yAxes = [];
    let ecgSeries = [];
    let numLeads = standardLeadOrder.length;
    let yAxisHeight = 100 / numLeads + 10;  // Adjust spacing between leads
    if (!data || !Array.isArray(data.time) || data.time.length === 0) {
        console.error("Invalid or missing ECG data.time array");
        return;
    }
    let originalXMin = data.time[0];  // Store original x-axis range
    let originalXMax = data.time[data.time.length - 1];

    standardLeadOrder.forEach((lead, index) => {
        if (!data.signals[lead]) {
            console.warn(`Warning: Lead ${lead} not found in data.signals`);
            return;
        }

        yAxes.push({
            id: `y-axis-${index}`,
            title: { text: lead.toUpperCase(), style: { color: leadColors[lead] } },
            top: `${index * (100 / numLeads) - 3}%`,  // Position each lead separately
            height: `${yAxisHeight}%`,
            offset: 0,
            lineWidth: 1,
            gridLineWidth: 0,
            gridLineColor: "#444",
            opposite: false,
            labels: { enabled: false}
        });

        ecgSeries.push({
            name: lead.toUpperCase(),
            data: data.signals[lead].map((y, i) => [data.time[i], y]),
            color: leadColors[lead] || "gray",
            yAxis: index,
            lineWidth: 1.5,
            marker: { 
                enabled: false,
                states: {
                    hover: {
                        enabled: false // Prevents dots on hover
                    }
                }
             }
        });
    });

    let chart = Highcharts.chart("ecgContainer", {
        chart: { 
            type: "line",
            backgroundColor: "#1e1e1e", 
            zoomType: "x", 
            panning: true, 
            panKey: "shift", 
            events: {
                load: function () {
                    const chart = this;
                    Highcharts.addEvent(chart.container, 'wheel', function (e) {
                        e.preventDefault();
            
                        let xAxis = chart.xAxis[0];
                        let extremes = xAxis.getExtremes();
                        let center = (extremes.min + extremes.max) / 2;
                        let range = extremes.max - extremes.min;
            
                        // Determine zoom factor (scroll up to zoom in, down to zoom out)
                        let zoomFactor = e.deltaY < 0 ? 0.9 : 1.1;
            
                        let newMin = center - (range * zoomFactor) / 2;
                        let newMax = center + (range * zoomFactor) / 2;
            
                        // Clamp zoom range to avoid going outside original data range
                        let dataMin = xAxis.dataMin;
                        let dataMax = xAxis.dataMax;
                        newMin = Math.max(dataMin, newMin);
                        newMax = Math.min(dataMax, newMax);
                        let originalXMin = data.time[0];
                        let originalXMax = data.time[data.time.length - 1];
                        chart.xAxis[0].setExtremes(newMin, newMax);
                        document.getElementById("resetScaleButton").style.display = "inline-block";
                        document.getElementById("resetScaleButton").addEventListener("click", function () {
                            chart.xAxis[0].setExtremes(originalXMin, originalXMax);
                            this.style.display = "none";
                            xScaleSelect.value = "1";
                            document.getElementById("scaleSelect").value = "1";
                        });
                    });
                    // === Create a container div inside the chart ===
                    const container = document.createElement("div");
                    container.style.position = "absolute";
                    container.style.top = "5px";
                    container.style.right = "10px"; // Position from right instead of left
                    container.style.zIndex = "5";
                    container.style.display = "flex";
                    container.style.gap = "10px";

                    // === Beat Mode Button ===
                    const beatBtn = document.createElement("button");
                    beatBtn.textContent = "Cardiac Beat";
                    beatBtn.id = "beatModeBtn";
                    beatBtn.className = "mode-btn";
                    beatBtn.style.backgroundColor = "#0f0";
                    beatBtn.style.padding = "5px 10px";
                    beatBtn.style.fontSize = "12px";

                    // === Flat Mode Button ===
                    const flatBtn = document.createElement("button");
                    flatBtn.textContent = "Flat Region";
                    flatBtn.id = "flatModeBtn";
                    flatBtn.className = "mode-btn active-mode";
                    flatBtn.style.backgroundColor = "#f00";
                    flatBtn.style.padding = "5px 10px";
                    flatBtn.style.fontSize = "12px";

                    // === Append buttons ===
                    container.appendChild(flatBtn);
                    container.appendChild(beatBtn);
                
                    // === Attach to chart container ===
                    chart.container.parentNode.style.position = "relative";
                    chart.container.parentNode.appendChild(container);

                    // === Event Listeners ===
                    let currentMode = "flat"; // default

                    beatBtn.addEventListener("click", () => {
                        currentMode = "beat";
                        beatBtn.classList.add("active-mode");
                        flatBtn.classList.remove("active-mode");
                    });

                    flatBtn.addEventListener("click", () => {
                        currentMode = "flat";
                        flatBtn.classList.add("active-mode");
                        beatBtn.classList.remove("active-mode");
                    });

                    // Make currentMode accessible to your selection logic
                    chart.customSelectionMode = () => currentMode;
                },
                selection: function (event) {
                    if (!event.xAxis) return false;
                
                    let xMin = event.xAxis[0].min;
                    let xMax = event.xAxis[0].max;
                    const mode = chart.customSelectionMode ? chart.customSelectionMode() : "beat";
                    if (mode === "beat") {
                        processECGSelection(data, xMin, xMax);
                    } else {
                        processFlatSelection(data, xMin, xMax);
                    }
                
                    const axis = this.xAxis[0];
                
                    // Remove previous highlights for current mode only
                    if (mode === "beat") {
                        axis.removePlotBand("highlight-beat");
                        axis.removePlotLine("start-beat");
                        axis.removePlotLine("end-beat");
                
                        // Add new highlight for beat
                        axis.addPlotBand({
                            id: "highlight-beat",
                            from: xMin,
                            to: xMax,
                            color: "rgba(6, 168, 0, 0.3)"
                        });
                        axis.addPlotLine({
                            id: "start-beat",
                            value: xMin,
                            color: "white",
                            width: 1
                        });
                        axis.addPlotLine({
                            id: "end-beat",
                            value: xMax,
                            color: "white",
                            width: 1
                        });
                    } else {
                        axis.removePlotBand("highlight-flat");
                        axis.removePlotLine("start-flat");
                        axis.removePlotLine("end-flat");
                
                        // Add new highlight for flat region
                        axis.addPlotBand({
                            id: "highlight-flat",
                            from: xMin,
                            to: xMax,
                            color: "rgba(255, 0, 0, 0.3)"  // Red-ish for flat region
                        });
                        axis.addPlotLine({
                            id: "start-flat",
                            value: xMin,
                            color: "red",
                            width: 1
                        });
                        axis.addPlotLine({
                            id: "end-flat",
                            value: xMax,
                            color: "red",
                            width: 1
                        });
                    }
                
                    // Reset chart back to original zoom
                    let selectedScale = xScaleSelect.value;
                    setTimeout(() => {
                        let newXMax = originalXMin + (originalXMax - originalXMin) / selectedScale;
                        chart.xAxis[0].setExtremes(originalXMin, newXMax);
                    }, 100);
                
                    return false;
                }
                
            }
        },
        title: { 
            text: `Patient ID: ${patientID}`,
            style: { color: "white", fontSize: "18px" }  
        },
        xAxis: { min: originalXMin, max: originalXMax, crosshair: true, gridLineWidth: 0, gridLineWidth: 0.5, gridLineColor: "#444" },
        yAxis: yAxes,
        tooltip: {
            enabled: false,
            shared: false,
            formatter: function () {
                return `<b>Time:</b> ${this.x}s<br><b>Lead ${this.series.name}:</b> ${this.y.toFixed(2)} mV`;
            }
        },
        legend: { enabled: false },
        plotOptions: {
            series: {
                lineWidth: 1.5,
                marker: { enabled: false }
            }
        },
        series: ecgSeries
    });

    chart.renderer.text("Time Scale: ", 220, 20)
        .css({
            color: "white",
            fontSize: "14px"
        })
        .add();

    // Create Reset Button
    const resetButton = document.createElement("button");
    resetButton.id = "resetScaleButton";
    resetButton.textContent = "Reset Scale";
    resetButton.style.position = "absolute";
    resetButton.style.top = "5px";          // Adjust as needed
    resetButton.style.left = "450px";        // Adjust to the right of dropdown
    resetButton.style.zIndex = "10";
    resetButton.style.backgroundColor = "#333";
    resetButton.style.color = "white";
    resetButton.style.border = "1px solid white";
    resetButton.style.padding = "5px 10px";
    resetButton.style.fontSize = "14px";
    resetButton.style.display = "none";      // Hidden by default

    document.getElementById("ecgContainer").appendChild(resetButton);

    let xScaleSelect = document.createElement("select");
    xScaleSelect.id = "xScaleSelect";
    xScaleSelect.style.position = "absolute";
    xScaleSelect.style.top = "5px";  // Adjust as needed
    xScaleSelect.style.left = "330px"; // Adjust as needed
    xScaleSelect.style.zIndex = "0";
    xScaleSelect.style.backgroundColor = "#333";
    xScaleSelect.style.color = "white";
    xScaleSelect.style.border = "1px solid white";
    xScaleSelect.style.padding = "5px";
    xScaleSelect.style.fontSize = "14px";

    // Scale options
    ["1", "2.5", "5", "10", "custom"].forEach(scale => {
        let option = document.createElement("option");
        option.value = scale;
        option.textContent = `${scale}x`;
        xScaleSelect.appendChild(option);
    });

    document.getElementById("ecgContainer").appendChild(xScaleSelect);

    // Scale Selection Event Listener
    xScaleSelect.addEventListener("change", function () {
        let scale = this.value;
        if (scale === "all") {
            chart.xAxis[0].setExtremes(originalXMin, originalXMax);
        } else {
            let newRange = (originalXMax - originalXMin) / scale;
            chart.xAxis[0].setExtremes(originalXMin, originalXMin + newRange);
        }
    });

    chart.renderer.text("Voltage Scale: ", 30, 20)
    .css({
        color: "white",
        fontSize: "14px"
    })
    .add();

    let yScaleSelect = document.createElement("select");
    yScaleSelect.id = "yScaleSelect";
    yScaleSelect.style.position = "absolute";
    yScaleSelect.style.top = "5px";  // Adjust as needed
    yScaleSelect.style.left = "150px"; // Adjust as needed
    yScaleSelect.style.zIndex = "0";
    yScaleSelect.style.backgroundColor = "#333";
    yScaleSelect.style.color = "white";
    yScaleSelect.style.border = "1px solid white";
    yScaleSelect.style.padding = "5px";
    yScaleSelect.style.fontSize = "14px";

    ["1", "0.8", "0.6", "0.4", "0.2"].forEach(scale => {
        let option = document.createElement("option");
        option.value = scale;
        option.textContent = `${scale}x`;
        yScaleSelect.appendChild(option);
    });
    
    document.getElementById("ecgContainer").appendChild(yScaleSelect);
    
    yScaleSelect.addEventListener("change", function () {
        let selectedScale = parseFloat(yScaleSelect.value);
        
        chart.yAxis.forEach(axis => {
            let originalMin = axis.dataMin;
            let originalMax = axis.dataMax;
            let newRange = (originalMax - originalMin) / selectedScale;
    
            axis.setExtremes(originalMin, originalMin + newRange);
        });
    });
}

function processECGSelection(data, xMin, xMax) {
    let standardLeadOrder = ["i", "ii", "iii", "avr", "avl", "avf", "v1", "v2", "v3", "v4", "v5", "v6"];
    let extractedBeats = {};

    standardLeadOrder.forEach(lead => {
        if (data.signals[lead]) {
            let filteredValues = [];
            let filteredTime = [];

            for (let i = 0; i < data.time.length; i++) {
                if (data.time[i] >= xMin && data.time[i] <= xMax) {
                    filteredValues.push(data.signals[lead][i]);
                    filteredTime.push(data.time[i]);
                }
            }

            if (filteredValues.length > 0) {
                extractedBeats[lead] = {
                    time: filteredTime,
                    signal: filteredValues,
                    min: Math.min(...filteredValues),
                    max: Math.max(...filteredValues),
                    startTime: filteredTime[0],
                    endTime: filteredTime[filteredTime.length - 1],
                    avgBaseline: (filteredValues.reduce((a, b) => a + b, 0) / filteredValues.length).toFixed(2)  // Average baseline
                };
            }
        }
    });
    selectedBeatData = extractedBeats;
    checkBothSelectionsReady();
}

function processFlatSelection(data, xMin, xMax) {
    const standardLeadOrder = ["i", "ii", "iii"];  // Process all 3 leads
    const flatSegment = {};

    standardLeadOrder.forEach(lead => {
        if (data.signals[lead]) {
            const flatValues = [];
            const flatTimes = [];

            for (let i = 0; i < data.time.length; i++) {
                if (data.time[i] >= xMin && data.time[i] <= xMax) {
                    flatValues.push(data.signals[lead][i]);
                    flatTimes.push(data.time[i]);
                }
            }

            if (flatValues.length > 0) {
                flatSegment[lead] = {
                    time: flatTimes,
                    signal: flatValues,
                    avg: (
                        flatValues.reduce((a, b) => a + b, 0) / flatValues.length
                    ).toFixed(4),
                    stdDev: Math.sqrt(
                        flatValues.reduce((acc, val) => acc + Math.pow(val - (flatValues.reduce((a, b) => a + b) / flatValues.length), 2), 0) / flatValues.length
                    ).toFixed(4)
                };
            }
        }
    });

    selectedFlatData = flatSegment;
    checkBothSelectionsReady();
}


function checkBothSelectionsReady() {
    if (selectedBeatData && selectedFlatData) {
        // When both selections are ready, proceed to show both single beat charts
        plotSingleBeat(selectedBeatData, "singleBeatContainer1");
        plotSingleBeat2(selectedBeatData, "singleBeatContainer2");
    }
}

function plotSingleBeat(beatsData) {
    let standardLeadOrder = ["i", "ii", "iii", "avr", "avl", "avf", "v1", "v2", "v3", "v4", "v5", "v6"];
    let leadColors = {
        "i": "white", "ii": "white", "iii": "white",
        "avr": "white", "avl": "white", "avf": "white",
        "v1": "white", "v2": "white", "v3": "white",
        "v4": "white", "v5": "white", "v6": "white"
    };

    let yAxes = [];
    let singleBeatSeries = [];
    let numLeads = standardLeadOrder.length;
    let yAxisHeight = 100 / numLeads + 10; // Adjusts spacing between leads
    standardLeadOrder.forEach((lead, index) => {
        if (!beatsData[lead]) return;

        // Assign each lead to its own Y-axis
        yAxes.push({
            id: `singleBeat-y-axis-${index}`,
            title: { text: lead.toUpperCase(), style: { color: leadColors[lead] } },
            top: `${index * (100 / numLeads) - 3}%`, // Position each lead separately
            height: `${yAxisHeight}%`,
            offset: 0,
            lineWidth: 1,
            gridLineWidth: 0,
            gridLineColor: "#444",
            opposite: false, // Aligns Y-axis on the left
            labels: { enabled: false } // Hides numerical Y-axis values
        });

        // Ensure each lead is placed on its own Y-axis
        singleBeatSeries.push({
            name: `Lead ${lead.toUpperCase()}`,
            data: beatsData[lead].time.map((t, i) => [t, beatsData[lead].signal[i]]),
            color: leadColors[lead] || "gray",
            yAxis: index, // Assign to separate Y-axis
            lineWidth: 1.5,
            marker: { 
                enabled: false,
                states: {
                    hover: {
                        enabled: false // 🔹 Prevents dots on hover
                    }
                }
             }
        });
    });
    

    // Plot the Highcharts graph
    let chart = Highcharts.chart("singleBeatContainer", {
        chart: { 
            type: "line",
            backgroundColor: "#1e1e1e",
            zoomType: "x",
            panning: true,
            panKey: "shift",
            events: {
                load: function () {
                    const chart = this;

                    // Create continue button inside chart using renderer
                    chart.customContinueBtn = chart.renderer.button(
                        'Proceed',
                        225, 7, // x, y
                        function () {
                            document.getElementById("screen1").style.display = "none";
                            document.getElementById("screen2").style.display = "flex";
                        },
                        {
                            fill: "#4CAF50",
                            stroke: "#333",
                            r: 5,
                            padding: 5,
                            style: {
                                color: "#fff",
                                fontSize: "13px"
                            }
                        },
                        {
                            fill: "#45a049"
                        }
                    ).attr({
                        zIndex: 10
                    }).add().hide(); // Hide initially

                    // Store original x-axis range when the chart loads
                    originalXMin = this.xAxis[0].min;
                    originalXMax = this.xAxis[0].max;
                },
                selection: function (event) {
                    if (!event.xAxis) return false;  // Prevent errors if no selection
    
                    let xMin = event.xAxis[0].min;
                    let xMax = event.xAxis[0].max;
    
                    processQRSSelection(beatsData, xMin, xMax);

                    // For removing previous plot bands and annotations
                    this.xAxis[0].removePlotBand("highlight-band");
                    this.xAxis[0].removePlotLine("start-time-label");
                    this.xAxis[0].removePlotLine("end-time-label");
                    // Add a new plot band (highlighting the selected range)
                    this.xAxis[0].addPlotBand({
                        id: "highlight-band",
                        from: xMin,
                        to: xMax,
                        color: "rgba(6, 168, 0, 0.32)"
                    });

                    // Add labels for the start and end times
                    this.xAxis[0].addPlotLine({
                        id: "start-time-label",
                        value: xMin,
                        color: "white",
                        width: 1,
                        dashStyle: "solid",
                    });

                    this.xAxis[0].addPlotLine({
                        id: "end-time-label",
                        value: xMax,
                        color: "white",
                        width: 1,
                        dashStyle: "solid",
                        label: {
                            text: `Time diff.: ${(xMax-xMin).toFixed(2)}s`,
                            align: "right",
                            rotation: 0,
                            x: -50,
                            y: -5,
                            style: { color: "white", fontSize: "12px" }
                        }
                    });
    
                    // Reset x-axis after selection to prevent zooming
                    setTimeout(() => {
                        this.xAxis[0].setExtremes(originalXMin, originalXMax);
                    }, 100);

                    this.customContinueBtn?.show();

                    setTimeout(() => {
                        this.xAxis[0].setExtremes(this.xAxis[0].userMin, this.xAxis[0].userMax);
                    }, 100);
    
                    return false;  // Prevent default zooming behavior
                }
            }   
        },
        exporting: {
            enabled: false
        },
        title: { 
            text: "Single Cardiac Beat",
            style: { color: "white", fontSize: "16px" }
        },
        xAxis: { 
            title: { text: "Time (s)", style: { color: "white" } },
            labels: { style: { color: "white" } },
            gridLineWidth: 0.5,
            crosshair: true,
            gridLineColor: "#444"
        },
        yAxis: yAxes, // Assign each lead its own Y-axis without min/max lines
        legend: { enabled: false },
        tooltip: {
            enabled: false,
            shared: false,
            formatter: function () {
                return `<b>Time:</b> ${this.x}s<br><b>${this.series.name}:</b> ${this.y.toFixed(2)} mV`;
            }
        },
        plotOptions: { 
            series: { 
                lineWidth: 1.5, 
                marker: { enabled: false } 
            } 
        },
        series: singleBeatSeries
    });
}
function plotSingleBeat2(beatsData) {
    let standardLeadOrder = ["i", "ii", "iii", "avr", "avl", "avf", "v1", "v2", "v3", "v4", "v5", "v6"];
    let leadColors = {
        "i": "white", "ii": "white", "iii": "white",
        "avr": "white", "avl": "white", "avf": "white",
        "v1": "white", "v2": "white", "v3": "white",
        "v4": "white", "v5": "white", "v6": "white"
    };

    let yAxes = [];
    let singleBeatSeries = [];
    let numLeads = standardLeadOrder.length;
    let yAxisHeight = 100 / numLeads + 10; // Adjusts spacing between leads
    standardLeadOrder.forEach((lead, index) => {
        if (!beatsData[lead]) return;

        // Assign each lead to its own Y-axis
        yAxes.push({
            id: `singleBeat-y-axis-${index}`,
            title: { text: lead.toUpperCase(), style: { color: leadColors[lead] } },
            top: `${index * (100 / numLeads) - 3}%`, // Position each lead separately
            height: `${yAxisHeight}%`,
            offset: 0,
            lineWidth: 1,
            gridLineWidth: 0,
            gridLineColor: "#444",
            opposite: false, // Aligns Y-axis on the left
            labels: { enabled: false } // Hides numerical Y-axis values
        });

        // Ensure each lead is placed on its own Y-axis
        singleBeatSeries.push({
            name: `Lead ${lead.toUpperCase()}`,
            data: beatsData[lead].time.map((t, i) => [t, beatsData[lead].signal[i]]),
            color: leadColors[lead] || "gray",
            yAxis: index, // Assign to separate Y-axis
            lineWidth: 1.5,
            marker: { 
                enabled: false,
                states: {
                    hover: {
                        enabled: false // 🔹 Prevents dots on hover
                    }
                }
             }
        });
    });
    

    // Plot the Highcharts graph
    let chart = Highcharts.chart("singleBeatContainer2", {
        chart: { 
            type: "line",
            backgroundColor: "#1e1e1e",
            zoomType: "x",
            panning: true,
            panKey: "shift",
        },
        title: { 
            text: "Single Cardiac Beat",
            style: { color: "white", fontSize: "16px" }
        },
        exporting: {
            enabled: false
        },
        xAxis: { 
            title: { text: "Time (s)", style: { color: "white" } },
            labels: { style: { color: "white" } },
            gridLineWidth: 0.5,
            crosshair: true,
            gridLineColor: "#444"
        },
        yAxis: yAxes, // Assign each lead its own Y-axis without min/max lines
        legend: { enabled: false },
        tooltip: {
            enabled: false,
            shared: false,
            formatter: function () {
                return `<b>Time:</b> ${this.x}s<br><b>${this.series.name}:</b> ${this.y.toFixed(2)} mV`;
            }
        },
        plotOptions: { 
            series: { 
                lineWidth: 1.5, 
                marker: { enabled: false } 
            } 
        },
        series: singleBeatSeries
    });
}

function processQRSSelection(QRSdata, xMin, xMax) {
    let selectedLeads = ["i", "ii", "iii"];  // ✅ Only process Lead I, II, III
    let extractedBeats = {};
    selectedLeads.forEach(lead => {
        if (QRSdata[lead] && Array.isArray(QRSdata[lead].time) && Array.isArray(QRSdata[lead].signal)) {
            let filteredValues = [];
            let filteredTime = [];
            for (let i = 0; i < QRSdata[lead].time.length; i++) {
                if (QRSdata[lead].time[i] >= xMin && QRSdata[lead].time[i] <= xMax) {
                    filteredValues.push(QRSdata[lead].signal[i]);
                    filteredTime.push(QRSdata[lead].time[i]);
                }
            }
            if (filteredValues.length > 0) {
                extractedBeats[lead] = {
                    time: filteredTime,
                    signal: filteredValues,
                    min: Math.min(...filteredValues),
                    max: Math.max(...filteredValues),
                    startTime: filteredTime[0],
                    endTime: filteredTime[filteredTime.length - 1],
                    avgBaseline: (
                        filteredValues.reduce((a, b) => a + b, 0) / filteredValues.length
                    ).toFixed(2)
                };
            }
        } else {
            console.warn(`Skipping lead ${lead} due to missing or invalid data.`);
        }
    });
    plotQRSComplex(extractedBeats, selectedFlatData);
    updateTable(extractedBeats, selectedFlatData);
    plotVectorGraph(extractedBeats, selectedFlatData);
}

function plotQRSComplex(beatsData, flatSegment = {}) {
    if (!beatsData["i"] || !beatsData["ii"] || !beatsData["iii"]) {
        console.error("Missing Leads for QRS Complex");
        return;
    }

    const leadColors = { i: "white", ii: "white", iii: "white" };
    const qrsSeries = [];
    const yAxes = [];
    const arrows = [];

    const numLeads = 3;
    const yAxisHeight = 100 / numLeads;

    ["i", "ii", "iii"].forEach((lead, index) => {
        const qrs = beatsData[lead];
        if (!qrs) return;

        const time = qrs.time;
        const signal = qrs.signal;

        const minVal = Math.min(...signal);
        const maxVal = Math.max(...signal);
        const minTime = time[signal.indexOf(minVal)];
        const maxTime = time[signal.indexOf(maxVal)];

        yAxes.push({
            id: `qrs-y-axis-${index}`,
            title: { text: lead.toUpperCase(), style: { color: leadColors[lead] } },
            top: `${index * yAxisHeight}%`,
            height: `${yAxisHeight}%`,
            offset: 0,
            gridLineWidth: 0.5,
            gridLineColor: "#444",
            labels: { enabled: false }
        });

        qrsSeries.push({
            name: `Lead ${lead.toUpperCase()}`,
            data: time.map((t, i) => [t, signal[i]]),
            color: leadColors[lead],
            yAxis: index,
            lineWidth: 1.5,
            marker: { 
                enabled: false,
                states: {
                    hover: {
                        enabled: false // Prevents dots on hover
                    }
                }
             }
        });

        // Hidden markers for reference positions
        qrsSeries.push({
            name: `Hidden Max (${lead})`,
            type: "scatter",
            data: [[maxTime, maxVal]],
            yAxis: index,
            marker: {
                radius: 0,
                enabled: true,
                states: { hover: { enabled: false } }
            },
            enableMouseTracking: false
        });

        qrsSeries.push({
            name: `Hidden Min (${lead})`,
            type: "scatter",
            data: [[minTime, minVal]],
            yAxis: index,
            marker: {
                radius: 0,
                enabled: true,
                states: { hover: { enabled: false } }
            },
            enableMouseTracking: false
        });

        // Save arrow data for later
        arrows.push({ time: maxTime, value: maxVal, text: "Max", color: "red", index });
        arrows.push({ time: minTime, value: minVal, text: "Min", color: "red", index });
    });

    Highcharts.chart("qrsContainer", {
        chart: {
            type: "line",
            backgroundColor: "#1e1e1e",
            height: "230%",
            events: {
                load: function () {
                    const chart = this;
                    arrows.forEach(a => {
                        const x = chart.xAxis[0].toPixels(a.time);
                        const y = chart.yAxis[a.index].toPixels(a.value);
                        const yMax = y - 6;
                        const yMin = y + 6;
                
                        const size = 4; // smaller arrow size
                
                        const arrowPath = a.text === "Max"
                            // Arrow pointing up
                            ? [
                                'M', x, yMax + size,
                                'L', x - size / 2, yMax - size / 2,
                                'L', x + size / 2, yMax - size / 2,
                                'Z'
                            ]
                            // Arrow pointing down
                            : [
                                'M', x, yMin - size,
                                'L', x - size / 2, yMin + size / 2,
                                'L', x + size / 2, yMin + size / 2,
                                'Z'
                            ];
                
                        chart.renderer.path(arrowPath)
                            .attr({ fill: a.color, zIndex: 10 })
                            .add();
                
                        // Text label above or below the arrow
                        chart.renderer.text(`${a.text}: ${a.value.toFixed(2)} mV`,
                                x + 5,
                                a.text === "Max" ? y - size - 5 : y + size + 15
                            )
                            .css({ color: a.color, fontSize: '11px' })
                            .add();
                    });
                }                
            }
        },
        exporting: {
            enabled: false
        },
        title: {
            text: "QRS Complex (Lead I, II, III)",
            style: { color: "white", fontSize: "16px" }
        },
        xAxis: {
            title: { text: "Time (s)", style: { color: "white" } },
            labels: { style: { color: "white" } },
            crosshair: true,
            gridLineWidth: 0.5,
            gridLineColor: "#444"
        },
        yAxis: yAxes,
        legend: { enabled: false },
        tooltip: {
            enabled: false,
            formatter: function () {
                return `<b>Time:</b> ${this.x}s<br><b>${this.series.name}:</b> ${this.y.toFixed(2)} mV`;
            }
        },
        plotOptions: {
            series: {
                marker: { enabled: false },
                lineWidth: 1.5
            }
        },
        series: qrsSeries
    });
}

function updateTable(selectedData, flatSegment) {
    let tableBody = document.querySelector("#leads-table tbody");
    let leadDataArray = [];
    const patientId = ecgData?.patient_info?.anonymous_id || "Unknown";
    tableBody.innerHTML = "";

    Object.keys(selectedData).forEach(lead => {
        const qrs = selectedData[lead];
        const flat = flatSegment[lead] || flatSegment["i"];
        const flatAvg = flat && flat.avg ? parseFloat(flat.avg) : 0;
        const signal = qrs.signal;
        const minVal = Math.min(...signal);
        const maxVal = Math.max(...signal);
        let correctedMax = 0;
        let correctedMin = 0;

        // Corrected peak calculations using flat region average
        if (flatAvg <= 0) {
            correctedMax = maxVal + Math.abs(flatAvg);
            correctedMin = -(Math.abs(minVal) - Math.abs(flatAvg));
        } else {
            correctedMax = maxVal - Math.abs(flatAvg);
            correctedMin = -(Math.abs(minVal) + Math.abs(flatAvg));
        }

        const resultantVector = correctedMax - Math.abs(correctedMin);

        // === TABLE ROW ===
        const row = `
            <tr>
                <td>${lead.toUpperCase()}</td>
                <td>${qrs.startTime.toFixed(2)}</td>
                <td>${qrs.endTime.toFixed(2)}</td>
                <td>${flatAvg.toFixed(2)}</td> <!-- Now using flat region average -->
                <td>${qrs.max.toFixed(2)}</td>
                <td>${qrs.min.toFixed(2)}</td>
                <td>${correctedMax.toFixed(2)}</td>
                <td>${correctedMin.toFixed(2)}</td>
                <td>${resultantVector.toFixed(2)}</td>
            </tr>
        `;
        tableBody.innerHTML += row;

        // === DATA FOR BACKEND ===
        leadDataArray.push({
            lead: lead.toUpperCase(),
            startTime: qrs.startTime,
            endTime: qrs.endTime,
            avgBaseline: flatAvg, // Now using flatAvg
            maxBeat: qrs.max,
            minBeat: qrs.min,
            correctedMaxPeak: correctedMax,
            correctedMinPeak: correctedMin,
            leadVector: resultantVector
        });
    });

    // === SEND TO BACKEND ===
    const dataToSend = {
        anonymous_id: patientId,
        leadDataArray: leadDataArray,
    };

    fetch("/api/post_result_vector", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(dataToSend),
    })
    .then((response) => response.json())
    .then((data) => {
        console.log("Success:", data);
    })
    .catch((error) => {
        console.error("Error:", error);
    });

    document.getElementById("table-container").style.display = "block";
    console.log("Lead Data Array:", leadDataArray);
}

function updatePatientInfo(patientData) {
    let patientContainer = document.getElementById("patientInfo");
    if (!patientContainer) return;

    // Fix gender → use gender instead of sex
    const age = patientData.age || "N/A";
    const gender = patientData.gender || "N/A";
    const rhythm = patientData.heart_rhythm || "Unknown";
    const repolarization = patientData.repolarization_abnormalities || "None";

    // Parse JSON strings safely
    const parseList = (field) => {
        try {
            const parsed = JSON.parse(field);
            return Array.isArray(parsed) && parsed.length > 0 ? parsed.join(", ") : "None";
        } catch {
            return "None";
        }
    };

    const hypertrophies = parseList(patientData.hypertrophies);
    const ischemia = parseList(patientData.ischemia);
    const conduction = parseList(patientData.conduction_system_disease);
    const pacing = parseList(patientData.cardiac_pacing);

    // Update DOM
    patientContainer.innerHTML = `
        <h2>Patient Information</h2>
        <p><strong>Age:</strong> ${age}</p>
        <p><strong>Gender:</strong> ${gender}</p>
        <p><strong>Rhythm:</strong> ${rhythm}</p>
        <p><strong>Repolarization Abnormalities:</strong> ${repolarization}</p>
        <p><strong>Hypertrophies:</strong> ${hypertrophies}</p>
        <p><strong>Ischemia:</strong> ${ischemia}</p>
        <p><strong>Conduction Issues:</strong> ${conduction}</p>
        <p><strong>Cardiac Pacing:</strong> ${pacing}</p>
    `;
}

function findClosestTimeIndex(timeArray, clickedX) {
    return timeArray.reduce((closestIdx, time, idx) =>
        Math.abs(time - clickedX) < Math.abs(timeArray[closestIdx] - clickedX) ? idx : closestIdx, 0);
}

function plotVectorGraph(data, flatSegment = {}) {
    if (!data || !data["i"] || !data["iii"]) {
        console.error("Missing data for Lead I or Lead III.");
        return;
    }

    let leadI = data["i"];
    let leadIII = data["iii"];

    let baselineI = flatSegment["i"] ? parseFloat(flatSegment["i"].avg) : 0;
    let baselineIII = flatSegment["iii"] ? parseFloat(flatSegment["iii"].avg) : 0;

    // Corrected max/min values using flat region
    let correctedMaxI = leadI.max - baselineI;
    let correctedMinI = leadI.min - baselineI;
    let correctedMaxIII = leadIII.max - baselineIII;
    let correctedMinIII = leadIII.min - baselineIII;

    // Compute resultant vector
    let dx = correctedMaxI - Math.abs(correctedMinI);
    let dy = correctedMaxIII - Math.abs(correctedMinIII);

    let magnitude = Math.sqrt(Math.pow(dx, 2) + Math.pow(dy, 2));
    let angle = Math.atan2(dy, dx) * (180 / Math.PI); // in degrees

    // Display magnitude and angle
    document.getElementById("magnitude").innerText = magnitude.toFixed(2);
    document.getElementById("angle").innerText = angle.toFixed(2);

    // Send corrected values to backend to generate vector image
    fetch("/api/vector-graph", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
            lead1: correctedMaxI - Math.abs(correctedMinI), 
            lead3: correctedMaxIII - Math.abs(correctedMinIII)
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.image) {
            let vectorImage = document.getElementById("vector-image");
            vectorImage.src = "data:image/png;base64," + data.image;
            vectorImage.style.display = "block";
            // Save this globally for AI use
            window.vectorData = {
                magnitude: data.magnitude,
                angle: data.angle,
                diagnose: data.diagnose || "No Axis Deviation"
            };
        } else {
            console.error("Error generating vector graph.");
        }
    })
    .catch(error => console.error("Error:", error));
}

// Function to call huggingface ai
async function getAIInterpretation(summaryText) {
    try {
        const response = await fetch("https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer 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"
            },
            body: JSON.stringify({ inputs: summaryText })
        });

        const data = await response.json();
        console.log("AI Response:", data);

        if (data && Array.isArray(data) && data[0]?.generated_text) {
            return data[0].generated_text; // Return the real text
        } else {
            return "AI response was invalid or empty.";
        }
    } catch (err) {
        console.error("AI interpretation failed:", err);
        return "AI interpretation could not be retrieved.";
    }
}



// show/hide ai pop up window
function showInterpretationModal(text) {
    const modal = document.getElementById("ai-interpretation");
    const aiText = document.getElementById("ai-text");
    const closeBtn = modal.querySelector(".close-btn");

    aiText.textContent = text;
    modal.style.display = "block";

    closeBtn.onclick = () => {
        modal.style.display = "none";
    };
}

  
  

// Hook into the final processing logic (after ECG + flat + vector complete)
async function runFinalAnalysis(patientData, vectorData) {
    let summary = `Interpreting this ECG data and explaining it in easy-to-understand terms. Include a summary at the end.

Patient Information:
- Age: ${patientData.age}
- Gender: ${patientData.gender || patientData.sex || "N/A"}
- Heart Rhythm: ${patientData.heart_rhythm || patientData.rhythm || "N/A"}
- Repolarization Abnormalities: ${patientData.repolarization_abnormalities || "None"}
- Hypertrophies: ${Array.isArray(patientData.hypertrophies) ? patientData.hypertrophies.join(", ") : patientData.hypertrophies || "None"}
- Ischemia: ${Array.isArray(patientData.ischemia) ? patientData.ischemia.join(", ") : patientData.ischemia || "None"}
- Conduction System Disease: ${Array.isArray(patientData.conduction_system_disease) ? patientData.conduction_system_disease.join(", ") : patientData.conduction_system_disease || "None"}
- Cardiac Pacing: ${Array.isArray(patientData.cardiac_pacing) ? patientData.cardiac_pacing.join(", ") : patientData.cardiac_pacing || "None"}

Electrical Axis Analysis:
- Resultant Vector Magnitude: ${vectorData.magnitude} mV
- Electrical Axis Angle: ${vectorData.angle} degrees
- Axis Deviation: ${vectorData.diagnose || "None"}

`;

    const aiResult = await getAIInterpretation(summary);
    showInterpretationModal(aiResult);  // Show it here
}




document.addEventListener("DOMContentLoaded", function () {
    console.log("Website Loaded Successfully!");

    // Ensure the ECG graph and patient info are visible after loading
    let graphSection = document.getElementById("screen1");
    let patientInfo = document.getElementById("patientInfo");

    if (graphSection) {
        graphSection.style.display = "block"; // Show ECG graph
    }

    if (patientInfo) {
        patientInfo.style.display = "block"; // Show patient info
    }
});

const selectAgainBtn = document.getElementById("selectAgain");
if (selectAgainBtn) {
    selectAgainBtn.addEventListener("click", () => {
        const screen2 = document.getElementById("screen2");
        const screen1 = document.getElementById("screen1");
        if (screen2) screen2.style.display = "none";
        if (screen1) screen1.style.display = "flex";
    });
}

const exitToUploadBtn = document.getElementById("exitToUpload");
if (exitToUploadBtn) {
    exitToUploadBtn.addEventListener("click", () => {
        window.location.href = "/";
    });
}

const chooseAnotherBtn = document.getElementById("chooseAnother");
if (chooseAnotherBtn) {
    chooseAnotherBtn.addEventListener("click", () => {
        window.location.href = "/allPatients";
    });
}

// Export functions for testing
if (typeof module !== 'undefined') {
    module.exports = {
        updatePatientInfo,
        findClosestTimeIndex,
        showInterpretationModal,
        processECGSelection,
        processFlatSelection,
        checkBothSelectionsReady,
        plotECGHighcharts,
        plotSingleBeat,
        plotSingleBeat2,
        processQRSSelection,
        plotQRSComplex,
        updateTable,
        plotVectorGraph,
        getAIInterpretation,
        runFinalAnalysis
    };
}


