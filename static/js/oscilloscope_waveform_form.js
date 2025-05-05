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

    // Add event listener for background shader selection
    const backgroundShaderSelect = document.getElementById('background_shader');
    const backgroundMediaInput = document.getElementById('background_media');

    if (backgroundShaderSelect && backgroundMediaInput) {
        backgroundShaderSelect.addEventListener('change', function() {
            if (this.value) {
                // If a shader is selected, show a note about precedence
                const note = document.createElement('small');
                note.id = 'shader-note';
                note.className = 'form-text text-warning';
                note.innerHTML = '<i class="bi bi-info-circle"></i> The selected shader will take precedence over the background image/video.';
                
                // Remove existing note if any
                const existingNote = document.getElementById('shader-note');
                if (existingNote) existingNote.remove();
                
                // Add the note after the background media input
                backgroundMediaInput.parentNode.appendChild(note);
                
                // Optionally, you can visually indicate that the media input is less important
                backgroundMediaInput.classList.add('opacity-50');
            } else {
                // Remove the note if no shader is selected
                const existingNote = document.getElementById('shader-note');
                if (existingNote) existingNote.remove();
                
                // Remove visual indication
                backgroundMediaInput.classList.remove('opacity-50');
            }
        });
    }

    // Add event listener for glow effect selection
    const glowEffectSelect = document.getElementById('glow_effect');
    const glowSettings = document.querySelectorAll('.glow-setting');

    if (glowEffectSelect && glowSettings.length > 0) {
        glowEffectSelect.addEventListener('change', function() {
            if (this.value === 'off') {
                // Hide glow settings if glow is off
                glowSettings.forEach(setting => {
                    setting.style.display = 'none';
                });
            } else {
                // Show glow settings if glow is on
                glowSettings.forEach(setting => {
                    setting.style.display = 'flex';
                });
            }
        });
        
        // Trigger the change event to set initial state
        glowEffectSelect.dispatchEvent(new Event('change'));
    }

    // Add event listener for resolution selection
    const resolutionSelect = document.getElementById('resolution');
    const widthInput = document.getElementById('width');
    const heightInput = document.getElementById('height');

    if (resolutionSelect && widthInput && heightInput) {
        resolutionSelect.addEventListener('change', function() {
            // Set width and height based on selected resolution
            switch(this.value) {
                case '720p':
                    widthInput.value = 1280;
                    heightInput.value = 720;
                    break;
                case '1080p':
                    widthInput.value = 1920;
                    heightInput.value = 1080;
                    break;
                case '1440p':
                    widthInput.value = 2560;
                    heightInput.value = 1440;
                    break;
                case '4K':
                    widthInput.value = 3840;
                    heightInput.value = 2160;
                    break;
            }
        });
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

        // Add background shader path if selected
        const backgroundShader = document.getElementById('background_shader');
        if (backgroundShader && backgroundShader.value) {
            formData.append('background_shader_path', backgroundShader.value);
        }

        console.log("Form data prepared, submitting...");

        // Submit the form using the shared processing UI
        processingUI.submitForm(formData);
    });
});
