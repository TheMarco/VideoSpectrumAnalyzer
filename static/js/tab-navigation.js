// --- START OF FILE tab-navigation.js ---
/**
 * Tab navigation utilities
 * This module provides functions for managing tabbed interfaces
 */

/**
 * Show a specific tab
 * @param {string} tabId - The ID of the tab pane to show
 */
function showTab(tabId) {
    const tabElement = document.querySelector(`[data-bs-target="#${tabId}"]`);
    if (tabElement) {
        const tabInstance = new bootstrap.Tab(tabElement);
        tabInstance.show();
    }
}

/**
 * Show the first tab
 * @param {string} [tabsContainerId='configTabs'] - The ID of the tabs container
 */
function showFirstTab(tabsContainerId = 'configTabs') {
    const firstTab = document.querySelector(`#${tabsContainerId} .nav-link`);
    if (firstTab) {
        const tabInstance = new bootstrap.Tab(firstTab);
        tabInstance.show();
    }
}

/**
 * Mark a tab as having an error
 * @param {string} tabId - The ID of the tab pane with the error
 */
function markTabWithError(tabId) {
    const tabElement = document.querySelector(`[data-bs-target="#${tabId}"]`);
    if (tabElement) {
        tabElement.classList.add('tab-error');

        // Remove existing error indicator if any
        const existingIndicator = tabElement.querySelector('.tab-error-indicator');
        if (existingIndicator) {
            existingIndicator.remove();
        }

        // Add error indicator
        const errorIndicator = document.createElement('span');
        errorIndicator.className = 'tab-error-indicator ms-2';
        errorIndicator.innerHTML = '<i class="bi bi-exclamation-circle-fill text-danger"></i>';
        tabElement.appendChild(errorIndicator);
    }
}

/**
 * Clear all tab error indicators
 */
function clearTabErrors() {
    document.querySelectorAll('.tab-error').forEach(tab => {
        tab.classList.remove('tab-error');
    });

    document.querySelectorAll('.tab-error-indicator').forEach(indicator => {
        indicator.remove();
    });
}

/**
 * Get the tab ID containing a specific element
 * @param {HTMLElement} element - The element to find the containing tab for
 * @returns {string|null} - The tab ID or null if not found
 */
function getTabIdForElement(element) {
    if (!element) return null;

    const tabPane = element.closest('.tab-pane');
    return tabPane ? tabPane.id : null;
}

/**
 * Show the first tab that contains an error
 */
function showFirstTabWithError() {
    // Find all elements with the 'is-invalid' class
    const invalidElements = document.querySelectorAll('.is-invalid');
    if (invalidElements.length === 0) return;

    // Find the first tab containing an invalid element
    for (const element of invalidElements) {
        const tabId = getTabIdForElement(element);
        if (tabId) {
            showTab(tabId);
            break;
        }
    }
}

// Export the module
window.TabNavigation = {
    showTab: showTab,
    showFirstTab: showFirstTab,
    markTabWithError: markTabWithError,
    clearTabErrors: clearTabErrors,
    getTabIdForElement: getTabIdForElement,
    showFirstTabWithError: showFirstTabWithError
};
// --- END OF FILE tab-navigation.js ---
