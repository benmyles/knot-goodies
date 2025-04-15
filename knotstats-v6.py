# /// script
# dependencies = [
#     "flask>=2.0",
#     "requests>=2.20",
# ]
# ///
#
# ################################################################################
# # Knot Resolver Stats Dashboard
# ################################################################################
#
# A simple web-based dashboard for monitoring Knot Resolver statistics in real-time.
#
# ## Requirements
#
# This script requires the Knot Resolver webmgmt feature to be enabled:
#
# ```kresd.conf
# net.listen('127.0.0.1', 8453, { kind = 'webmgmt' })
# modules = {
#    'http',
# }
# http.config({})
# ```
#
# ## Usage
#
# 1. Install uv: https://docs.astral.sh/uv/guides/scripts/
# 2. Run the dashboard: `uv run knotstats.py`
# 3. Open http://127.0.0.1:5001 in your browser
#

import requests
import json
from flask import Flask, render_template_string, jsonify

# --- Configuration ---
KNOT_RESOLVER_STATS_URL = "http://192.168.1.22:8888/metrics/json"
# --- Flask App ---
app = Flask(__name__)

# --- HTML Template with Tailwind CSS, Chart.js, and JavaScript ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Knot Resolver Stats Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background-color: #f7fafc; /* gray-100 */
        }
        /* Custom card styling */
        .chart-card, .stat-card {
            background-color: white;
            border-radius: 0.75rem; /* rounded-xl */
            padding: 1.5rem; /* p-6 */
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); /* shadow-lg */
            margin-bottom: 1.5rem; /* mb-6 */
        }
        .chart-title {
            font-size: 1.125rem; /* text-lg */
            font-weight: 600; /* font-semibold */
            color: #4a5568; /* text-gray-700 */
            margin-bottom: 1rem; /* mb-4 */
            text-align: center;
        }
        /* Grid for charts */
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem; /* gap-6 */
            margin-bottom: 1.5rem; /* mb-6 */
        }
        /* Grid for raw stats */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem; /* gap-4 */
        }
        .stat-card {
             padding: 1rem; /* p-4 */
             min-height: 70px;
             display: flex;
             flex-direction: column;
             justify-content: space-between;
             box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06); /* shadow-md */
        }
        .stat-key {
            font-weight: 600; /* font-semibold */
            color: #718096; /* text-gray-500 */
            font-size: 0.75rem; /* text-xs */
            margin-bottom: 0.25rem; /* mb-1 */
            word-break: break-all;
        }
        .stat-value {
            font-size: 1.125rem; /* text-lg */
            font-weight: 700; /* font-bold */
            color: #2d3748; /* text-gray-800 */
        }
        /* Loading and Error states */
        #loading-state, #error-state {
            text-align: center;
            padding: 3rem;
            font-size: 1.25rem; /* text-xl */
            color: #718096; /* text-gray-500 */
        }
        #error-message {
            color: #e53e3e; /* text-red-600 */
            font-weight: 600; /* font-semibold */
            margin-top: 0.5rem; /* mt-2 */
            font-size: 1rem; /* text-base */
        }
        /* Header style */
        header {
            background: linear-gradient(to right, #4a5568, #2d3748); /* gray-700 to gray-800 */
            color: white;
            padding: 1.5rem 2rem; /* p-6 sm:px-8 */
            margin-bottom: 2rem; /* mb-8 */
            border-radius: 0.75rem; /* rounded-xl */
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05); /* shadow-xl */
        }
        header h1 {
            font-size: 2.25rem; /* text-4xl */
            font-weight: 700; /* font-bold */
            text-align: center;
        }
        /* Footer style */
        footer {
            text-align: center;
            margin-top: 3rem; /* mt-12 */
            padding: 1.5rem; /* p-6 */
            font-size: 0.875rem; /* text-sm */
            color: #a0aec0; /* text-gray-400 */
        }
        /* Ensure canvas is responsive */
        canvas {
            max-width: 100%;
            height: auto !important; /* Override potential fixed height */
        }
        /* Section title for raw stats */
        .section-title {
             font-size: 1.5rem; /* text-2xl */
             font-weight: 600; /* font-semibold */
             color: #4a5568; /* text-gray-700 */
             margin-bottom: 1rem; /* mb-4 */
             padding-bottom: 0.5rem; /* pb-2 */
             border-bottom: 2px solid #e2e8f0; /* border-gray-300 */
        }
        /* Instance selector style */
        .instance-selector {
            margin-bottom: 1.5rem;
            text-align: center;
        }
        .instance-selector select {
            padding: 0.5rem 1rem;
            border-radius: 0.375rem;
            border: 1px solid #e2e8f0;
            background-color: white;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            font-size: 1rem;
            width: 100%;
            max-width: 400px;
        }
    </style>
