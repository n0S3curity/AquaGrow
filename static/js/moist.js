// moist.js content (updated to use inline SVGs instead of Lucide)
const sensorCardsContainer = document.getElementById('sensorCardsContainer');
const graphSensorSelect = document.getElementById('graphSensorSelect');
const selectedSensorForGraphEl = document.getElementById('selectedSensorForGraph');
const moistureChartCanvas = document.getElementById('moistureChart').getContext('2d');
const logContainerEl = document.getElementById('logContainer');

let moistureChart; // Variable to hold the Chart.js instance
let allSensorData = []; // To store data for all sensors

// Helper function to get an inline SVG for a given icon type and color
function getIconSVG(iconType, className = '') {
    const defaultClasses = 'w-4 h-4 mr-1'; // Default size and margin
    let svgPath = '';
    switch (iconType) {
        case 'water':
            // Lucide 'water' or 'droplet' equivalent
            svgPath = '<path d="M12 2.69L12 18.29C12 19.86 10.86 21 9.29 21H6.71C5.14 21 4 19.86 4 18.29V2.69C4 1.12 5.14 0 6.71 0H9.29C10.86 0 12 1.12 12 2.69Z M12 2.69L12 18.29C12 19.86 13.14 21 14.71 21H17.29C18.86 21 20 19.86 20 18.29V2.69C20 1.12 18.86 0 17.29 0H14.71C13.14 0 12 1.12 12 2.69Z"/>';
            break;
        case 'check-circle':
            // Lucide 'check-circle' equivalent
            svgPath = '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline>';
            break;
        case 'circle-x':
            // Lucide 'circle-x' equivalent
            svgPath = '<circle cx="12" cy="12" r="10"></circle><path d="m15 9-6 6"></path><path d="m9 9 6 6"></path>';
            break;
        // Removed 'alert-triangle' and 'lightbulb' cases as requested for simplification
        default:
            return ''; // No SVG for unknown types
    }
    return `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="${defaultClasses} ${className}">${svgPath}</svg>`;
}

// Function to create a sensor card HTML
function createSensorCard(sensor) {
    // Determine status based on moisture value relative to a threshold (e.g., 500 for DRY)
    // Assuming a threshold is available, or setting a default.
    // For this example, let's assume 'DRY' if moisture is below 300, 'Optimal' above 700, otherwise 'Moderate'.
    // Use sensor.moisture_threshold if available, otherwise default to 500
    const effectiveThreshold = sensor.moisture_threshold !== undefined && sensor.moisture_threshold !== null ? sensor.moisture_threshold : 500;

    const status = sensor.current_moisture < effectiveThreshold ? "DRY" :
                   sensor.current_moisture >= 700 ? "Optimal" : "Moderate";

    const statusColor = status.includes("DRY") ? 'bg-red-100 border-red-400 text-red-700' :
                        status.includes("Optimal") ? 'bg-green-100 border-green-400 text-green-700' :
                        'bg-blue-100 border-blue-400 text-blue-700';

    const buttonColor = status.includes("DRY") ? 'bg-red-500 hover:bg-red-600' : 'bg-blue-500 hover:bg-blue-600';

    return `
        <div class="bg-white p-6 rounded-xl shadow-lg border ${statusColor} flex flex-col space-y-3">
            <h3 class="text-2xl font-bold text-gray-800 mb-2">${sensor.name}</h3>
            <div class="flex justify-between items-center text-lg">
                <span class="font-medium">Moisture:</span>
                <span class="text-3xl font-extrabold ${status.includes("DRY") ? 'text-red-600' : 'text-green-600'}">
                    ${sensor.current_moisture}
                </span>
            </div>
            <div class="flex justify-between items-center text-lg">
                <span class="font-medium">Status:</span>
                <span class="text-xl font-semibold ${status.includes("DRY") ? 'text-red-500 font-bold' : 'text-green-500'}">
                    ${status}
                </span>
            </div>



              <div class="flex justify-between items-center text-lg">
                <span class="font-medium">IP:</span>
                <span class="text-xl font-semibold ${sensor.ip_address ? 'text-gray-800' : 'text-red-600'}">
                    ${sensor.ip_address ? sensor.ip_address : 'N/A'}
                </span>
            </div>


            <p class="text-xs text-gray-500">Last updated: ${sensor.last_updated ? new Date(sensor.last_updated).toLocaleTimeString() : '--'}</p>
            <button data-sensor-name="${sensor.name}" class="water-single-btn ${buttonColor} text-white font-bold py-2 px-4 rounded-lg shadow transform transition duration-200 hover:scale-105 active:scale-95 flex items-center justify-center space-x-2">
                ${getIconSVG('water', 'w-4 h-4 mr-2')} <span>Water ${sensor.name}</span>
            </button>
            <div id="wateringMessage-${sensor.name}" class="text-center mt-1 text-sm font-medium text-gray-600 hidden flex items-center justify-center"></div>
        </div>
    `;
}

