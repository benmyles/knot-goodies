# /// script
# dependencies = [
#   "flask>=2.0",
#   "requests>=2.20",
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
#   'http',
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
KNOT_RESOLVER_STATS_URL = "http://127.0.0.1:8453/stats"
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
            <div class="charts-grid">
                <div class="chart-card">
                    <div class="chart-title">Answer Status Distribution</div>
                    <canvas id="answerStatusChart"></canvas>
                </div>
                <div class="chart-card">
                    <div class="chart-title">Request Type Distribution</div>
                    <canvas id="requestTypeChart"></canvas>
                </div>
                <div class="chart-card" style="grid-column: 1 / -1;"> <div class="chart-title">Answer Latency (ms)</div>
                    <canvas id="answerLatencyChart"></canvas>
                </div>
            </div>

            <h2 class="section-title">All Statistics</h2>
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
        const statsApiUrl = '/api/stats';

        // Chart instances (initialized later)
        let answerStatusChart = null;
        let requestTypeChart = null;
        let answerLatencyChart = null;

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
        };
        const colorPalette = Object.values(chartColors);

        // --- Chart Initialization Functions ---

        function initAnswerStatusChart(ctx, data) {
            const chartData = {
                labels: ['NoError', 'NoData', 'NXDomain', 'ServFail'],
                datasets: [{
                    label: 'Answer Status',
                    data: [
                        data['answer.noerror'] || 0,
                        data['answer.nodata'] || 0,
                        data['answer.nxdomain'] || 0,
                        data['answer.servfail'] || 0
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
             const chartData = {
                labels: ['UDP', 'TCP', 'DoT', 'DoH', 'Internal'], // Added Internal
                datasets: [{
                    label: 'Request Types',
                    data: [
                        data['request.udp'] || 0,
                        data['request.tcp'] || 0,
                        data['request.dot'] || 0,
                        data['request.doh'] || 0,
                        data['request.internal'] || 0 // Include internal requests
                    ],
                    backgroundColor: [chartColors.blue, chartColors.purple, chartColors.teal, chartColors.indigo, chartColors.gray],
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
            const labels = ['<1ms', '<10ms', '<50ms', '<100ms', '<250ms', '<500ms', '<1s', '<1.5s', 'Slow'];
            const chartData = {
                labels: labels,
                datasets: [{
                    label: 'Query Count by Latency Bucket',
                    data: [
                        data['answer.1ms'] || 0,
                        data['answer.10ms'] || 0,
                        data['answer.50ms'] || 0,
                        data['answer.100ms'] || 0,
                        data['answer.250ms'] || 0,
                        data['answer.500ms'] || 0,
                        data['answer.1000ms'] || 0,
                        data['answer.1500ms'] || 0,
                        data['answer.slow'] || 0
                    ],
                    backgroundColor: colorPalette.slice(0, labels.length), // Use palette colors
                    borderColor: colorPalette.map(c => c.replace(')', ', 0.8)').replace('rgb', 'rgba')), // Slightly darker border
                    borderWidth: 1
                }]
            };
            return new Chart(ctx, {
                type: 'bar',
                data: chartData,
                options: {
                    responsive: true,
                    scales: { y: { beginAtZero: true, title: { display: true, text: 'Number of Queries' } } },
                    plugins: { legend: { display: false } } // Hide legend for bar chart if desired
                }
            });
        }

        // --- Data Update Functions ---

        function updateChartData(chart, newData) {
            if (chart) {
                chart.data.datasets[0].data = newData;
                chart.update();
            }
        }

        // Function to format numbers nicely
        function formatValue(key, value) {
            // ... (keep the existing formatValue function) ...
             if (typeof value !== 'number') {
                return value;
            }
            if (key.includes('percent')) {
                return `${value.toFixed(2)}%`;
            }
             if (key.includes('rss') || key.includes('bytes')) {
                if (value < 1024) return `${value} B`;
                if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
                if (value < 1024 * 1024 * 1024) return `${(value / (1024 * 1024)).toFixed(1)} MB`;
                return `${(value / (1024 * 1024 * 1024)).toFixed(1)} GB`;
            }
            if (Number.isInteger(value)) {
                return value.toLocaleString();
            }
            return value.toFixed(3);
        }

        // Function to update the stats display (raw grid + charts)
        function updateDashboard(stats) {
            // Hide loading/error, show dashboard content
            errorMessage.textContent = '';
            loadingState.style.display = 'none';
            errorState.style.display = 'none';
            dashboardContent.style.display = 'block'; // Show the main content area

            // --- Update Charts ---
            const answerStatusData = [
                stats['answer.noerror'] || 0, stats['answer.nodata'] || 0,
                stats['answer.nxdomain'] || 0, stats['answer.servfail'] || 0
            ];
            const requestTypeData = [
                 stats['request.udp'] || 0, stats['request.tcp'] || 0,
                 stats['request.dot'] || 0, stats['request.doh'] || 0,
                 stats['request.internal'] || 0
            ];
            const answerLatencyData = [
                stats['answer.1ms'] || 0, stats['answer.10ms'] || 0, stats['answer.50ms'] || 0,
                stats['answer.100ms'] || 0, stats['answer.250ms'] || 0, stats['answer.500ms'] || 0,
                stats['answer.1000ms'] || 0, stats['answer.1500ms'] || 0, stats['answer.slow'] || 0
            ];

            if (!answerStatusChart) { // Initialize charts on first successful fetch
                answerStatusChart = initAnswerStatusChart(document.getElementById('answerStatusChart').getContext('2d'), stats);
                requestTypeChart = initRequestTypeChart(document.getElementById('requestTypeChart').getContext('2d'), stats);
                answerLatencyChart = initAnswerLatencyChart(document.getElementById('answerLatencyChart').getContext('2d'), stats);
            } else { // Update existing charts
                updateChartData(answerStatusChart, answerStatusData);
                updateChartData(requestTypeChart, requestTypeData);
                updateChartData(answerLatencyChart, answerLatencyData);
            }

            // --- Update Raw Stats Grid ---
            statsContainer.innerHTML = ''; // Clear previous raw stats
            const sortedKeys = Object.keys(stats).sort();

            sortedKeys.forEach(key => {
                const value = stats[key];
                const card = document.createElement('div');
                card.className = 'stat-card'; // Use the updated card class
                card.innerHTML = `
                    <div class="stat-key">${key}</div>
                    <div class="stat-value">${formatValue(key, value)}</div>
                `;
                statsContainer.appendChild(card);
            });
        }

        // Function to show error state
        function showError(error) {
            loadingState.style.display = 'none';
            dashboardContent.style.display = 'none'; // Hide dashboard on error
            errorState.style.display = 'block';
            errorMessage.textContent = `Details: ${error}`;
            console.error("Error fetching stats:", error);
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
                    } catch (parseError) { /* Ignore */ }
                    throw new Error(errorDetails);
                }
                const data = await response.json();
                if (data.error) {
                     throw new Error(data.error);
                }
                updateDashboard(data); // Call the main update function
            } catch (error) {
                showError(error.message);
            }
        }

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
        response = requests.get(KNOT_RESOLVER_STATS_URL, timeout=0.5)
        response.raise_for_status()
        stats_data = response.json()
        return jsonify(stats_data)
    except requests.exceptions.ConnectionError:
        return jsonify({"error": f"Connection refused. Is Knot Resolver running at {KNOT_RESOLVER_STATS_URL}?"}), 503
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out."}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch stats: {str(e)}"}), 500
    except json.JSONDecodeError:
        return jsonify({"error": "Failed to decode JSON response from Knot Resolver."}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error fetching stats: {e}", exc_info=True)
        return jsonify({"error": f"An unexpected server error occurred: {str(e)}"}), 500

# --- Main Execution ---
if __name__ == '__main__':
    print("Starting Flask server for Knot Resolver Stats UI...")
    print(f"Fetching stats from: {KNOT_RESOLVER_STATS_URL}")
    print("Access the UI at: http://127.0.0.1:5001")
    app.run(host='0.0.0.0', port=5001, debug=False)
