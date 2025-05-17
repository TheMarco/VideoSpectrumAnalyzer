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
    console.log(`Initializing modal: ${modalId}`);
    const modal = document.getElementById(modalId);
    if (!modal) {
        console.error(`Modal element not found: ${modalId}`);
        return null;
    }

    // Clean up any existing modal instances
    try {
        const existingModal = bootstrap.Modal.getInstance(modal);
        if (existingModal) {
            console.log(`Disposing existing modal instance for ${modalId}`);
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

    try {
        console.log(`Creating new Bootstrap modal instance for ${modalId}`);
        return new bootstrap.Modal(modal);
    } catch (e) {
        console.error(`Error creating Bootstrap modal for ${modalId}:`, e);
        return null;
    }
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
    console.log(`Showing modal: ${modalId} with options:`, options);

    try {
        const modal = initModal(modalId);
        if (!modal) {
            console.error(`Failed to initialize modal: ${modalId}`);
            return null;
        }

        const modalElement = document.getElementById(modalId);

        // Set title if provided
        if (options.title) {
            const titleElement = modalElement.querySelector('.modal-title');
            if (titleElement) {
                console.log(`Setting modal title: ${options.title}`);
                titleElement.innerHTML = options.title;
            } else {
                console.warn(`Modal title element not found in ${modalId}`);
            }
        }

        // Set body content if provided
        if (options.content) {
            const bodyElement = modalElement.querySelector('.modal-body');
            if (bodyElement) {
                console.log(`Setting modal body content (length: ${options.content.length})`);
                bodyElement.innerHTML = options.content;
            } else {
                console.warn(`Modal body element not found in ${modalId}`);
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
        console.log(`Calling modal.show() for ${modalId}`);
        modal.show();

        // Verify the modal is visible
        setTimeout(() => {
            if (modalElement.classList.contains('show') && modalElement.style.display !== 'none') {
                console.log(`Modal ${modalId} is now visible`);
            } else {
                console.warn(`Modal ${modalId} may not be visible. classList:`, modalElement.classList, 'style.display:', modalElement.style.display);
            }
        }, 300);

        return modal;
    } catch (error) {
        console.error(`Error showing modal ${modalId}:`, error);
        return null;
    }
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
    console.log("DOM loaded - initializing modals");
    const errorModal = document.getElementById('errorModal');

    if (errorModal) {
        console.log("Error modal found in DOM");

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

        // Test that Bootstrap is available
        if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
            console.log("Bootstrap Modal is available");
        } else {
            console.error("Bootstrap Modal is not available! This will cause errors when showing modals.");
        }

        // Verify modal structure
        const modalTitle = errorModal.querySelector('.modal-title');
        const modalBody = errorModal.querySelector('.modal-body');
        const modalFooter = errorModal.querySelector('.modal-footer');

        console.log("Modal structure check:", {
            "title": !!modalTitle,
            "body": !!modalBody,
            "footer": !!modalFooter
        });
    } else {
        console.error("Error modal not found in DOM! This will cause errors when showing error messages.");
    }
});

// Export the module
window.ModalManager = {
    initModal: initModal,
    showModal: showModal,
    hideModal: hideModal
};
// --- END OF FILE modal-manager.js ---
