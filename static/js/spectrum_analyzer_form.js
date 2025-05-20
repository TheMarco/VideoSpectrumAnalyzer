// --- START OF FILE spectrum_analyzer_form.js ---

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the shared processing UI module
    const processingUI = window.ProcessingUI.init();

    // Get form element
    const uploadForm = document.getElementById('upload-form');

    // Handle blur radius slider value display
    const blurRadiusSlider = document.getElementById('glow_blur_radius');
    const blurRadiusValue = document.getElementById('glow_blur_radius_value');

    if (blurRadiusSlider && blurRadiusValue) {
        // Update the value display when the slider changes
        blurRadiusSlider.addEventListener('input', function() {
            blurRadiusValue.textContent = this.value;
        });
    }

    // Add event listener for background shader selection
    const backgroundShaderSelect = document.getElementById('background_shader');
    const backgroundMediaInput = document.getElementById('background_media');

    if (backgroundShaderSelect && backgroundMediaInput) {
        backgroundShaderSelect.addEventListener('change', function() {
            if (this.value) {
                // If a shader is selected, show a note about precedence
                if (backgroundMediaInput.value) {
                    const note = document.createElement('small');
                    note.id = 'shader-note';
                    note.className = 'form-text text-warning';
                    note.innerHTML = '<i class="bi bi-info-circle"></i> The selected shader will take precedence over the background image/video.';

                    // Remove existing note if any
                    const existingNote = document.getElementById('shader-note');
                    if (existingNote) existingNote.remove();

                    // Add the note after the background media input
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

        // Submit the form using the shared processing UI
        processingUI.submitForm(formData);
    });

    // Function to validate the form
    function validateForm() {
        console.log("%c VALIDATING FORM", "background: #ff0000; color: white; font-size: 16px;");

        const audioFileInput = document.getElementById('file');
        if (!audioFileInput || audioFileInput.files.length === 0) {
            showValidationError({
                field: audioFileInput,
                friendlyName: "Audio File",
                tabName: "Input Files & Info",
                message: "Please select an audio file to process",
                description: "The primary audio track for your visualization"
            });
            return false;
        }

        // Get all form fields
        const fields = Array.from(uploadForm.elements).filter(el =>
            el.tagName === 'INPUT' ||
            el.tagName === 'SELECT' ||
            el.tagName === 'TEXTAREA'
        );

        console.log("Found fields:", fields.length);

        // Validate each field manually
        for (const field of fields) {
            console.log("Checking field:", field.name, field.type, field.value);

            // Skip fields that don't need validation
            if (field.type === 'hidden' || field.type === 'submit' || !field.name) {
                continue;
            }

            // Get field metadata for better error messages
            const friendlyName = field.dataset.friendlyName || field.name;
            const tabName = field.dataset.tabName || getTabNameFromField(field);
            const description = field.dataset.description || "";

            // Check number inputs
            if (field.type === 'number' || field.type === 'range') {
                const value = parseFloat(field.value);

                // Check if it's a valid number
                if (isNaN(value)) {
                    showValidationError({
                        field: field,
                        friendlyName: friendlyName,
                        tabName: tabName,
                        message: `Please enter a valid number`,
                        description: description
                    });
                    return false;
                }

                // Check min constraint
                if (field.hasAttribute('min') && value < parseFloat(field.getAttribute('min'))) {
                    console.log("MIN VALUE ERROR:", field.name, value, field.getAttribute('min'));
                    showValidationError({
                        field: field,
                        friendlyName: friendlyName,
                        tabName: tabName,
                        message: `Value must be at least ${field.getAttribute('min')}`,
                        description: description
                    });
                    return false;
                }

                // Check max constraint
                if (field.hasAttribute('max') && value > parseFloat(field.getAttribute('max'))) {
                    console.log("MAX VALUE ERROR:", field.name, value, field.getAttribute('max'));
                    showValidationError({
                        field: field,
                        friendlyName: friendlyName,
                        tabName: tabName,
                        message: `Value must be at most ${field.getAttribute('max')}`,
                        description: description
                    });
                    return false;
                }

                // Check step constraint if specified
                if (field.hasAttribute('step') && field.getAttribute('step') !== 'any') {
                    const step = parseFloat(field.getAttribute('step'));
                    const min = field.hasAttribute('min') ? parseFloat(field.getAttribute('min')) : 0;

                    // Check if the value is a valid step from the min value
                    const remainder = Math.abs((value - min) % step);
                    if (remainder > 0.00001 && remainder < step - 0.00001) { // Using small epsilon for floating point comparison
                        showValidationError({
                            field: field,
                            friendlyName: friendlyName,
                            tabName: tabName,
                            message: `Value must be in steps of ${step} from ${min}`,
                            description: description
                        });
                        return false;
                    }
                }
            }

            // Check required fields
            if (field.required && !field.value.trim()) {
                showValidationError({
                    field: field,
                    friendlyName: friendlyName,
                    tabName: tabName,
                    message: `This field is required`,
                    description: description
                });
                return false;
            }
        }

        console.log("All validation passed!");
        return true;
    }

    // Update the file input to clear validation styling when a file is selected
    const audioFileInput = document.getElementById('file');
    if (audioFileInput) {
        audioFileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                this.classList.remove('is-invalid');
            }
        });
    }

    // Clear tab errors when switching tabs
    document.querySelectorAll('#configTabs .nav-link').forEach(tab => {
        tab.addEventListener('shown.bs.tab', function() {
            window.TabNavigation.clearTabErrors();
        });
    });
});
// --- END OF FILE spectrum_analyzer_form.js ---
