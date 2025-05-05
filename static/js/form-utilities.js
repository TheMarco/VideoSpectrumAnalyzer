// --- START OF FILE form-utilities.js ---
/**
 * Form utilities
 * This module provides common form handling functions
 */

/**
 * Collect all form data from a form element
 * @param {HTMLFormElement} form - The form element
 * @returns {FormData} - The collected form data
 */
function collectFormData(form) {
    const formData = new FormData();
    
    // Get all form elements
    const formElements = form.elements;
    
    // Loop through form elements and add to FormData
    for (let i = 0; i < formElements.length; i++) {
        const element = formElements[i];
        
        // Skip file inputs (they're handled separately)
        if (element.type === 'file') continue;
        
        // Skip buttons
        if (element.type === 'button' || element.type === 'submit' || element.type === 'reset') continue;
        
        // Handle checkboxes
        if (element.type === 'checkbox') {
            formData.append(element.name, element.checked);
            continue;
        }
        
        // Handle radio buttons
        if (element.type === 'radio') {
            if (element.checked) {
                formData.append(element.name, element.value);
            }
            continue;
        }
        
        // Handle select elements
        if (element.tagName.toLowerCase() === 'select') {
            formData.append(element.name, element.value);
            continue;
        }
        
        // Handle all other inputs
        if (element.name) {
            formData.append(element.name, element.value);
        }
    }
    
    return formData;
}

/**
 * Add file inputs to FormData
 * @param {FormData} formData - The FormData object
 * @param {Array} fileInputIds - Array of file input IDs to add
 */
function addFileInputs(formData, fileInputIds) {
    fileInputIds.forEach(id => {
        const fileInput = document.getElementById(id);
        if (fileInput && fileInput.files.length > 0) {
            formData.append(id, fileInput.files[0]);
            console.log(`Appending ${id}:`, fileInput.files[0].name);
        } else {
            console.log(`No file selected for ${id}.`);
        }
    });
    
    // Add background shader path if it exists
    const backgroundShader = document.getElementById('background_shader');
    if (backgroundShader && backgroundShader.value) {
        formData.append('background_shader_path', backgroundShader.value);
        console.log("Appending background shader path:", backgroundShader.value);
    }
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
