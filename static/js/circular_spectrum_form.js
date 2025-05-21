/**
 * Circular Spectrum Form JavaScript
 * Handles form submission and UI interactions for the Circular Spectrum visualizer.
 */

// Initialize processing UI controller
let processingUI;

document.addEventListener('DOMContentLoaded', function() {
    console.log("Circular Spectrum Form JS loaded");

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

    // Get form element
    const uploadForm = document.getElementById('upload-form');
    if (!uploadForm) {
        console.error("Upload form not found");
        return;
    }

    // Add event listener for background shader selection
    const backgroundShaderSelect = document.getElementById('background_shader');
    const backgroundMediaInput = document.getElementById('background_media');

    if (backgroundShaderSelect && backgroundMediaInput) {
        backgroundShaderSelect.addEventListener('change', function() {
            if (this.value) {
                // Add a note about shader taking precedence
                let existingNote = document.getElementById('shader-note');
                if (!existingNote) {
                    const note = document.createElement('div');
                    note.id = 'shader-note';
                    note.className = 'alert alert-info mt-2';
                    note.innerHTML = '<i class="bi bi-info-circle me-2"></i> The selected shader will take precedence over any background image/video.';
                    backgroundMediaInput.parentNode.appendChild(note);
                }
            } else {
                // Remove the note if no shader is selected
                const existingNote = document.getElementById('shader-note');
                if (existingNote) existingNote.remove();
            }
        });
    }

    // Handle form submission
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();

        // Disable submit button to prevent multiple submissions
        const submitBtn = document.getElementById('submit-btn');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Processing...';
        }

        // Prepare form data using the form utilities
        const formData = window.FormUtils.collectFormData(uploadForm);

        // Add file inputs
        window.FormUtils.addFileInputs(formData, ['file', 'background_media']);

        // Add background shader if selected
        const backgroundShader = document.getElementById('background_shader');
        if (backgroundShader && backgroundShader.value) {
            formData.append('background_shader_path', backgroundShader.value);
        }

        // Validate required file input
        if (!window.FormUtils.validateFileInput('file', {
            errorMessage: 'Please select an audio file to process'
        })) {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="bi bi-magic me-2"></i> Generate Visualization';
            }
            return; // Stop submission
        }

        console.log("Form data prepared, submitting...");

        // Submit the form using the shared processing UI
        processingUI.submitForm(formData);
    });

    // Handle debug mode toggle
    const debugModeCheckbox = document.getElementById('debug_mode');
    const debugLevelContainer = document.getElementById('debug_level_container');

    if (debugModeCheckbox && debugLevelContainer) {
        debugModeCheckbox.addEventListener('change', function() {
            debugLevelContainer.style.display = this.checked ? 'block' : 'none';
        });
    }

    // Update range input displays
    const rangeInputs = [
        'inner_radius', 'outer_radius', 'segment_spacing', 'bar_width',
        'sensitivity', 'border_size', 'debug_level'
    ];

    rangeInputs.forEach(function(id) {
        const input = document.getElementById(id);
        const valueDisplay = document.getElementById(id + '_value');

        if (input && valueDisplay) {
            // Update on page load
            if (id === 'segment_spacing') {
                // For segment_spacing, show as pixels
                valueDisplay.textContent = input.value + ` pixels`;
            } else {
                valueDisplay.textContent = input.value;
            }

            // Update on input change
            input.addEventListener('input', function() {
                if (id === 'segment_spacing') {
                    // For segment_spacing, show as pixels
                    valueDisplay.textContent = input.value + ` pixels`;
                } else {
                    valueDisplay.textContent = input.value;
                }
            });
        }
    });
});
