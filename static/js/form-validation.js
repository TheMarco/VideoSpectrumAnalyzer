// Form validation and error handling utilities
// This file contains shared code for form validation and error handling
// that can be used across different visualizer forms

/**
 * Shows a validation error with improved UI using a modal dialog
 * @param {Object} errorInfo - Information about the error
 * @param {HTMLElement} errorInfo.field - The field that has the error
 * @param {string} errorInfo.friendlyName - User-friendly name of the field
 * @param {string} errorInfo.tabName - Name of the tab containing the field
 * @param {string} errorInfo.message - Error message
 * @param {string} errorInfo.description - Additional description of the field
 */
function showValidationError(errorInfo) {
    console.log("VALIDATION ERROR:", errorInfo);

    // Store field and tab information for later use
    const field = errorInfo.field;
    const tabPane = field ? field.closest('.tab-pane') : null;
    let tabId = null;

    if (tabPane) {
        tabId = tabPane.id;

        // Mark the tab with an error indicator
        if (window.TabNavigation) {
            window.TabNavigation.markTabWithError(tabId);
        }
    }

    // Highlight the field with error
    if (field) {
        field.classList.add('is-invalid');

        // Remove the invalid class after 5 seconds
        setTimeout(() => {
            field.classList.remove('is-invalid');
        }, 5000);
    }

    // Create a more detailed error message for the modal
    const errorMessage = `
        <div class="error-content">
            <div class="error-message"><strong>${errorInfo.friendlyName}</strong>: ${errorInfo.message}</div>
            ${errorInfo.description ? `<div class="error-description">${errorInfo.description}</div>` : ''}
            <div class="error-location mt-2">
                <span class="badge bg-secondary"><i class="bi bi-layout-text-window me-1"></i>${errorInfo.tabName} Tab</span>
            </div>
        </div>
    `;

    // Show the error in a modal
    showErrorModal({
        title: 'Validation Error',
        message: errorMessage,
        field: field,
        tabId: tabId
    });
}

/**
 * Helper function to get tab name from field
 * @param {HTMLElement} field - The form field
 * @returns {string} - The name of the tab containing the field
 */
function getTabNameFromField(field) {
    // Find the tab pane containing this field
    const tabPane = field.closest('.tab-pane');
    if (!tabPane) return "Unknown";

    // Get the tab ID
    const tabId = tabPane.id;

    // Find the tab button for this pane
    const tabButton = document.querySelector(`[data-bs-target="#${tabId}"]`);
    if (!tabButton) return "Unknown";

    // Extract the tab name from the button text
    const tabText = tabButton.textContent.trim();
    // Remove any numbers and icons from the tab name
    return tabText.replace(/^\d+\.\s*/, '').replace(/^\s*\S+\s+/, '').trim();
}

/**
 * Shows an error message in a modal dialog
 * @param {Object} errorOptions - Options for the error modal
 * @param {string} errorOptions.title - The title of the error modal
 * @param {string} errorOptions.message - The error message to display
 * @param {HTMLElement} [errorOptions.field] - The field that has the error
 * @param {string} [errorOptions.tabId] - The ID of the tab containing the error field
 */
function showErrorModal(errorOptions) {
    // Handle undefined message
    if (errorOptions.message === undefined) {
        console.log("Form validation: Detected undefined error message");

        // Try to use the shader error handler first
        if (window.ShaderErrorHandler) {
            const shaderPath = document.getElementById('shader_path');
            const shaderName = shaderPath ? shaderPath.options[shaderPath.selectedIndex].text : "Unknown Shader";

            window.ShaderErrorHandler.showShaderError(
                shaderName,
                "The shader failed to render. This could be due to compatibility issues with your graphics hardware or syntax errors in the shader code."
            );
            return;
        }

        // If shader error handler is not available, use a generic error message
        errorOptions.message = "An error occurred while processing the shader. Please try a different shader or check the console for more details.";
    }

    // Handle undefined title
    if (errorOptions.title === undefined) {
        errorOptions.title = "Error";
    }

    console.error("Error displayed:", errorOptions.message);

    // Use the modal manager if available
    if (window.ModalManager) {
        const modalContent = {
            title: `<i class="bi bi-exclamation-triangle-fill me-2"></i>${errorOptions.title}`,
            content: errorOptions.message
        };

        // Show the modal
        window.ModalManager.showModal('errorModal', modalContent);

        // Configure "Go to Field" button
        const goToFieldBtn = document.getElementById('goToFieldBtn');
        if (goToFieldBtn) {
            if (errorOptions.field && errorOptions.tabId) {
                goToFieldBtn.style.display = 'block';

                // Remove any existing click handlers
                const newGoToFieldBtn = goToFieldBtn.cloneNode(true);
                goToFieldBtn.parentNode.replaceChild(newGoToFieldBtn, goToFieldBtn);

                // Add click handler to go to the field
                newGoToFieldBtn.addEventListener('click', function() {
                    // Hide the modal
                    window.ModalManager.hideModal('errorModal');

                    // Show the tab containing the field
                    if (window.TabNavigation && errorOptions.tabId) {
                        window.TabNavigation.showTab(errorOptions.tabId);
                    }

                    // Focus and scroll to the field
                    setTimeout(() => {
                        if (errorOptions.field) {
                            errorOptions.field.focus();
                            errorOptions.field.scrollIntoView({ behavior: 'smooth', block: 'center' });

                            // Add a temporary highlight effect
                            errorOptions.field.classList.add('is-invalid');
                            setTimeout(() => {
                                errorOptions.field.classList.remove('is-invalid');
                            }, 5000);
                        }
                    }, 400); // Wait for tab transition
                });
            } else {
                goToFieldBtn.style.display = 'none';
            }
        }

        return;
    }

    // Fallback if modal manager is not available
    console.log("Fallback error modal display");
    showErrorFallback(errorOptions.message);

    // Handle any ongoing processes
    const progressInterval = window.progressInterval; // Access from window scope
    if (progressInterval) clearInterval(progressInterval);

    // Update submit button state
    const submitBtn = document.getElementById('submit-btn');
    if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="bi bi-magic me-2"></i> Generate Visualization';
    }
}

