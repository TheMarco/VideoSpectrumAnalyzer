// static/js/oscilloscope_waveform_form.js

document.addEventListener('DOMContentLoaded', function() {
    console.log("Initializing Oscilloscope Waveform Form");

    // Initialize shared modules
    const processingUI = window.ProcessingUI.init();

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            delay: { show: 50, hide: 50 },
            html: true
        });
    });

    // Get form element
    const uploadForm = document.getElementById('upload-form');
    if (!uploadForm) {
        console.error("Upload form not found");
        return;
    }

    // Handle form submission
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        console.log("Form submitted");

        // Basic validation - check if audio file is selected
        const fileInput = document.getElementById('file');
        if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
            console.log("Audio file validation failed");

            // Use the error modal directly
            if (window.ModalManager && typeof window.ModalManager.showModal === 'function') {
                window.ModalManager.showModal('errorModal', {
                    title: '<i class="bi bi-exclamation-triangle-fill me-2"></i>Validation Error',
                    content: `
                        <div class="error-content">
                            <div class="error-message"><strong>Audio File</strong>: Please select an audio file</div>
                            <div class="error-description">An audio file is required to create the visualization</div>
                            <div class="error-location mt-2">
                                <span class="badge bg-secondary"><i class="bi bi-layout-text-window me-1"></i>Input Files & Info Tab</span>
                            </div>
                        </div>
                    `
                });
            } else {
                // Fallback if modal manager is not available
                alert("Please select an audio file");
            }

            // Show the input tab
            const inputTab = document.getElementById('input-tab');
            if (inputTab) {
                const tabInstance = new bootstrap.Tab(inputTab);
                tabInstance.show();
            }

            return;
        }

        // Convert numeric inputs to numbers
        const numericInputs = ['line_thickness', 'scale', 'smoothing_factor', 'glow_blur_radius', 'glow_intensity', 'fps', 'width', 'height', 'duration'];
        numericInputs.forEach(inputName => {
            const input = document.getElementById(inputName);
            if (input && input.value) {
                // Convert to appropriate type (int or float)
                if (inputName === 'scale' || inputName === 'smoothing_factor' || inputName === 'glow_intensity') {
                    input.value = parseFloat(input.value);
                } else {
                    input.value = parseInt(input.value, 10);
                }
            }
        });

        // Prepare form data using shared utilities
        const formData = new FormData(uploadForm);

        // Make sure the visualizer name is included
        if (!formData.has('visualizer_name')) {
            formData.append('visualizer_name', 'OscilloscopeWaveformVisualizer');
        }

        console.log("Form data prepared, submitting...");

        // Submit the form using the shared processing UI
        processingUI.submitForm(formData);
    });
});