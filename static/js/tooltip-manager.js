// --- START OF FILE tooltip-manager.js ---
/**
 * Tooltip management
 * This module handles tooltip initialization across the application
 */

/**
 * Initialize tooltips
 * @param {string} [selector='[data-bs-toggle="tooltip"]'] - Selector for tooltip elements
 * @returns {Array} - Array of Bootstrap tooltip instances
 */
function initTooltips(selector = '[data-bs-toggle="tooltip"]') {
    const tooltipTriggerList = document.querySelectorAll(selector);
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => 
        new bootstrap.Tooltip(tooltipTriggerEl, {
            boundary: document.body // Ensures tooltips are properly positioned
        })
    );
    
    return tooltipList;
}

/**
 * Refresh tooltips (destroy and reinitialize)
 * @param {string} [selector='[data-bs-toggle="tooltip"]'] - Selector for tooltip elements
 * @returns {Array} - Array of Bootstrap tooltip instances
 */
function refreshTooltips(selector = '[data-bs-toggle="tooltip"]') {
    // Dispose existing tooltips
    const tooltipTriggerList = document.querySelectorAll(selector);
    [...tooltipTriggerList].forEach(tooltipTriggerEl => {
        const tooltip = bootstrap.Tooltip.getInstance(tooltipTriggerEl);
        if (tooltip) {
            tooltip.dispose();
        }
    });
    
    // Initialize new tooltips
    return initTooltips(selector);
}

// Initialize tooltips on DOM content loaded
document.addEventListener('DOMContentLoaded', function() {
    initTooltips();
});

// Export the module
window.TooltipManager = {
    init: initTooltips,
    refresh: refreshTooltips
};
// --- END OF FILE tooltip-manager.js ---