</head>
<body class="p-4 md:p-8">

    <header>
        <h1>Knot Resolver Stats Dashboard</h1>
    </header>

    <main>
        <div id="loading-state">Loading stats...</div>

        <div id="error-state" style="display: none;">
            Could not fetch stats. Is Knot Resolver running at {{ knot_resolver_url }}?
            <div id="error-message"></div>
        </div>

        <div id="dashboard-content" style="display: none;">
            <div class="instance-selector">
                <label for="instance-select" class="sr-only">Select Instance:</label>
                <select id="instance-select" class="instance-select">
                    </select>
            </div>

            <div class="charts-grid">
                <div class="chart-card">
                    <div class="chart-title">Answer Status Distribution</div>
                    <canvas id="answerStatusChart"></canvas>
                </div>
                <div class="chart-card">
                    <div class="chart-title">Request Type Distribution</div>
                    <canvas id="requestTypeChart"></canvas>
                </div>
                <div class="chart-card">
                    <div class="chart-title">Answer Source</div>
                    <canvas id="answerSourceChart"></canvas>
                </div>
                <div class="chart-card">
                    <div class="chart-title">Answer Latency (ms)</div>
                    <canvas id="answerLatencyChart"></canvas>
                </div>
            </div>

            <h2 class="section-title" id="stats-title">All Statistics</h2>
            <div id="stats-container" class="stats-grid">
                </div>
        </div>
    </main>

    <footer>
        Auto-refreshing every second.
    </footer>

    <script>
        const statsContainer = document.getElementById('stats-container');
        const loadingState = document.getElementById('loading-state');
        const errorState = document.getElementById('error-state');
        const errorMessage = document.getElementById('error-message');
        const dashboardContent = document.getElementById('dashboard-content');
        const instanceSelect = document.getElementById('instance-select');
        const statsTitle = document.getElementById('stats-title');
        const statsApiUrl = '/api/stats';

        let currentInstanceId = 'All'; // Default to 'All'
        let allStats = {}; // Will hold all instances stats

        // Chart instances (initialized later)
        let answerStatusChart = null;
        let requestTypeChart = null;
        let answerLatencyChart = null;
        let answerSourceChart = null;

        // Chart configuration helper
        const chartColors = {
            blue: 'rgb(59, 130, 246)',
            green: 'rgb(34, 197, 94)',
            yellow: 'rgb(234, 179, 8)',
            red: 'rgb(239, 68, 68)',
            purple: 'rgb(168, 85, 247)',
            orange: 'rgb(249, 115, 22)',
            teal: 'rgb(20, 184, 166)',
            pink: 'rgb(236, 72, 153)',
            gray: 'rgb(107, 114, 128)',
            indigo: 'rgb(99, 102, 241)',
            lime: 'rgb(132, 204, 22)',
            amber: 'rgb(245, 158, 11)',
            emerald: 'rgb(16, 185, 129)',
            sky: 'rgb(14, 165, 233)',
            fuchsia: 'rgb(217, 70, 239)',
        };
        const colorPalette = Object.values(chartColors);

        // --- Chart Initialization Functions ---

        function initAnswerStatusChart(ctx, data) {
            const answerStats = data.answer || {};
            const chartData = {
                labels: ['NoError', 'NoData', 'NXDomain', 'ServFail'],
                datasets: [{
                    label: 'Answer Status',
                    data: [
                        answerStats.noerror || 0,
                        answerStats.nodata || 0,
                        answerStats.nxdomain || 0,
                        answerStats.servfail || 0
                    ],
                    backgroundColor: [chartColors.green, chartColors.yellow, chartColors.red, chartColors.orange],
                    hoverOffset: 4
                }]
            };
            return new Chart(ctx, {
                type: 'doughnut',
                data: chartData,
                options: {
                    responsive: true,
                    plugins: { legend: { position: 'top' } }
                }
            });
        }

        function initRequestTypeChart(ctx, data) {
            const requestStats = data.request || {};
            const chartData = {
                labels: ['UDP', 'TCP', 'DoT', 'DoH', 'Internal', 'XDP'],
                datasets: [{
                    label: 'Request Types',
                    data: [
                        requestStats.udp || 0,
                        requestStats.tcp || 0,
                        requestStats.dot || 0,
                        requestStats.doh || 0,
                        requestStats.internal || 0,
                        requestStats.xdp || 0
                    ],
                    backgroundColor: [chartColors.blue, chartColors.purple, chartColors.teal, chartColors.indigo, chartColors.gray, chartColors.pink],
                    hoverOffset: 4
                }]
            };
            return new Chart(ctx, {
                type: 'doughnut',
                data: chartData,
                options: {
                    responsive: true,
                    plugins: { legend: { position: 'top' } }
                }
            });
        }

        function initAnswerSourceChart(ctx, data) {
            const answerStats = data.answer || {};
            const chartData = {
                labels: ['Cached', 'Stale', 'Other'],
                datasets: [{
                    label: 'Answer Source',
                    data: [
                        answerStats.cached || 0,
                        answerStats.stale || 0,
                        (answerStats.total || 0) - (answerStats.cached || 0) - (answerStats.stale || 0)
                    ],
                    backgroundColor: [chartColors.emerald, chartColors.amber, chartColors.sky],
                    hoverOffset: 4
                }]
            };
            return new Chart(ctx, {
                type: 'doughnut',
                data: chartData,
                options: {
                    responsive: true,
                    plugins: { legend: { position: 'top' } }
                }
            });
        }

        function initAnswerLatencyChart(ctx, data) {
            const answerStats = data.answer || {};
            const labels = ['<1ms', '<10ms', '<50ms', '<100ms', '<250ms', '<500ms', '<1s', '<1.5s', 'Slow'];
            const chartData = {
                labels: labels,
                datasets: [{
                    label: 'Query Count by Latency Bucket',
                    data: [
                        answerStats['1ms'] || 0,
                        answerStats['10ms'] || 0,
                        answerStats['50ms'] || 0,
                        answerStats['100ms'] || 0,
                        answerStats['250ms'] || 0,
                        answerStats['500ms'] || 0,
                        answerStats['1000ms'] || 0,
                        answerStats['1500ms'] || 0,
                        answerStats.slow || 0
                    ],
                    backgroundColor: colorPalette.slice(0, labels.length), // Use palette colors
                    hoverOffset: 4
                }]
            };
            return new Chart(ctx, {
                type: 'doughnut',
                data: chartData,
                options: {
                    responsive: true,
                    plugins: { legend: { position: 'top' } }
                }
            });
        }

        // --- Data Update Functions ---

        function updateChartData(chart, newData) {
            if (chart) {
                chart.data.datasets[0].data = newData;
                chart.update('none'); // 'none' prevents animation on update
            }
        }

        // Function to format numbers nicely
        function formatValue(key, value) {
            if (typeof value !== 'number') {
                return value; // Return non-numbers as is
            }
            if (key.includes('percent')) {
                return `${value.toFixed(2)}%`;
            }
            if (key.includes('rss') || key.includes('bytes') || key.includes('memory')) {
                if (value < 1024) return `${value} B`;
                if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
                if (value < 1024 * 1024 * 1024) return `${(value / (1024 * 1024)).toFixed(1)} MB`;
                return `${(value / (1024 * 1024 * 1024)).toFixed(1)} GB`;
            }
             // Check if it's a count/integer-like value
            if (Number.isInteger(value) || key.includes('count') || key.includes('total') || key.match(/\d+ms|slow$/) || key.match(/^(noerror|nodata|nxdomain|servfail|udp|tcp|dot|doh|internal|xdp|cached|stale)$/)) {
                 return value.toLocaleString();
            }
            // Default to 3 decimal places for other floats (e.g., cpu times)
            return value.toFixed(3);
        }

        // Function to populate the instance selector dropdown
        function populateInstanceSelector(instances) {
            const previouslySelected = instanceSelect.value || currentInstanceId; // Remember what was selected
            instanceSelect.innerHTML = ''; // Clear existing options

            // Add the "All" option first
            const allOption = document.createElement('option');
            allOption.value = 'All';
            allOption.textContent = 'All Instances (Aggregated)';
            instanceSelect.appendChild(allOption);

            // Add individual instance options
            instances.forEach(instance => {
                const option = document.createElement('option');
                option.value = instance;
                option.textContent = instance;
                instanceSelect.appendChild(option);
            });

            // Try to re-select the previously selected option
            if (Array.from(instanceSelect.options).some(opt => opt.value === previouslySelected)) {
                 instanceSelect.value = previouslySelected;
                 currentInstanceId = previouslySelected; // Update currentInstanceId if it changed
            } else {
                // If the previous selection isn't valid anymore, default to 'All'
                instanceSelect.value = 'All';
                currentInstanceId = 'All';
            }
        }

        // Function to aggregate stats from all instances
        function aggregateStats(allInstancesData) {
            const aggregated = {};
            const instanceIds = Object.keys(allInstancesData);

            if (instanceIds.length === 0) {
                return {}; // Return empty if no instances
            }

            // Deep clone the structure of the first instance to initialize aggregation
            // This helps ensure all sections and keys are present
            const firstInstanceData = allInstancesData[instanceIds[0]];
            for (const section in firstInstanceData) {
                aggregated[section] = {};
                for (const key in firstInstanceData[section]) {
                     // Initialize numeric keys to 0, keep others as null/undefined for now
                     aggregated[section][key] = (typeof firstInstanceData[section][key] === 'number') ? 0 : null;
                }
            }


            // Sum numeric stats across all instances
            instanceIds.forEach(id => {
                const instanceData = allInstancesData[id];
                for (const section in instanceData) {
                    if (!aggregated[section]) aggregated[section] = {}; // Ensure section exists
                    for (const key in instanceData[section]) {
                        const value = instanceData[section][key];
                        if (typeof value === 'number') {
                             // Initialize if null or undefined in aggregated structure
                            if (aggregated[section][key] === null || aggregated[section][key] === undefined) {
                                aggregated[section][key] = 0;
                            }
                            aggregated[section][key] = (aggregated[section][key] || 0) + value;
                        } else if (aggregated[section][key] === null || aggregated[section][key] === undefined) {
                            // If it's the first time seeing a non-numeric stat, just take the value
                            // (doesn't make sense to aggregate strings, etc.) - maybe show 'Multiple'?
                            // For simplicity, let's keep it simple and just init to 0 for numbers.
                            // We might need more sophisticated handling for specific non-numeric stats later.
                             if (aggregated[section][key] === null) { // Only set if it's still null
                                // aggregated[section][key] = value; // Or maybe keep it null/indicate mixed?
                             }
                        }
                    }
                }
            });

             // Post-processing: Calculate percentages, ratios if needed based on aggregated sums
            if (aggregated.cache && aggregated.cache.hit_ratio_compute) {
                 const hits = aggregated.cache.hit || 0;
                 const totalLookups = aggregated.cache.lookup || 0;
                 aggregated.cache.hit_percent = totalLookups > 0 ? (hits / totalLookups) * 100 : 0;
                 // Remove the compute flag if it exists
                 delete aggregated.cache.hit_ratio_compute;
            }
             // Example: Calculate cache hit percent if applicable
            if (aggregated.cache && aggregated.cache.hasOwnProperty('hit') && aggregated.cache.hasOwnProperty('lookup')) {
                 const hits = aggregated.cache.hit || 0;
                 const lookups = aggregated.cache.lookup || 0;
                 // Use a more specific key like 'hit_percent_calculated' to avoid conflict
                 aggregated.cache.hit_percent_calculated = lookups > 0 ? (hits / lookups * 100) : 0;
            }


            return aggregated;
        }


        // Function to render raw stats for current instance or aggregated view
        function renderRawStats(dataToRender) {
            statsContainer.innerHTML = ''; // Clear previous raw stats

            if (!dataToRender || Object.keys(dataToRender).length === 0) {
                statsContainer.innerHTML = '<p class="text-gray-500 col-span-full text-center">No statistics available for this selection.</p>';
                return;
            }

            // Sort sections alphabetically, except maybe put 'summary' or 'global' first if they exist
            const sections = Object.keys(dataToRender).sort((a, b) => {
                if (a === 'summary') return -1;
                if (b === 'summary') return 1;
                return a.localeCompare(b);
            });

            sections.forEach(section => {
                const sectionData = dataToRender[section];
                if (typeof sectionData !== 'object' || sectionData === null) return; // Skip non-object sections

                const sectionDiv = document.createElement('div');
                sectionDiv.style.gridColumn = '1 / -1'; // Make section title span all columns
                sectionDiv.innerHTML = `<h3 class="text-lg font-semibold text-gray-700 mt-4 mb-2 capitalize">${section.replace(/_/g, ' ')}</h3>`;
                statsContainer.appendChild(sectionDiv);

                const sortedKeys = Object.keys(sectionData).sort();

                sortedKeys.forEach(key => {
                    const value = sectionData[key];
                    // Only display stats with actual values (not null/undefined)
                    if (value !== null && value !== undefined) {
                        const card = document.createElement('div');
                        card.className = 'stat-card';
                        card.innerHTML = `
                            <div class="stat-key">${key.replace(/_/g, ' ')}</div>
                            <div class="stat-value">${formatValue(key, value)}</div>
                        `;
                        statsContainer.appendChild(card);
                    }
                });
            });
        }

        // Function to update the dashboard with data from the selected instance or 'All'
        function updateDashboard(allInstancesData) {
            // Hide loading/error, show dashboard content
            errorMessage.textContent = '';
            loadingState.style.display = 'none';
            errorState.style.display = 'none';
            dashboardContent.style.display = 'block';

            allStats = allInstancesData; // Store the latest full data
            const instanceIds = Object.keys(allInstancesData);

            // Update instance selector (only if instance list changed?) - safer to update always
             populateInstanceSelector(instanceIds);

            let dataToDisplay;
            let titleSuffix = '';

            if (currentInstanceId === 'All') {
                dataToDisplay = aggregateStats(allInstancesData);
                titleSuffix = ' (Aggregated)';
            } else {
                dataToDisplay = allInstancesData[currentInstanceId];
                if (!dataToDisplay) {
                     // This case should ideally be handled by populateInstanceSelector defaulting to 'All'
                     console.warn(`Selected instance "${currentInstanceId}" not found in data, defaulting to aggregated view.`);
                     currentInstanceId = 'All';
                     instanceSelect.value = 'All';
                     dataToDisplay = aggregateStats(allInstancesData);
                     titleSuffix = ' (Aggregated - Fallback)';
                } else {
                    titleSuffix = ` (${currentInstanceId})`;
                }
            }

             // Update the title for the raw stats section
             statsTitle.textContent = `All Statistics${titleSuffix}`;


            // Render raw stats
            renderRawStats(dataToDisplay);

            // --- Prepare Chart Data ---
            const answerStats = dataToDisplay.answer || {};
            const requestStats = dataToDisplay.request || {};

            const answerStatusData = [
                answerStats.noerror || 0,
                answerStats.nodata || 0,
                answerStats.nxdomain || 0,
                answerStats.servfail || 0
            ];

            const requestTypeData = [
                requestStats.udp || 0,
                requestStats.tcp || 0,
                requestStats.dot || 0,
                requestStats.doh || 0,
                requestStats.internal || 0,
                requestStats.xdp || 0
            ];

            const answerSourceData = [
                answerStats.cached || 0,
                answerStats.stale || 0,
                Math.max(0, (answerStats.total || 0) - (answerStats.cached || 0) - (answerStats.stale || 0)) // Ensure non-negative
            ];

            const answerLatencyData = [
                answerStats['1ms'] || 0,
                answerStats['10ms'] || 0,
                answerStats['50ms'] || 0,
                answerStats['100ms'] || 0,
                answerStats['250ms'] || 0,
                answerStats['500ms'] || 0,
                answerStats['1000ms'] || 0,
                answerStats['1500ms'] || 0,
                answerStats.slow || 0
            ];

            // --- Initialize or Update Charts ---
            if (!answerStatusChart) { // Initialize charts on first successful fetch
                try {
                    answerStatusChart = initAnswerStatusChart(document.getElementById('answerStatusChart').getContext('2d'), dataToDisplay);
                    requestTypeChart = initRequestTypeChart(document.getElementById('requestTypeChart').getContext('2d'), dataToDisplay);
                    answerSourceChart = initAnswerSourceChart(document.getElementById('answerSourceChart').getContext('2d'), dataToDisplay);
                    answerLatencyChart = initAnswerLatencyChart(document.getElementById('answerLatencyChart').getContext('2d'), dataToDisplay);
                } catch (e) {
                    console.error("Error initializing charts:", e);
                    showError("Error initializing charts. Check console for details.");
                }
            } else { // Update existing charts
                 try {
                    updateChartData(answerStatusChart, answerStatusData);
                    updateChartData(requestTypeChart, requestTypeData);
                    updateChartData(answerSourceChart, answerSourceData);
                    updateChartData(answerLatencyChart, answerLatencyData);
                } catch (e) {
                    console.error("Error updating charts:", e);
                    // Don't necessarily show a full error screen, but log it.
                }
            }
        }

        // Function to show error state
        function showError(error) {
            loadingState.style.display = 'none';
            dashboardContent.style.display = 'none'; // Hide dashboard on error
            errorState.style.display = 'block';
            errorMessage.textContent = `Details: ${error}`;
            console.error("Error fetching/processing stats:", error);
        }

        // Function to fetch stats from the Flask backend
        async function fetchStats() {
            try {
                const response = await fetch(statsApiUrl);
                if (!response.ok) {
                    let errorDetails = `HTTP error! Status: ${response.status}`;
                    try {
                        const errorData = await response.json();
                        if (errorData && errorData.error) { errorDetails = errorData.error; }
                    } catch (parseError) { /* Ignore if response is not JSON */ }
                    throw new Error(errorDetails);
                }
                const data = await response.json();
                if (data.error) {
                    throw new Error(data.error);
                }
                 if (typeof data !== 'object' || data === null || Object.keys(data).length === 0) {
                    // Handle case where backend returns valid JSON but it's empty or not an object
                    throw new Error("Received empty or invalid data structure from backend.");
                }
                updateDashboard(data); // Call the main update function
            } catch (error) {
                showError(error.message);
            }
        }

        // Handle instance selection change
        instanceSelect.addEventListener('change', function() {
            currentInstanceId = this.value;
            // Re-render the dashboard immediately with the stored data for the new selection
            if (allStats && Object.keys(allStats).length > 0) {
                updateDashboard(allStats);
            } else {
                // If allStats is empty for some reason, trigger a fetch
                fetchStats();
            }
        });

        // Fetch stats immediately on load
        fetchStats();

        // Set interval to fetch stats every 1000ms (1 second)
        setInterval(fetchStats, 1000);
    </script>