// Function to populate the graph select dropdown
function populateSensorSelectors(sensors) {
    graphSensorSelect.innerHTML = '<option value="all">All Plants (Combined)</option>'; // Option for combined graph
    sensors.forEach(sensor => {
        const optionGraph = document.createElement('option');
        optionGraph.value = sensor.name;
        optionGraph.textContent = sensor.name;
        graphSensorSelect.appendChild(optionGraph);
    });
    // Restore selection if possible, or set default
    if (graphSensorSelect.dataset.selected) {
         graphSensorSelect.value = graphSensorSelect.dataset.selected;
    } else {
         graphSensorSelect.value = 'all'; // Default to "all"
         selectedSensorForGraphEl.textContent = "All Plants";
    }
}


// Function to initialize or update the Chart.js graph for a selected sensor
function updateMoistureChart(selectedSensorName) {
    let dataToShow = [];
    let threshold = null;

    if (selectedSensorName === 'all') {
        selectedSensorForGraphEl.textContent = "All Plants (Combined)";
        let datasets = [];
        const colors = [
            'rgb(75, 192, 192)', 'rgb(255, 159, 64)', 'rgb(255, 99, 132)',
            'rgb(54, 162, 235)', 'rgb(153, 102, 255)', 'rgb(201, 203, 207)',
            'rgb(255, 205, 86)', 'rgb(75, 192, 1)', 'rgb(192, 75, 75)',
            'rgb(86, 205, 255)'
        ];
        let allLabels = new Set();

        allSensorData.forEach((sensor, index) => {
            // Use sensor.moisture_history, if not available, default to an empty array
            const history = sensor.moisture_history || [];
            history.forEach(entry => allLabels.add(entry.timestamp));
            datasets.push({
                label: sensor.name,
                data: history.map(entry => entry.moisture), // Use 'moisture' from history
                borderColor: colors[index % colors.length],
                tension: 0.1,
                fill: false,
                pointRadius: 3,
                pointBackgroundColor: colors[index % colors.length],
                originalTimestamps: history.map(entry => entry.timestamp)
            });
            // Only add threshold if it exists for the sensor
            if (sensor.moisture_threshold !== undefined && sensor.moisture_threshold !== null) {
                datasets.push({
                    label: `${sensor.name} Threshold`,
                    data: new Array(history.length).fill(sensor.moisture_threshold),
                    borderColor: colors[index % colors.length].replace('rgb', 'rgba').replace(')', ', 0.5)'),
                    borderWidth: 1,
                    borderDash: [2, 2],
                    fill: false,
                    pointRadius: 0,
                    originalTimestamps: history.map(entry => entry.timestamp)
                });
            }
        });

        const sortedLabels = Array.from(allLabels).sort();
        const formattedLabels = sortedLabels.map(ts => {
            const date = new Date(ts);
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        });

        datasets = datasets.map(dataset => {
            const newData = sortedLabels.map(labelTs => {
                const originalIndex = dataset.originalTimestamps.indexOf(labelTs);
                return originalIndex !== -1 ? dataset.data[originalIndex] : null;
            });
            return { ...dataset, data: newData };
        });


        if (moistureChart) {
            moistureChart.data.labels = formattedLabels;
            moistureChart.data.datasets = datasets;
            moistureChart.update();
        } else {
            moistureChart = new Chart(moistureChartCanvas, {
                type: 'line',
                data: {
                    labels: formattedLabels,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: false,
                            title: {
                                display: true,
                                text: 'Moisture Value'
                            },
                            min: 0,
                            max: 1023
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Time'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    }
                }
            });
        }


    } else {
        const sensor = allSensorData.find(s => s.name === selectedSensorName);
        if (sensor) {
            dataToShow = sensor.moisture_history || []; // Use history or empty array
            threshold = sensor.moisture_threshold;
            selectedSensorForGraphEl.textContent = sensor.name;
        } else {
            dataToShow = [];
            threshold = null;
            selectedSensorForGraphEl.textContent = "N/A";
        }

        const labels = dataToShow.map(entry => {
            const date = new Date(entry.timestamp);
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        });
        const data = dataToShow.map(entry => entry.moisture); // Use 'moisture' from history

        if (moistureChart) {
            moistureChart.data.labels = labels;
            moistureChart.data.datasets = [
                {
                    label: 'Moisture Level',
                    data: data,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1,
                    fill: false,
                    pointRadius: 4,
                    pointBackgroundColor: 'rgb(75, 192, 192)'
                },
                {
                    label: 'Dry Threshold',
                    data: threshold !== null ? new Array(data.length).fill(threshold) : [],
                    borderColor: threshold !== null ? 'rgb(255, 99, 132)' : 'rgba(0,0,0,0)',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0
                }
            ];
            moistureChart.update();
        } else {
            moistureChart = new Chart(moistureChartCanvas, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Moisture Level',
                            data: data,
                            borderColor: 'rgb(75, 192, 192)',
                            tension: 0.1,
                            fill: false,
                            pointRadius: 4,
                            pointBackgroundColor: 'rgb(75, 192, 192)'
                        },
                        {
                            label: 'Dry Threshold',
                            data: threshold !== null ? new Array(data.length).fill(threshold) : [],
                            borderColor: threshold !== null ? 'rgb(255, 99, 132)' : 'rgba(0,0,0,0)',
                            borderWidth: 2,
                            borderDash: [5, 5],
                            fill: false,
                            pointRadius: 0
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: false,
                            title: {
                                display: true,
                                text: 'Moisture Value'
                            },
                            min: 0,
                            max: 1023
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Time'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    }
                }
            });
        }
    }
}


