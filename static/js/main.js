
// Global variables
let detectionActive = false;
let currentToast = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Main initialization function
function initializeApp() {
    console.log('🚀 Food Calorie Tracker initialized');
    
    // Update navbar calories periodically
    updateNavbarCalories();
    setInterval(updateNavbarCalories, 30000); // Update every 30 seconds
    
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Add keyboard shortcuts
    addKeyboardShortcuts();
}

// Update navbar calories display
function updateNavbarCalories() {
    fetch('/get_daily_summary')
        .then(response => response.json())
        .then(data => {
            const caloriesElement = document.getElementById('today-calories');
            if (caloriesElement) {
                caloriesElement.textContent = data.total_calories || 0;
            }
        })
        .catch(error => {
            console.error('Error updating navbar calories:', error);
        });
}

// Toggle detection logging
function toggleDetection() {
    const toggleBtn = document.getElementById('toggle-detection-btn');
    if (toggleBtn) {
        toggleBtn.disabled = true;
        toggleBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
    }
    
    fetch('/toggle_detection', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        detectionActive = data.detection_active;
        showToast(data.message, 'success');
        
        // Update UI elements
        updateDetectionStatus();
        
        // Re-enable button
        if (toggleBtn) {
            toggleBtn.disabled = false;
        }
    })
    .catch(error => {
        console.error('Error toggling detection:', error);
        showToast('Error toggling detection', 'error');
        
        // Re-enable button
        if (toggleBtn) {
            toggleBtn.disabled = false;
            updateToggleButton();
        }
    });
}

// Update detection status across UI
function updateDetectionStatus() {
    // Update all toggle buttons
    const toggleButtons = document.querySelectorAll('#toggle-detection-btn');
    toggleButtons.forEach(updateToggleButton);
    
    // Update status indicators
    const statusIndicators = document.querySelectorAll('#status-indicator');
    const statusTexts = document.querySelectorAll('#status-text');
    
    statusIndicators.forEach(indicator => {
        indicator.className = detectionActive ? 
            'status-indicator me-2 bg-success' : 
            'status-indicator me-2 bg-danger';
    });
    
    statusTexts.forEach(text => {
        text.textContent = detectionActive ? 'Detection Active' : 'Detection Paused';
    });
}

// Update individual toggle button
function updateToggleButton(button = null) {
    if (!button) {
        button = document.getElementById('toggle-detection-btn');
    }
    
    if (!button) return;
    
    if (detectionActive) {
        button.className = 'btn btn-danger btn-sm';
        button.innerHTML = '<i class="fas fa-pause me-1"></i><span>Stop Logging</span>';
    } else {
        button.className = 'btn btn-success btn-sm';
        button.innerHTML = '<i class="fas fa-play me-1"></i><span>Start Logging</span>';
    }
}

// Show toast notification
function showToast(message, type = 'info', duration = 4000) {
    // Dismiss current toast if exists
    if (currentToast) {
        currentToast.hide();
    }
    
    const toastElement = document.getElementById('notification-toast');
    const toastMessage = document.getElementById('toast-message');
    
    if (!toastElement || !toastMessage) return;
    
    // Set message and style based on type
    toastMessage.textContent = message;
    
    // Remove existing classes
    toastElement.classList.remove('bg-success', 'bg-danger', 'bg-warning', 'bg-info');
    
    // Add appropriate class
    switch (type) {
        case 'success':
            toastElement.classList.add('bg-success', 'text-white');
            break;
        case 'error':
        case 'danger':
            toastElement.classList.add('bg-danger', 'text-white');
            break;
        case 'warning':
            toastElement.classList.add('bg-warning');
            break;
        default:
            toastElement.classList.add('bg-info', 'text-white');
    }
    
    // Show toast
    currentToast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: duration
    });
    currentToast.show();
}

