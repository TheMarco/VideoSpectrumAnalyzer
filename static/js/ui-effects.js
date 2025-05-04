// --- START OF FILE ui-effects.js ---
/**
 * Shared UI animations and effects
 * This module provides common UI animations and effects used across the application
 */

// Initialize UI effects
function initUIEffects() {
    // Add fade-in animation to cards
    document.querySelectorAll('.card').forEach(card => {
        card.classList.add('fade-in');
    });

    // Add subtle hover effects to form controls
    document.querySelectorAll('.form-control, .form-select').forEach(input => {
        input.addEventListener('focus', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.transition = 'all 0.3s ease';
        });

        input.addEventListener('blur', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

/**
 * Fade in/out element with callback
 * @param {HTMLElement} element - The element to fade
 * @param {boolean} show - Whether to show (true) or hide (false) the element
 * @param {number} duration - Duration of the animation in milliseconds
 * @param {number} delay - Delay before starting the animation in milliseconds
 * @returns {Promise} - Resolves when the animation is complete
 */
function fadeElement(element, show, duration = 300, delay = 0) {
    if (!element) return Promise.resolve();
    
    return new Promise(resolve => {
        if (show) {
            element.style.display = 'block';
            element.style.opacity = '0';
            setTimeout(() => {
                element.style.opacity = '1';
                element.style.transition = `opacity ${duration/1000}s ease`;
                setTimeout(resolve, duration);
            }, delay);
        } else {
            element.style.opacity = '0';
            element.style.transition = `opacity ${duration/1000}s ease`;
            setTimeout(() => { 
                element.style.display = 'none';
                resolve();
            }, duration + delay);
        }
    });
}

/**
 * Smoothly transition between elements
 * @param {HTMLElement} hideElement - Element to hide
 * @param {HTMLElement} showElement - Element to show
 * @param {number} duration - Duration of each transition in milliseconds
 */
function transitionElements(hideElement, showElement, duration = 300) {
    if (hideElement) {
        hideElement.style.opacity = '0';
        hideElement.style.transition = `opacity ${duration/1000}s ease`;
        setTimeout(() => { 
            hideElement.style.display = 'none';
            
            if (showElement) {
                showElement.style.display = 'block';
                showElement.style.opacity = '0';
                setTimeout(() => {
                    showElement.style.opacity = '1';
                    showElement.style.transition = `opacity ${duration/1000}s ease`;
                }, 50);
            }
        }, duration);
    } else if (showElement) {
        showElement.style.display = 'block';
        showElement.style.opacity = '0';
        setTimeout(() => {
            showElement.style.opacity = '1';
            showElement.style.transition = `opacity ${duration/1000}s ease`;
        }, 50);
    }
}

// Export the module
window.UIEffects = {
    init: initUIEffects,
    fadeElement: fadeElement,
    transitionElements: transitionElements
};

// Initialize on DOM content loaded
document.addEventListener('DOMContentLoaded', initUIEffects);
// --- END OF FILE ui-effects.js ---