// Function to fetch and update sensor status for all sensors
async function fetchSensorStatus() {
    try {
        const response = await fetch('/api/status');
        const sensorsDataObject = await response.json(); // Data is an object

        // Transform the object into an array of sensor objects
        const sensorsData = Object.keys(sensorsDataObject).map(key => {
            const sensor = sensorsDataObject[key];
            return {
                name: key,
                ip_address: sensor.ip,
                current_moisture: sensor.moisture,
                moisture_threshold: sensor.moisture_threshold || 500, // Default if not provided
                last_updated: sensor.last_updated || new Date().toISOString(), // Default if not provided
                moisture_history: sensor.history || [] // Use 'history' from the new JSON structure
            };
        });

        allSensorData = sensorsData; // Store globally

        // Store current selection for graph to preserve it across updates
        const currentGraphSelection = graphSensorSelect.value;
        graphSensorSelect.dataset.selected = currentGraphSelection;

        sensorCardsContainer.innerHTML = ''; // Clear previous cards
        if (sensorsData.length === 0) {
            sensorCardsContainer.innerHTML = '<p class="col-span-full text-center text-gray-500">No sensor data available. Please check backend configuration.</p>';
        } else {
            sensorsData.forEach(sensor => {
                sensorCardsContainer.innerHTML += createSensorCard(sensor);
            });
        }

        // After updating cards, re-attach event listeners for dynamic buttons
        document.querySelectorAll('.water-single-btn').forEach(button => {
            button.onclick = handleSingleWater;
        });

        // Populate and update graph
        populateSensorSelectors(sensorsData);
        // Now retrieve the stored selection
        updateMoistureChart(graphSensorSelect.dataset.selected || 'all'); // Default to 'all' if no selection

    } catch (error) {
        console.error("Error fetching sensor status:", error);
        sensorCardsContainer.innerHTML = '<p class="col-span-full text-center text-red-500">Error loading sensor data. Check server connection.</p>';
    }
}