// Export data functionality
function exportData() {
    showToast('Preparing data export...', 'info');
    
    fetch('/export_data')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'error') {
                showToast(data.message, 'error');
                return;
            }
            
            // Create download link
            const dataStr = JSON.stringify(data, null, 2);
            const dataBlob = new Blob([dataStr], {type: 'application/json'});
            const url = URL.createObjectURL(dataBlob);
            
            const link = document.createElement('a');
            link.href = url;
            link.download = `food-tracker-export-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            URL.revokeObjectURL(url);
            showToast('Data exported successfully!', 'success');
        })
        .catch(error => {
            console.error('Error exporting data:', error);
            showToast('Error exporting data', 'error');
        });
}

// Clear today's logs
function clearTodayLogs() {
    if (!confirm('Are you sure you want to clear today\'s logs? This cannot be undone.')) {
        return;
    }
    
    fetch('/clear_today_logs', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showToast(data.message, 'success');
            // Refresh the page after a short delay
            setTimeout(() => {
                location.reload();
            }, 1500);
        } else {
            showToast(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error clearing logs:', error);
        showToast('Error clearing logs', 'error');
    });
}

// Refresh recent detections (for dashboard)
function refreshRecentDetections() {
    const container = document.getElementById('recent-detections-list');
    if (!container) return;
    
    // Show loading state
    container.innerHTML = `
        <div class="text-center py-3">
            <div class="spinner-border spinner-border-sm me-2"></div>
            Loading recent detections...
        </div>
    `;
    
    fetch('/get_recent_detections')
        .then(response => response.json())
        .then(detections => {
            if (detections.length === 0) {
                container.innerHTML = `
                    <p class="text-muted text-center mb-0">
                        <i class="fas fa-search fa-2x mb-2 d-block"></i>
                        No recent detections
                    </p>
                `;
                return;
            }
            
            container.innerHTML = '';
            
            // Show last 5 detections
            const recentDetections = detections.slice(-5).reverse();
            
            recentDetections.forEach(detection => {
                const timeAgo = getTimeAgo(detection.timestamp);
                const confidence = Math.round(detection.confidence * 100);
                
                const detectionDiv = document.createElement('div');
                detectionDiv.className = 'd-flex justify-content-between align-items-center mb-2 p-2 bg-light rounded fade-in';
                detectionDiv.innerHTML = `
                    <div>
                        <strong>${getFoodEmoji(detection.food)} ${detection.food}</strong>
                        <small class="text-muted d-block">${timeAgo}</small>
                    </div>
                    <div class="text-end">
                        <span class="badge bg-success">${detection.calories} cal</span>
                        <small class="d-block text-muted">${confidence}%</small>
                    </div>
                `;
                
                container.appendChild(detectionDiv);
            });
        })
        .catch(error => {
            console.error('Error refreshing detections:', error);
            container.innerHTML = `
                <div class="text-center text-danger py-3">
                    <i class="fas fa-exclamation-triangle mb-2"></i>
                    <div>Error loading detections</div>
                </div>
            `;
        });
}

// Utility function to get time ago string
function getTimeAgo(timestamp) {
    const now = new Date();
    const detectionTime = new Date(timestamp);
    const diffMs = now - detectionTime;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffSecs < 60) return `${diffSecs}s ago`;
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
}

// Get food emoji utility
function getFoodEmoji(food) {
    const emojiMap = {
        'Apple': '🍎',
        'Orange': '🍊',
        'Banana': '🍌',
        'Strawberry': '🍓',
        'Cucumber': '🥒',
        'Pizza': '🍕',
        'Watermelon': '🍉',
        'Bread': '🍞',
        'Broccoli': '🥦',
        'Carrot': '🥕'
    };
    return emojiMap[food] || '🍽️';
}

// Add keyboard shortcuts
function addKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Space: Toggle detection
        if ((e.ctrlKey || e.metaKey) && e.code === 'Space') {
            e.preventDefault();
            toggleDetection();
        }
        
        // Ctrl/Cmd + E: Export data
        if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
            e.preventDefault();
            exportData();
        }
        
        // Ctrl/Cmd + R: Refresh current view
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            // Let default behavior happen, but also refresh detection lists
            setTimeout(() => {
                if (typeof refreshRecentDetections === 'function') {
                    refreshRecentDetections();
                }
            }, 100);
        }
    });
}

// Format number with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Debounce function for performance
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

// Throttle function for performance
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Check if device is mobile
function isMobile() {
    return window.innerWidth <= 768;
}

// Handle responsive behavior
function handleResponsive() {
    if (isMobile()) {
        // Add mobile-specific classes or behavior
        document.body.classList.add('mobile-device');
    } else {
        document.body.classList.remove('mobile-device');
    }
}

// Add resize listener for responsive behavior
window.addEventListener('resize', debounce(handleResponsive, 250));

// Initialize responsive behavior
handleResponsive();

// Error handling for fetch requests
function handleFetchError(error) {
    console.error('Fetch error:', error);
    showToast('Network error. Please check your connection.', 'error');
}

// Generic fetch wrapper with error handling
async function safeFetch(url, options = {}) {
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        handleFetchError(error);
        throw error;
    }
}

// Expose global functions
window.toggleDetection = toggleDetection;
window.exportData = exportData;
window.clearTodayLogs = clearTodayLogs;
window.refreshRecentDetections = refreshRecentDetections;
window.showToast = showToast;
window.getFoodEmoji = getFoodEmoji;
window.getTimeAgo = getTimeAgo;
window.formatNumber = formatNumber;