</body>
</html>
"""

# --- Flask Routes ---

@app.route('/')
def index():
    """Renders the main HTML page."""
    return render_template_string(HTML_TEMPLATE, knot_resolver_url=KNOT_RESOLVER_STATS_URL)

@app.route('/api/stats')
def get_stats():
    """Fetches stats from Knot Resolver and returns as JSON."""
    try:
        response = requests.get(KNOT_RESOLVER_STATS_URL, timeout=0.5) # Short timeout for responsiveness
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
        stats_data = response.json()

        # Basic validation: Check if it's a dictionary (expected format)
        if not isinstance(stats_data, dict):
             app.logger.warning(f"Received non-dictionary data from {KNOT_RESOLVER_STATS_URL}")
             return jsonify({"error": "Received unexpected data format from Knot Resolver."}), 500

        return jsonify(stats_data)

    except requests.exceptions.ConnectionError:
        app.logger.error(f"Connection refused to {KNOT_RESOLVER_STATS_URL}")
        return jsonify({"error": f"Connection refused. Is Knot Resolver webmgmt running at {KNOT_RESOLVER_STATS_URL}?"}), 503 # Service Unavailable
    except requests.exceptions.Timeout:
        app.logger.warning(f"Request timed out for {KNOT_RESOLVER_STATS_URL}")
        return jsonify({"error": "Request timed out fetching stats from Knot Resolver."}), 504 # Gateway Timeout
    except requests.exceptions.HTTPError as e:
         app.logger.error(f"HTTP error fetching stats: {e}")
         return jsonify({"error": f"HTTP error {e.response.status_code} from Knot Resolver: {e.response.reason}"}), e.response.status_code if e.response.status_code >= 500 else 500
    except requests.exceptions.RequestException as e:
        app.logger.error(f"General request error fetching stats: {e}")
        return jsonify({"error": f"Failed to fetch stats: {str(e)}"}), 500 # Internal Server Error
    except json.JSONDecodeError:
        app.logger.error(f"Failed to decode JSON from {KNOT_RESOLVER_STATS_URL}")
        return jsonify({"error": "Failed to decode JSON response from Knot Resolver."}), 500 # Internal Server Error
    except Exception as e:
        app.logger.error(f"Unexpected error in /api/stats: {e}", exc_info=True) # Log traceback for unexpected errors
        return jsonify({"error": f"An unexpected server error occurred."}), 500 # Internal Server Error

# --- Main Execution ---
if __name__ == '__main__':
    print("Starting Flask server for Knot Resolver Stats UI...")
    print(f"Fetching stats from: {KNOT_RESOLVER_STATS_URL}")
    print("Access the UI at: http://127.0.0.1:5001")
    # Use waitress or gunicorn for production instead of Flask's development server
    app.run(host='0.0.0.0', port=5001, debug=False) # Turn off debug for production/general use
