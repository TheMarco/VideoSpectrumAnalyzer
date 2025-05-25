/**
 * Audioreactive Shader Form JavaScript
 * Handles form submission and UI interactions for the Audioreactive Shader visualizer.
 */

// Initialize processing UI controller
let processingUI;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    if (typeof initTooltips === 'function') {
        initTooltips();
    }

    // Initialize form validation
    if (typeof initFormValidation === 'function') {
        initFormValidation();
    }

    // Initialize processing UI
    if (window.ProcessingUI) {
        processingUI = window.ProcessingUI.init();
    }

    // Initialize form submission
    const form = document.getElementById('upload-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            // Validate form
            if (!validateForm(form)) {
                return;
            }

            // Get form data
            const formData = new FormData(form);

            // Submit form using the shared processing UI
            if (processingUI) {
                processingUI.submitForm(formData);
            } else {
                // Fallback to basic form submission
                submitFormBasic(form);
            }
        });
    }
});

/**
 * Validate the form.
 *
 * @param {HTMLFormElement} form - The form to validate
 * @returns {boolean} - Whether the form is valid
 */
function validateForm(form) {
    // Check if audio file is selected
    const audioFile = form.querySelector('#file');
    if (!audioFile || !audioFile.files || audioFile.files.length === 0) {
        if (processingUI) {
            processingUI.showError('Please select an audio file.');
        } else {
            showErrorBasic('Please select an audio file.');
        }
        return false;
    }

    // Check if shader is selected
    const shader = form.querySelector('#shader_path');
    if (!shader || !shader.value) {
        if (processingUI) {
            processingUI.showError('Please select a shader.');
        } else {
            showErrorBasic('Please select a shader.');
        }
        return false;
    }

    return true;
}



/**
 * Basic form submission function as a fallback.
 *
 * @param {HTMLFormElement} form - The form to submit
 */
function submitFormBasic(form) {
    // Basic UI update
    form.style.display = 'none';
    const processingCard = document.getElementById('processing-card');
    if (processingCard) {
        processingCard.style.display = 'block';
    }

    // Get form data
    const formData = new FormData(form);

    // Submit form using fetch API
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showErrorBasic(data.error);
            return;
        }

        // Start polling for job status
        const jobId = data.job_id;
        const statusUrl = '/job_status/' + jobId;

        // Set up polling interval
        const pollInterval = setInterval(function() {
            fetch(statusUrl)
                .then(response => response.json())
                .then(statusData => {
                    // Update progress
                    const progressBar = document.getElementById('progress-bar');
                    const statusMessage = document.getElementById('status-message');

                    if (progressBar) {
                        progressBar.style.width = statusData.progress + '%';
                        progressBar.textContent = statusData.progress + '%';
                    }

                    if (statusMessage && statusData.message) {
                        statusMessage.textContent = statusData.message;
                    }

                    // Check if processing is complete
                    if (statusData.status === 'completed') {
                        clearInterval(pollInterval);

                        // Show video player
                        const videoPlayerContainer = document.getElementById('video-player-container');
                        const resultVideo = document.getElementById('result-video');

                        if (videoPlayerContainer && resultVideo) {
                            resultVideo.src = '/stream/' + jobId;
                            videoPlayerContainer.style.display = 'block';
                        }

                        // Show download section
                        const downloadSection = document.getElementById('download-section');
                        const downloadLink = document.getElementById('download-link');

                        if (downloadSection && downloadLink) {
                            downloadLink.href = '/download/' + jobId;
                            downloadSection.style.display = 'block';
                        }
                    } else if (statusData.status === 'failed') {
                        clearInterval(pollInterval);

                        // Check if this is a shader error
                        if (statusData.error_type === 'shader_error' ||
                            (statusData.error && (statusData.error.includes('shader') || statusData.error.includes('.glsl')))) {

                            console.log("Detected shader error - redirecting to error page");

                            // Get shader name
                            let shaderName = "Unknown Shader";
                            if (statusData.shader_name) {
                                shaderName = statusData.shader_name;
                            } else if (statusData.shader_path) {
                                const pathParts = statusData.shader_path.split('/');
                                shaderName = pathParts[pathParts.length - 1];
                            } else if (statusData.error) {
                                const match = statusData.error.match(/shader ['"]([^'"]+)['"]/i);
                                if (match && match[1]) {
                                    shaderName = match[1];
                                }
                            }

                            // Get error message
                            const errorMessage = statusData.error ||
                                "The shader failed to render. This could be due to compatibility issues with your graphics hardware or syntax errors in the shader code.";

                            // Redirect to the shader error page
                            window.location.href = `/shader_error?shader_name=${encodeURIComponent(shaderName)}&error_details=${encodeURIComponent(errorMessage)}`;
                            return;
                        } else {
                            // Fall back to basic error display for non-shader errors
                            showErrorBasic(statusData.error || 'An error occurred during processing.');
                        }
                    }
                })
                .catch(error => {
                    console.error('Error polling job status:', error);
                });
        }, 1000);
    })
    .catch(error => {
        showErrorBasic('An error occurred while submitting the form: ' + error.message);
    });
}

/**
 * Show an error message (basic fallback version).
 *
 * @param {string} message - The error message to show
 */
function showErrorBasic(message) {
    // Hide processing card
    const processingCard = document.getElementById('processing-card');
    if (processingCard) {
        processingCard.style.display = 'none';
    }

    // Show error card
    const errorCard = document.getElementById('error-card');
    const errorMessage = document.getElementById('error-message');

    if (errorCard && errorMessage) {
        errorMessage.textContent = message;
        errorCard.style.display = 'block';
    } else {
        // Fallback to alert
        alert('Error: ' + message);
    }
}