/**
 * Shows an error message with animations (fallback method)
 * @param {string} message - The error message to display
 */
function showErrorFallback(message) {
    console.error("Using fallback error display method");

    // Get UI elements
    const configTabs = document.getElementById('configTabs');
    const configTabsContent = document.getElementById('configTabsContent');
    const processingCard = document.getElementById('processing-card');
    const errorCard = document.getElementById('error-card');
    const errorMessage = document.getElementById('error-message');
    const progressInterval = window.progressInterval; // Access from window scope

    // Fade out other elements
    if (configTabs) {
        configTabs.style.opacity = '0';
        configTabs.style.transition = 'opacity 0.3s ease';
        setTimeout(() => { configTabs.style.display = 'none'; }, 300);
    }

    if (configTabsContent) {
        configTabsContent.style.opacity = '0';
        configTabsContent.style.transition = 'opacity 0.3s ease';
        setTimeout(() => { configTabsContent.style.display = 'none'; }, 300);
    }

    if (processingCard && processingCard.style.display === 'block') {
        processingCard.style.opacity = '0';
        processingCard.style.transition = 'opacity 0.3s ease';
        setTimeout(() => { processingCard.style.display = 'none'; }, 300);
    }

    // Show error card with animation
    setTimeout(() => {
        if (errorCard) {
            errorCard.style.display = 'block';
            errorCard.style.opacity = '0';

            // Check if the message contains HTML
            if (errorMessage) {
                if (message.includes('<') && message.includes('>')) {
                    // It's HTML content, use innerHTML
                    errorMessage.innerHTML = message;
                } else {
                    // It's plain text, use textContent for security
                    errorMessage.textContent = message;
                }
            }

            setTimeout(() => {
                errorCard.style.opacity = '1';
                errorCard.style.transition = 'opacity 0.5s ease';
            }, 50);
        }
    }, 350);

    if (progressInterval) clearInterval(progressInterval);

    const submitBtn = document.getElementById('submit-btn');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="bi bi-x-circle me-2"></i> Error Occurred';
    }
}

/**
 * Shows an error message (legacy method that now uses the modal)
 * @param {string} message - The error message to display
 */
function showError(message) {
    // Handle undefined message
    if (message === undefined) {
        console.log("showError: Detected undefined error message");

        // Try to use the shader error handler first
        if (window.ShaderErrorHandler) {
            const shaderPath = document.getElementById('shader_path');
            const shaderName = shaderPath ? shaderPath.options[shaderPath.selectedIndex].text : "Unknown Shader";

            window.ShaderErrorHandler.showShaderError(
                shaderName,
                "The shader failed to render. This could be due to compatibility issues with your graphics hardware or syntax errors in the shader code."
            );
            return;
        }

        // If shader error handler is not available, use a generic error message
        message = "An error occurred while processing the shader. Please try a different shader or check the console for more details.";
    }

    // Create a simple error object for the modal
    showErrorModal({
        title: 'Error',
        message: message
    });
}

// Export functions to global scope
window.showValidationError = showValidationError;
window.getTabNameFromField = getTabNameFromField;
window.showError = showError;
window.showErrorModal = showErrorModal;
window.showErrorFallback = showErrorFallback;

// Initialize on DOM content loaded
document.addEventListener('DOMContentLoaded', function() {
    // This is now handled by the modal-manager.js module
});
