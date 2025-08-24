// 🚀 Helix Dashboard - Interactive functionality

class HelixDashboard {
    constructor() {
        this.charts = {};
        this.updateInterval = null;
        this.wsConnection = null;
        this.data = {};
    }
    
    initialize(data) {
        this.data = data;
        this.initializeCharts();
        this.initializeRealtimeUpdates();
        this.bindEvents();
        console.log('🎛️ Helix Dashboard initialized with Swiss precision!');
    }
    
    initializeCharts() {
        this.initializeFileTypesChart();
        this.initializePerformanceChart();
    }
    
    initializeFileTypesChart() {
        const ctx = document.getElementById('fileTypesChart');
        if (!ctx) return;
        
        const fileTypes = this.data.processing_stats?.files_by_type || {};
        
        this.charts.fileTypes = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(fileTypes).map(type => {
                    const emojis = {
                        'MT940': '💰 MT940',
                        'CAMT.053': '💼 CAMT.053',
                        'BAI2': '🏛️ BAI2',
                        'CSV': '📊 CSV'
                    };
                    return emojis[type] || `📄 ${type}`;
                }),
                datasets: [{
                    data: Object.values(fileTypes),
                    backgroundColor: [
                        '#667eea',
                        '#764ba2',
                        '#f7931e',
                        '#10b981',
                        '#f59e0b'
                    ],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    initializePerformanceChart() {
        const ctx = document.getElementById('performanceChart');
        if (!ctx) return;
        
        const processingTimes = this.data.processing_stats?.processing_times || [];
        
        this.charts.performance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: processingTimes.map((_, index) => `File ${index + 1}`),
                datasets: [{
                    label: 'Processing Time (seconds)',
                    data: processingTimes,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Seconds'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
    
    initializeRealtimeUpdates() {
        // Poll for updates every 5 seconds
        this.updateInterval = setInterval(() => {
            this.fetchDashboardData();
        }, 5000);
        
        // Try to establish WebSocket connection for real-time updates
        this.initializeWebSocket();
    }
    
    initializeWebSocket() {
        // WebSocket implementation for real-time updates
        // This would connect to a WebSocket endpoint if available
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/dashboard`;
            
            this.wsConnection = new WebSocket(wsUrl);
            
            this.wsConnection.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.updateDashboard(data);
            };
            
            this.wsConnection.onerror = () => {
                console.log('WebSocket not available, using polling instead');
            };
        } catch (error) {
            console.log('WebSocket not supported, using polling for updates');
        }
    }
    
    async fetchDashboardData() {
        try {
            const response = await fetch('/api/dashboard/stats');
            if (response.ok) {
                const data = await response.json();
                this.updateDashboard(data);
            }
        } catch (error) {
            console.error('Failed to fetch dashboard data:', error);
        }
    }
    
    updateDashboard(data) {
        this.data = { ...this.data, ...data };
        
        // Update stats cards
        this.updateStatsCards(data);
        
        // Update activity feed
        this.updateActivityFeed(data.recent_activities);
        
        // Update processing queue
        this.updateProcessingQueue(data.current_processing);
        
        // Update charts if needed
        if (data.processing_stats) {
            this.updateCharts(data.processing_stats);
        }
    }
    
    updateStatsCards(data) {
        const stats = data.processing_stats || {};
        
        // Update individual stat values
        this.updateElement('filesProcessedToday', stats.total_files_processed || 0);
        this.updateElement('transactionsProcessed', this.formatNumber(stats.total_transactions || 0));
        this.updateElement('processingSpeed', `${stats.avg_processing_time || 0}s`);
        this.updateElement('successRate', `${stats.success_rate || 100}%`);
        this.updateElement('currentlyProcessing', Object.keys(data.current_processing || {}).length);
    }
    
    updateActivityFeed(activities) {
        const feedElement = document.getElementById('activityFeed');
        if (!feedElement || !activities) return;
        
        const activityHTML = activities.slice(0, 10).map(activity => `
            <div class="activity-item">
                <div class="activity-icon">${activity.emoji || 'ℹ️'}</div>
                <div class="activity-content">
                    <div class="activity-message">${activity.message}</div>
                    <div class="activity-time">${this.timeAgo(activity.timestamp)}</div>
                </div>
            </div>
        `).join('');
        
        feedElement.innerHTML = activityHTML;
    }
    
    updateProcessingQueue(currentProcessing) {
        const queueElement = document.getElementById('processingQueue');
        if (!queueElement) return;
        
        if (!currentProcessing || Object.keys(currentProcessing).length === 0) {
            queueElement.innerHTML = `
                <div class="text-center p-4">
                    <div style="font-size: 3rem; opacity: 0.5;">⏱️</div>
                    <p>No files currently processing</p>
                    <p class="text-muted">Upload files above to get started</p>
                </div>
            `;
            return;
        }
        
        const queueHTML = Object.entries(currentProcessing).map(([jobId, job]) => `
            <div class="file-item processing">
                <div class="file-icon">${job.file_type_emoji || '📄'}</div>
                <div class="file-info">
                    <div class="file-name">${job.filename || 'Unknown file'}</div>
                    <div class="file-meta">
                        ${job.routing_code || 'Unknown route'} • Started ${this.timeAgo(job.started_at)}
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${job.progress || 0}%"></div>
                    </div>
                </div>
                <div class="file-status processing">Processing</div>
            </div>
        `).join('');
        
        queueElement.innerHTML = queueHTML;
    }
    
    updateCharts(stats) {
        // Update file types chart
        if (this.charts.fileTypes && stats.files_by_type) {
            const chart = this.charts.fileTypes;
            chart.data.datasets[0].data = Object.values(stats.files_by_type);
            chart.update('none');
        }
        
        // Update performance chart
        if (this.charts.performance && stats.processing_times) {
            const chart = this.charts.performance;
            chart.data.datasets[0].data = stats.processing_times;
            chart.data.labels = stats.processing_times.map((_, index) => `File ${index + 1}`);
            chart.update('none');
        }
    }
    
    bindEvents() {
        // Refresh button for activity feed
        window.refreshActivityFeed = () => {
            this.fetchDashboardData();
            showNotification('🔄 Activity feed refreshed', 'info');
        };
        
        // Export activity log
        window.exportActivityLog = () => {
            const activities = this.data.recent_activities || [];
            const csvContent = this.convertToCSV(activities);
            this.downloadCSV(csvContent, 'helix_activity_log.csv');
            showNotification('📤 Activity log exported', 'success');
        };
        
        // Auto-refresh toggle
        const refreshToggle = document.getElementById('autoRefreshToggle');
        if (refreshToggle) {
            refreshToggle.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.startAutoRefresh();
                } else {
                    this.stopAutoRefresh();
                }
            });
        }
    }
    
    // Utility Methods
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }
    
    formatNumber(num) {
        return new Intl.NumberFormat().format(num);
    }
    
    timeAgo(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diff = now - time;
        
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);
        
        if (seconds < 60) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        return `${days}d ago`;
    }
    
    convertToCSV(data) {
        const headers = ['Timestamp', 'Type', 'Message', 'Level'];
        const rows = data.map(item => [
            item.timestamp,
            item.type,
            item.message.replace(/"/g, '""'),
            item.level
        ]);
        
        const csvContent = [headers, ...rows]
            .map(row => row.map(field => `"${field}"`).join(','))
            .join('\n');
            
        return csvContent;
    }
    
    downloadCSV(content, filename) {
        const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    startAutoRefresh() {
        if (this.updateInterval) return;
        
        this.updateInterval = setInterval(() => {
            this.fetchDashboardData();
        }, 5000);
        
        showNotification('🔄 Auto-refresh enabled', 'info');
    }
    
    stopAutoRefresh() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        
        showNotification('⏸️ Auto-refresh disabled', 'info');
    }
    
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        
        if (this.wsConnection) {
            this.wsConnection.close();
        }
        
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
    }
}

// Global dashboard instance
let dashboard = null;

// Initialize dashboard
function initializeDashboard(data) {
    dashboard = new HelixDashboard();
    dashboard.initialize(data);
}

// Start real-time updates
function startRealtimeUpdates() {
    if (dashboard) {
        dashboard.startAutoRefresh();
    }
}

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (dashboard) {
        dashboard.destroy();
    }
});
