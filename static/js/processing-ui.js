// --- START OF FILE processing-ui.js ---
/**
 * Shared functionality for processing UI and video playback
 * This module handles the common processing, video display, and UI transitions
 * that are shared across different visualizer types.
 */

/**
 * Initialize the processing UI functionality
 * @param {Object} options - Configuration options
 * @returns {Object} - Methods for controlling the processing UI
 */
function initProcessingUI(options = {}) {
    // Get element references
    const elements = {
        uploadForm: document.getElementById('upload-form'),
        processingCard: document.getElementById('processing-card'),
        errorCard: document.getElementById('error-card'),
        progressBar: document.getElementById('progress-bar'),
        statusMessage: document.getElementById('status-message'),
        errorMessage: document.getElementById('error-message'),
        downloadSection: document.getElementById('download-section'),
        downloadLink: document.getElementById('download-link'),
        backBtn: document.getElementById('back-btn'),
        createAnotherBtn: document.getElementById('create-another-btn'),
        configTabs: document.getElementById('configTabs'),
        configTabsContent: document.getElementById('configTabsContent'),
        processingAnimation: document.getElementById('processing-animation'),
        videoPlayerContainer: document.getElementById('video-player-container'),
        resultVideo: document.getElementById('result-video')
    };

    // State variables
    let currentJobId = null;
    let progressInterval = null;

    // Make progressInterval accessible to the shared error handling code
    window.progressInterval = progressInterval;

    // Attach event listeners
    if (elements.backBtn) {
        elements.backBtn.addEventListener('click', resetToFormState);
    }

    if (elements.createAnotherBtn) {
        elements.createAnotherBtn.addEventListener('click', resetToFormState);
    }

    /**
     * Reset the UI back to the form state with animations
     */
    function resetToFormState() {
        // Fade out error and processing cards
        if (elements.errorCard && elements.errorCard.style.display === 'block') {
            elements.errorCard.style.opacity = '0';
            elements.errorCard.style.transition = 'opacity 0.3s ease';
            setTimeout(() => { elements.errorCard.style.display = 'none'; }, 300);
        }

        if (elements.processingCard && elements.processingCard.style.display === 'block') {
            elements.processingCard.style.opacity = '0';
            elements.processingCard.style.transition = 'opacity 0.3s ease';
            setTimeout(() => { elements.processingCard.style.display = 'none'; }, 300);
        }

        // Fade in form elements
        if (elements.configTabs) {
            elements.configTabs.style.display = 'flex';
            elements.configTabs.style.opacity = '0';
            setTimeout(() => {
                elements.configTabs.style.opacity = '1';
                elements.configTabs.style.transition = 'opacity 0.5s ease';
            }, 350);
        }

        if (elements.configTabsContent) {
            elements.configTabsContent.style.display = 'block';
            elements.configTabsContent.style.opacity = '0';
            setTimeout(() => {
                elements.configTabsContent.style.opacity = '1';
                elements.configTabsContent.style.transition = 'opacity 0.5s ease';
            }, 350);

            // Activate the first tab
            const firstTab = document.querySelector('#configTabs .nav-link');
            if (firstTab) {
                const tabInstance = new bootstrap.Tab(firstTab);
                tabInstance.show();
            }
        }

        // Reset submit button
        const submitBtn = document.getElementById('submit-btn');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="bi bi-magic me-2"></i> Generate Visualization';
        }

        // Reset progress elements
        if (elements.progressBar) {
            elements.progressBar.style.width = '0%';
            elements.progressBar.textContent = '';
            elements.progressBar.classList.remove('bg-success', 'bg-danger');
            elements.progressBar.classList.add('progress-bar-animated');
        }

        if (elements.statusMessage) {
            elements.statusMessage.textContent = 'Processing your audio file...';
        }

        // Reset video player
        if (elements.resultVideo) {
            elements.resultVideo.pause();
            elements.resultVideo.removeAttribute('src');
            elements.resultVideo.load();
        }

        // Reset UI elements visibility
        if (elements.processingAnimation) {
            elements.processingAnimation.style.display = 'block';
        }
        if (elements.videoPlayerContainer) {
            elements.videoPlayerContainer.style.display = 'none';
        }
        if (elements.downloadSection) {
            elements.downloadSection.style.display = 'none';
        }

        // Reset file inputs
        const audioFileInput = document.getElementById('file');
        const backgroundMediaInput = document.getElementById('background_media');
        if (audioFileInput) audioFileInput.value = '';
        if (backgroundMediaInput) backgroundMediaInput.value = '';

        currentJobId = null;
    }

    /**
     * Show the processing UI and hide the form
     */
    function showProcessingUI() {
        // Smooth transition to processing card
        if (elements.configTabs) {
            elements.configTabs.style.opacity = '0';
            elements.configTabs.style.transition = 'opacity 0.3s ease';
            setTimeout(() => { elements.configTabs.style.display = 'none'; }, 300);
        }

        if (elements.configTabsContent) {
            elements.configTabsContent.style.opacity = '0';
            elements.configTabsContent.style.transition = 'opacity 0.3s ease';
            setTimeout(() => { elements.configTabsContent.style.display = 'none'; }, 300);
        }

        // Show processing card with animation
        if (elements.processingCard) {
            elements.processingCard.style.display = 'block';
            elements.processingCard.style.opacity = '0';
            setTimeout(() => {
                elements.processingCard.style.opacity = '1';
                elements.processingCard.style.transition = 'opacity 0.5s ease';
            }, 50);
        }

        if (elements.errorCard) {
            elements.errorCard.style.display = 'none';
        }
        if (elements.downloadSection) {
            elements.downloadSection.style.display = 'none';
        }
        if (elements.progressBar) {
            elements.progressBar.style.width = '0%';
            elements.progressBar.textContent = '';
            elements.progressBar.classList.remove('bg-success', 'bg-danger');
            elements.progressBar.classList.add('progress-bar-animated');
        }
        if (elements.statusMessage) {
            elements.statusMessage.textContent = 'Uploading files...';
        }

        // Reset video player
        if (elements.resultVideo) {
            elements.resultVideo.pause();
            elements.resultVideo.removeAttribute('src');
            elements.resultVideo.load();
        }

        // Reset UI elements visibility
        if (elements.processingAnimation) {
            elements.processingAnimation.style.display = 'block';
        }
        if (elements.videoPlayerContainer) {
            elements.videoPlayerContainer.style.display = 'none';
        }
    }

    /**
     * Start polling for job progress
     * @param {string} jobId - The ID of the job to poll
     */
    function startProgressPolling(jobId) {
        currentJobId = jobId;

        if (progressInterval) {
            clearInterval(progressInterval);
        }

        progressInterval = setInterval(() => {
            fetch(`/job_status/${jobId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        showError(data.error);
                        clearInterval(progressInterval);
                        return;
                    }
                    updateProgress(data);
                    if (data.status === 'completed' || data.status === 'failed') {
                        clearInterval(progressInterval);
                    }
                })
                .catch(error => {
                    showError('Error polling job status: ' + error.message);
                    clearInterval(progressInterval);
                });
        }, 500); // Poll more frequently (every 500ms instead of 1500ms)

        // Update global reference
        window.progressInterval = progressInterval;
    }

    /**
     * Update the progress UI based on job status
     * @param {Object} data - The job status data
     */
    function updateProgress(data) {
        if (!elements.progressBar) return;

        const progress = Math.min(100, Math.max(0, data.progress || 0));
        elements.progressBar.style.width = `${progress}%`;
        elements.progressBar.textContent = `${progress}%`;
        elements.progressBar.setAttribute('aria-valuenow', progress);

        if (data.status === 'queued' && elements.statusMessage) {
            elements.statusMessage.textContent = 'Waiting in queue...';
        }
        else if (data.status === 'processing' && elements.statusMessage) {
            if (data.message) {
                console.log("DEBUG: Received message from server:", data.message);
                elements.statusMessage.textContent = data.message;
            } else {
                elements.statusMessage.textContent = `Processing: ${progress}% complete`;
            }
        }
        else if (data.status === 'completed') {
            if (elements.statusMessage) {
                elements.statusMessage.textContent = 'Processing complete!';
            }

            // Hide processing animation
            if (elements.processingAnimation) {
                elements.processingAnimation.style.display = 'none';
            }

            // Show video player
            if (elements.videoPlayerContainer && elements.resultVideo) {
                elements.videoPlayerContainer.style.display = 'block';
                elements.resultVideo.src = `/stream/${currentJobId}`;
                elements.resultVideo.load();
                elements.resultVideo.play().catch(e => console.log('Auto-play prevented:', e));
            }

            // Show download section
            if (elements.downloadSection) {
                elements.downloadSection.style.display = 'block';
            }
            if (elements.downloadLink) {
                elements.downloadLink.href = `/download/${currentJobId}`;
            }

            // Update progress bar
            if (elements.progressBar) {
                elements.progressBar.classList.remove('progress-bar-animated');
                elements.progressBar.classList.add('bg-success');
            }

            // Update submit button
            const submitBtn = document.getElementById('submit-btn');
            if (submitBtn) {
                submitBtn.textContent = 'Completed!';
                submitBtn.disabled = true;
            }
        } else if (data.status === 'failed') {
            showError(data.error || 'An unknown error occurred during processing.');
            if (elements.progressBar) {
                elements.progressBar.classList.remove('progress-bar-animated');
                elements.progressBar.classList.add('bg-danger');
            }
            if (elements.statusMessage) {
                elements.statusMessage.textContent = 'Processing Failed';
            }
        }
    }

    /**
     * Show an error message
     * @param {string} message - The error message to display
     */
    function showError(message) {
        // Use the shared error handling function if available
        if (typeof window.showErrorModal === 'function') {
            window.showErrorModal(message);
            return;
        }

        // Fallback to basic error display
        console.error("Error:", message);

        if (elements.errorMessage) {
            elements.errorMessage.textContent = message;
        }

        if (elements.errorCard) {
            elements.errorCard.style.display = 'block';
        }

        if (elements.processingCard && elements.processingCard.style.display === 'block') {
            elements.processingCard.style.display = 'none';
        }

        if (progressInterval) {
            clearInterval(progressInterval);
        }
    }

    /**
     * Handle form submission
     * @param {FormData} formData - The form data to submit
     */
    function submitForm(formData) {
        showProcessingUI();

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(({ status, body }) => {
            if (status >= 400 || body.error) {
                showError(body.error || `Server error: ${status}`);
                return;
            }
            if (elements.statusMessage) {
                elements.statusMessage.textContent = 'Upload complete. Starting processing...';
            }
            startProgressPolling(body.job_id);
        })
        .catch(error => {
            showError('An error occurred during upload: ' + error.message);
        });
    }

    // Return public methods
    return {
        resetToFormState,
        showProcessingUI,
        startProgressPolling,
        updateProgress,
        submitForm,
        showError,
        getCurrentJobId: () => currentJobId
    };
}

// Export the module
window.ProcessingUI = {
    init: initProcessingUI
};
// --- END OF FILE processing-ui.js ---
