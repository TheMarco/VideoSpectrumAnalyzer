/**
 * Smooth Curves Form JS
 * This module provides form handling for the Smooth Curves visualizer
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Smooth Curves form script loaded');

    // Get form elements
    const fillEnabledSelect = document.getElementById('fill_enabled');
    const fillOpacityInput = document.getElementById('fill_opacity');

    // Add event listener for fill enabled selection
    if (fillEnabledSelect && fillOpacityInput) {
        fillEnabledSelect.addEventListener('change', function() {
            // Enable/disable fill opacity input based on fill enabled selection
            fillOpacityInput.disabled = (fillEnabledSelect.value === 'false');
        });
    }

    // Get text-related form elements
    const showTextSelect = document.getElementById('show_text');
    const textSizeSelect = document.getElementById('text_size');
    const textColorInput = document.getElementById('text_color');
    const glowEffectSelect = document.getElementById('glow_effect');

    // Add event listener for show text selection
    if (showTextSelect && textSizeSelect && textColorInput && glowEffectSelect) {
        showTextSelect.addEventListener('change', function() {
            // Enable/disable text-related inputs based on show text selection
            const showText = (showTextSelect.value === 'true');
            textSizeSelect.disabled = !showText;
            textColorInput.disabled = !showText;
            glowEffectSelect.disabled = !showText;
        });
    }

    // Initialize form validation
    const form = document.getElementById('upload-form');
    if (form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault();

            // Validate form
            if (!form.checkValidity()) {
                event.stopPropagation();
                form.classList.add('was-validated');
                return;
            }

            // Additional validation for audio file
            const audioFile = document.getElementById('file').files[0];
            if (!audioFile) {
                // Show error using the global function if available
                if (typeof window.showErrorModal === 'function') {
                    window.showErrorModal({
                        title: 'Validation Error',
                        message: 'Please select an audio file.'
                    });
                } else {
                    alert('Please select an audio file.');
                }
                return;
            }

            // Show loading indicator
            const submitButton = form.querySelector('button[type="submit"]');
            const originalButtonText = submitButton.innerHTML;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Generating...';
            submitButton.disabled = true;

            // Collect form data
            const formData = window.FormUtils.collectFormData(form);

            // Add file inputs - note that the server expects "file" for the audio file
            // We already have audioFile from the validation check above
            if (audioFile) {
                formData.append('file', audioFile);
                console.log('Appending audio file as "file":', audioFile.name);
            }

            // Add background media file - server expects "background_media" for background files
            const backgroundMedia = document.getElementById('background_media').files[0];
            if (backgroundMedia) {
                formData.append('background_media', backgroundMedia);
                console.log('Appending background media as "background_media":', backgroundMedia.name);
            }

            // Submit form data
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    // Show error message using the correct function
                    if (typeof window.showErrorModal === 'function') {
                        window.showErrorModal({
                            title: 'Error',
                            message: data.error
                        });
                    } else {
                        console.error('Error:', data.error);
                        alert('Error: ' + data.error);
                    }

                    // Reset submit button
                    submitButton.innerHTML = originalButtonText;
                    submitButton.disabled = false;
                } else if (data.job_id) {
                    // Redirect to job status page
                    window.location.href = `/job/${data.job_id}`;
                }
            })
            .catch(error => {
                console.error('Error:', error);

                // Show error message using the correct function
                if (typeof window.showErrorModal === 'function') {
                    window.showErrorModal({
                        title: 'Error',
                        message: 'An error occurred while submitting the form. Please try again.'
                    });
                } else {
                    alert('Error: An error occurred while submitting the form. Please try again.');
                }

                // Reset submit button
                submitButton.innerHTML = originalButtonText;
                submitButton.disabled = false;
            });
        });
    }
});
