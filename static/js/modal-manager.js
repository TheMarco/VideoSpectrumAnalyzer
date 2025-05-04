// --- START OF FILE modal-manager.js ---
/**
 * Modal management utilities
 * This module provides functions for managing modals across the application
 */

/**
 * Initialize a modal properly
 * @param {string} modalId - The ID of the modal element
 * @returns {bootstrap.Modal|null} - The Bootstrap modal instance or null if not found
 */
function initModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return null;
    
    // Clean up any existing modal instances
    try {
        const existingModal = bootstrap.Modal.getInstance(modal);
        if (existingModal) {
            existingModal.dispose();
        }
    } catch (e) {
        console.error(`Error disposing modal ${modalId}:`, e);
    }
    
    // Remove any existing backdrops
    document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
        backdrop.parentNode.removeChild(backdrop);
    });
    
    // Reset modal state
    modal.style.display = 'none';
    modal.classList.remove('show');
    document.body.classList.remove('modal-open');
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';
    
    return new bootstrap.Modal(modal);
}

/**
 * Show a modal with content
 * @param {string} modalId - The ID of the modal element
 * @param {Object} options - Options for the modal
 * @param {string} [options.title] - The title of the modal
 * @param {string} [options.content] - The content of the modal body
 * @param {Function} [options.onShow] - Callback when the modal is shown
 * @param {Function} [options.onHide] - Callback when the modal is hidden
 * @returns {bootstrap.Modal|null} - The Bootstrap modal instance or null if not found
 */
function showModal(modalId, options = {}) {
    const modal = initModal(modalId);
    if (!modal) return null;
    
    const modalElement = document.getElementById(modalId);
    
    // Set title if provided
    if (options.title) {
        const titleElement = modalElement.querySelector('.modal-title');
        if (titleElement) {
            titleElement.innerHTML = options.title;
        }
    }
    
    // Set body content if provided
    if (options.content) {
        const bodyElement = modalElement.querySelector('.modal-body');
        if (bodyElement) {
            bodyElement.innerHTML = options.content;
        }
    }
    
    // Add event listeners if callbacks provided
    if (options.onShow) {
        modalElement.addEventListener('shown.bs.modal', options.onShow, { once: true });
    }
    
    if (options.onHide) {
        modalElement.addEventListener('hidden.bs.modal', options.onHide, { once: true });
    }
    
    // Show the modal
    modal.show();
    
    return modal;
}

/**
 * Hide a modal
 * @param {string} modalId - The ID of the modal element
 */
function hideModal(modalId) {
    try {
        const modalElement = document.getElementById(modalId);
        if (!modalElement) return;
        
        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) {
            modal.hide();
        }
    } catch (e) {
        console.error(`Error hiding modal ${modalId}:`, e);
    }
}

// Initialize error modal on page load
document.addEventListener('DOMContentLoaded', function() {
    const errorModal = document.getElementById('errorModal');
    if (errorModal) {
        // Make sure the error modal is hidden on page load
        errorModal.style.display = 'none';
        errorModal.classList.remove('show');

        // Remove any existing backdrops
        document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
            backdrop.parentNode.removeChild(backdrop);
        });

        // Remove modal-open class from body
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
        
        // Add event listeners to close buttons
        const closeButtons = errorModal.querySelectorAll('#closeModalBtn, #closeModalXBtn, .btn-close');
        closeButtons.forEach(button => {
            button.addEventListener('click', () => hideModal('errorModal'));
        });
    }
});

// Export the module
window.ModalManager = {
    initModal: initModal,
    showModal: showModal,
    hideModal: hideModal
};
// --- END OF FILE modal-manager.js ---
