/**
 * Circular Audio Visualizer Form Handler
 */

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('upload-form');

    if (!form) {
        console.error('Circular Audio form not found');
        return;
    }

    // Initialize the shared processing UI
    const processingUI = window.ProcessingUI.init();

    // Initialize range input displays
    initializeRangeInputs();

    // Form submission handler
    form.addEventListener('submit', function(e) {
        e.preventDefault();

        if (validateForm()) {
            submitForm(processingUI);
        }
    });

    function initializeRangeInputs() {
        const rangeInputs = form.querySelectorAll('input[type="range"]');

        rangeInputs.forEach(input => {
            const updateDisplay = () => {
                // Look for the value span with the pattern: input_id + "_value"
                const valueSpan = document.getElementById(input.id + '_value');
                if (valueSpan) {
                    valueSpan.textContent = input.value;
                }
            };

            // Update display on input
            input.addEventListener('input', updateDisplay);

            // Initialize display
            updateDisplay();
        });
    }

    function validateForm() {
        // Clear previous validation states
        form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));

        let isValid = true;

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
            return false;
        }

        // Validate file size (1.6GB limit)
        const maxSize = 1.6 * 1024 * 1024 * 1024; // 1.6GB in bytes
        if (audioFile.size > maxSize) {
            if (typeof window.showErrorModal === 'function') {
                window.showErrorModal({
                    title: 'File Too Large',
                    message: 'Audio file must be smaller than 1.6GB.'
                });
            } else {
                alert('Audio file must be smaller than 1.6GB.');
            }
            return false;
        }

        return isValid;
    }

    function submitForm(processingUI) {
        // Use the shared form utilities to collect form data
        const formData = window.FormUtils.collectFormData(form);

        // Add file inputs using the shared utility
        window.FormUtils.addFileInputs(formData, ['file', 'background_media']);

        // Add background shader if selected
        const backgroundShader = document.getElementById('background_shader');
        if (backgroundShader && backgroundShader.value) {
            formData.append('background_shader_path', backgroundShader.value);
        }

        // Make sure the visualizer name is included
        if (!formData.has('visualizer_name')) {
            formData.append('visualizer_name', 'CircularAudioVisualizer');
        }

        // Debug: Log all form data
        console.log('Form data being sent:');
        for (let [key, value] of formData.entries()) {
            console.log(key, value);
        }

        // Use the shared processing UI to submit the form
        processingUI.submitForm(formData);
    }

    // Fallback progress polling function (in case shared function isn't available)
    function pollProgress(jobId) {
        function updateProgress() {
            fetch(`/progress/${jobId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'completed') {
                        // Success - redirect to result
                        setTimeout(() => {
                            window.location.href = `/result/${jobId}`;
                        }, 1000);
                    } else if (data.status === 'failed') {
                        // Error occurred
                        if (typeof window.showErrorModal === 'function') {
                            window.showErrorModal({
                                title: 'Processing Error',
                                message: data.error || 'An error occurred during processing.'
                            });
                        } else {
                            alert('Processing error: ' + (data.error || 'An error occurred during processing.'));
                        }
                    } else {
                        // Continue polling
                        setTimeout(updateProgress, 1000);
                    }
                })
                .catch(error => {
                    console.error('Progress polling error:', error);
                    // Continue polling on error (server might be temporarily unavailable)
                    setTimeout(updateProgress, 2000);
                });
        }

        // Start polling
        updateProgress();
    }

    console.log('Circular Audio form handler initialized');
});
