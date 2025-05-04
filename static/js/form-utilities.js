// --- START OF FILE form-utilities.js ---
/**
 * Form utilities
 * This module provides common form handling functions
 */

/**
 * Collect form data from a form element
 * @param {HTMLFormElement} formElement - The form element to collect data from
 * @returns {FormData|null} - The collected form data or null if form not found
 */
function collectFormData(formElement) {
    if (!formElement) return null;
    
    const formData = new FormData();
    const formElements = formElement.elements;
    
    // Add regular form fields
    for (let i = 0; i < formElements.length; i++) {
        const element = formElements[i];
        if (element.name && element.type !== 'file' && element.type !== 'submit' && element.type !== 'radio') {
            if (element.type === 'checkbox') {
                formData.append(element.name, element.checked ? 'on' : 'off');
            } else {
                formData.append(element.name, element.value);
            }
        }
    }
    
    return formData;
}

/**
 * Add file inputs to form data
 * @param {FormData} formData - The FormData object to add files to
 * @param {Array<string>} fileInputIds - Array of file input IDs to add
 * @returns {FormData} - The updated FormData object
 */
function addFileInputs(formData, fileInputIds) {
    if (!formData) return formData;
    
    fileInputIds.forEach(inputId => {
        const fileInput = document.getElementById(inputId);
        if (fileInput && fileInput.files.length > 0) {
            formData.append(fileInput.name || inputId, fileInput.files[0]);
            console.log(`Added file: ${fileInput.files[0].name}`);
        } else {
            console.log(`No file selected for ${inputId}`);
        }
    });
    
    return formData;
}

/**
 * Reset form inputs
 * @param {HTMLFormElement} formElement - The form element to reset
 */
function resetFormInputs(formElement) {
    if (!formElement) return;
    
    // Reset all inputs
    Array.from(formElement.elements).forEach(element => {
        if (element.type === 'file') {
            element.value = '';
        } else if (element.type === 'checkbox' || element.type === 'radio') {
            element.checked = element.defaultChecked;
        } else if (element.type !== 'submit' && element.type !== 'button') {
            element.value = element.defaultValue;
        }
        
        // Clear validation styling
        element.classList.remove('is-invalid', 'is-valid');
    });
}

/**
 * Check if a file input has a file selected
 * @param {string} inputId - The ID of the file input
 * @param {Object} [options] - Options
 * @param {string} [options.errorMessage] - Custom error message
 * @returns {boolean} - True if file is selected, false otherwise
 */
function validateFileInput(inputId, options = {}) {
    const fileInput = document.getElementById(inputId);
    if (!fileInput || fileInput.files.length === 0) {
        if (typeof window.showValidationError === 'function') {
            window.showValidationError({
                field: fileInput,
                friendlyName: fileInput ? (fileInput.dataset.friendlyName || "File") : "File",
                tabName: fileInput ? (fileInput.dataset.tabName || getTabNameFromField(fileInput) || "Input") : "Input",
                message: options.errorMessage || "Please select a file",
                description: fileInput ? (fileInput.dataset.description || "") : ""
            });
        } else if (typeof window.showError === 'function') {
            window.showError(options.errorMessage || "Please select a file");
        }
        return false;
    }
    return true;
}

/**
 * Get the tab name from a field element
 * @param {HTMLElement} field - The field element
 * @returns {string} - The tab name or "Unknown Tab"
 */
function getTabNameFromField(field) {
    if (!field) return "Unknown Tab";
    
    const tabPane = field.closest('.tab-pane');
    if (!tabPane || !tabPane.id) return "Unknown Tab";
    
    const tabButton = document.querySelector(`[data-bs-target="#${tabPane.id}"]`);
    if (!tabButton) return "Unknown Tab";
    
    return tabButton.textContent.trim();
}

// Export the module
window.FormUtils = {
    collectFormData: collectFormData,
    addFileInputs: addFileInputs,
    resetFormInputs: resetFormInputs,
    validateFileInput: validateFileInput,
    getTabNameFromField: getTabNameFromField
};
// --- END OF FILE form-utilities.js ---
