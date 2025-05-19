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

    // Add event listener for original settings selection
    const useStandardSettingsSelect = document.getElementById('use_standard_settings');
    const customColorContainer = document.getElementById('custom_color_container');
    const scaleInput = document.getElementById('scale');
    const thicknessScaleInput = document.getElementById('thickness_scale');
    const smoothingFactorInput = document.getElementById('smoothing_factor');

    if (useStandardSettingsSelect) {
        // Store original values when switching to custom
        let originalValues = {};

        // Standard settings values
        const standardSettings = {
            'line_color': '#ffffe5',
            'line_thickness': 10,
            'scale': 4.0,
            'thickness_scale': 0.1,
            'smoothing_factor': 0.8,
            'persistence': 0.7,
            'vertical_offset': -1.5,
            'waveform_update_rate': 15
        };

        // Function to toggle custom settings visibility and reset values
        const toggleCustomSettingsVisibility = () => {
            const useStandard = useStandardSettingsSelect.value === 'true';

            // Get all form inputs that should be affected
            const lineColorInput = document.getElementById('line_color');
            const lineThicknessInput = document.getElementById('line_thickness');
            const scaleInput = document.getElementById('scale');
            const thicknessScaleInput = document.getElementById('thickness_scale');
            const smoothingFactorInput = document.getElementById('smoothing_factor');
            const persistenceInput = document.getElementById('persistence');
            const waveformUpdateRateInput = document.getElementById('waveform_update_rate');
            const verticalOffsetInput = document.getElementById('vertical_offset');

            const customInputs = [
                customColorContainer,
                lineThicknessInput,
                scaleInput,
                thicknessScaleInput,
                smoothingFactorInput,
                persistenceInput,
                waveformUpdateRateInput,
                verticalOffsetInput
            ];

            const formInputs = {
                'line_color': lineColorInput,
                'line_thickness': lineThicknessInput,
                'scale': scaleInput,
                'thickness_scale': thicknessScaleInput,
                'smoothing_factor': smoothingFactorInput,
                'persistence': persistenceInput,
                'vertical_offset': verticalOffsetInput,
                'waveform_update_rate': waveformUpdateRateInput
            };

            if (useStandard) {
                // Switching to standard settings

                // Store current custom values before resetting
                Object.keys(formInputs).forEach(key => {
                    if (formInputs[key]) {
                        originalValues[key] = formInputs[key].value;
                    }
                });

                // Reset form fields to standard values
                Object.keys(standardSettings).forEach(key => {
                    if (formInputs[key]) {
                        // Special handling for color picker
                        if (key === 'line_color') {
                            // Update the color picker value
                            formInputs[key].value = standardSettings[key];

                            // If there's a color preview element, update it too
                            const colorPreview = formInputs[key].parentElement.querySelector('.color-preview');
                            if (colorPreview) {
                                colorPreview.style.backgroundColor = standardSettings[key];
                            }
                        } else {
                            formInputs[key].value = standardSettings[key];
                        }
                    }
                });

                // Disable inputs
                customInputs.forEach(input => {
                    if (input) {
                        input.style.opacity = '0.5';
                        input.style.pointerEvents = 'none';
                    }
                });
            } else {
                // Switching to custom settings

                // Restore original values if they exist
                if (Object.keys(originalValues).length > 0) {
                    Object.keys(originalValues).forEach(key => {
                        if (formInputs[key]) {
                            // Special handling for color picker
                            if (key === 'line_color') {
                                // Update the color picker value
                                formInputs[key].value = originalValues[key];

                                // If there's a color preview element, update it too
                                const colorPreview = formInputs[key].parentElement.querySelector('.color-preview');
                                if (colorPreview) {
                                    colorPreview.style.backgroundColor = originalValues[key];
                                }
                            } else {
                                formInputs[key].value = originalValues[key];
                            }
                        }
                    });
                }

                // Enable inputs
                customInputs.forEach(input => {
                    if (input) {
                        input.style.opacity = '1';
                        input.style.pointerEvents = 'auto';
                    }
                });
            }
        };

        // Set initial state - force reset to standard values if standard is selected
        if (useStandardSettingsSelect.value === 'true') {
            // Initialize with standard settings
            const lineColorInput = document.getElementById('line_color');
            const lineThicknessInput = document.getElementById('line_thickness');
            const scaleInput = document.getElementById('scale');
            const thicknessScaleInput = document.getElementById('thickness_scale');
            const smoothingFactorInput = document.getElementById('smoothing_factor');
            const persistenceInput = document.getElementById('persistence');
            const waveformUpdateRateInput = document.getElementById('waveform_update_rate');
            const verticalOffsetInput = document.getElementById('vertical_offset');

            const formInputs = {
                'line_color': lineColorInput,
                'line_thickness': lineThicknessInput,
                'scale': scaleInput,
                'thickness_scale': thicknessScaleInput,
                'smoothing_factor': smoothingFactorInput,
                'persistence': persistenceInput,
                'vertical_offset': verticalOffsetInput,
                'waveform_update_rate': waveformUpdateRateInput
            };

            // Set form fields to standard values
            Object.keys(standardSettings).forEach(key => {
                if (formInputs[key]) {
                    formInputs[key].value = standardSettings[key];
                }
            });
        }

        // Apply visibility settings
        toggleCustomSettingsVisibility();

        // Add event listener
        useStandardSettingsSelect.addEventListener('change', toggleCustomSettingsVisibility);
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

    // Add event listener for text glow effect selection
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

        // Prepare form data using shared utilities
        const formData = new FormData(uploadForm);

        // Convert numeric inputs to numbers
        const numericInputs = ['line_thickness', 'scale', 'thickness_scale', 'smoothing_factor', 'persistence', 'vertical_offset', 'waveform_update_rate', 'glow_blur_radius', 'glow_intensity', 'fps', 'width', 'height', 'duration'];
        numericInputs.forEach(inputName => {
            const input = document.getElementById(inputName);
            if (input && input.value) {
                // Convert to appropriate type (int or float)
                if (inputName === 'scale' || inputName === 'thickness_scale' || inputName === 'smoothing_factor' ||
                   inputName === 'persistence' || inputName === 'glow_intensity' || inputName === 'vertical_offset') {
                    formData.set(inputName, parseFloat(input.value));
                } else if (inputName === 'waveform_update_rate') {
                    // Ensure waveform_update_rate is an integer
                    formData.set(inputName, parseInt(input.value, 10));
                } else {
                    formData.set(inputName, parseInt(input.value, 10));
                }
            }
        });

        // Convert boolean inputs
        const booleanInputs = ['use_standard_settings'];
        booleanInputs.forEach(inputName => {
            const input = document.getElementById(inputName);
            if (input && input.value) {
                // Convert string 'true'/'false' to actual boolean
                const boolValue = input.value === 'true';
                // Replace the value in the form data
                formData.set(inputName, boolValue);
            }
        });

        // For backward compatibility, also set use_original_settings to the same value
        const useStandardInput = document.getElementById('use_standard_settings');
        if (useStandardInput && useStandardInput.value) {
            const boolValue = useStandardInput.value === 'true';
            formData.set('use_original_settings', boolValue);
        }

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