// Function to handle single water button click
async function handleSingleWater(event) {
    const button = event.currentTarget;
    const sensorName = button.dataset.sensorName;
    const messageEl = document.getElementById(`wateringMessage-${sensorName}`);

    button.disabled = true;
    // Add a spinner icon to show watering is in progress
    messageEl.innerHTML = `<svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>Watering ${sensorName}...`;
    messageEl.classList.remove('hidden');
    messageEl.classList.add('text-blue-600');

    try {
        const response = await fetch('/api/water', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sensor_names: [sensorName] })
        });
        const result = await response.json();

        const sensorResult = result.results[sensorName];
        if (sensorResult && sensorResult.status === 'success') {
            messageEl.innerHTML = `${getIconSVG('check-circle', 'text-green-600')}Watering ${sensorName} successful!`;
            messageEl.classList.remove('text-blue-600', 'text-red-600');
            messageEl.classList.add('text-green-600');
        } else {
            messageEl.innerHTML = `${getIconSVG('circle-x', 'text-red-600')}Watering ${sensorName} failed: ${sensorResult ? sensorResult.message : 'Unknown error'}`;
            messageEl.classList.remove('text-blue-600', 'text-green-600');
            messageEl.classList.add('text-red-600');
        }
    } catch (error) {
        console.error(`Error watering ${sensorName}:`, error);
        messageEl.innerHTML = `${getIconSVG('circle-x', 'text-red-600')}Network error watering ${sensorName}.`;
        messageEl.classList.remove('text-blue-600', 'text-green-600');
        messageEl.classList.add('text-red-600');
    } finally {
        button.disabled = false;
        setTimeout(() => {
            messageEl.classList.add('hidden');
        }, 3000);
    }
}

// Event listener for graph sensor selection
graphSensorSelect.addEventListener('change', (event) => {
    const selectedSensor = event.target.value;
    graphSensorSelect.dataset.selected = selectedSensor;
    updateMoistureChart(selectedSensor);
});

// Function to fetch and update logs
async function fetchLogs() {
    try {
        const response = await fetch('/api/logs');

        // Correct way for JSON: Directly parse as JSON
        const logs = await response.json();
        console.log("Fetched logs (parsed as JSON):", logs); // This will show the parsed array/object

        logContainerEl.innerHTML = ''; // Clear previous logs
        if (logs.length === 0) {
            logContainerEl.innerHTML = '<p class="text-gray-500 text-sm">No log entries yet.</p>';
        } else {
            logs.forEach(log => {
                const p = document.createElement('p');
                p.className = `text-sm font-mono flex items-center`;
                let iconHtml = '';
                let textColor = 'text-gray-800';

                switch(log.level) {
                    case 'ERROR':
                        iconHtml = getIconSVG('circle-x', 'text-red-600');
                        textColor = 'text-red-700';
                        break;
                    case 'WARNING':
                        // Removed icon for WARNING logs
                        textColor = 'text-yellow-700';
                        break;
                    case 'INFO':
                        // Removed icon for INFO logs
                        textColor = 'text-gray-800';
                        break;
                    default:
                        iconHtml = ''; // No icon for DEBUG, etc.
                        textColor = 'text-gray-800';
                }
                p.classList.add(textColor);
                p.innerHTML = `${iconHtml}<span>${log.timestamp} - ${log.level} - ${log.message}</span>`;
                logContainerEl.appendChild(p);
            });
            // Removed lucide.createIcons as we are now using inline SVGs
            logContainerEl.scrollTop = logContainerEl.scrollHeight;
        }
    } catch (error) {
        console.error("Error fetching logs:", error);
        logContainerEl.innerHTML = '<p class="text-red-500 text-sm">Failed to load logs.</p>';
    }
}

// Initial fetch and set up polling
document.addEventListener('DOMContentLoaded', () => {
    fetchSensorStatus();
    fetchLogs();

    const refreshIntervalMs = 5000;

    setInterval(fetchSensorStatus, refreshIntervalMs);
    setInterval(fetchLogs, refreshIntervalMs * 2);
});