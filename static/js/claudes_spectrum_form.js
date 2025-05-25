// Claude's Spectrum Form JavaScript
// Handles form interactions, range sliders, and color scheme changes

document.addEventListener('DOMContentLoaded', function() {
    console.log('Claude\'s Spectrum form loaded');

    // Initialize range sliders with value display
    const rangeInputs = document.querySelectorAll('input[type="range"]');
    rangeInputs.forEach(input => {
        const valueSpan = document.getElementById(input.id + '_value');
        if (valueSpan) {
            // Set initial value
            valueSpan.textContent = input.value;

            // Update value on change
            input.addEventListener('input', function() {
                valueSpan.textContent = this.value;
            });
        }
    });

    // Handle color scheme changes
    const colorSchemeSelect = document.getElementById('color_scheme');
    const colorControls = document.getElementById('color-controls');
    const singleColorControl = document.getElementById('single-color-control');
    const lowColorControl = document.getElementById('low-color-control');
    const midColorControl = document.getElementById('mid-color-control');
    const highColorControl = document.getElementById('high-color-control');

    function updateColorControls() {
        const scheme = parseInt(colorSchemeSelect.value);

        // Hide all color controls first
        singleColorControl.style.display = 'none';
        lowColorControl.style.display = 'none';
        midColorControl.style.display = 'none';
        highColorControl.style.display = 'none';

        // Show relevant controls based on scheme
        if (scheme === 0) { // Gradient (Red-Yellow-Blue)
            lowColorControl.style.display = 'block';
            midColorControl.style.display = 'block';
            highColorControl.style.display = 'block';
        } else if (scheme === 1) { // Single Color
            singleColorControl.style.display = 'block';
        }
        // For schemes 2-5 (Rainbow, Purple, Green, Blue), no color controls needed
    }

    if (colorSchemeSelect) {
        // Set initial state
        updateColorControls();

        // Update on change
        colorSchemeSelect.addEventListener('change', updateColorControls);
    }

    // Handle center line checkbox
    const showCenterLineCheckbox = document.getElementById('show_center_line');
    const centerLineControls = document.querySelectorAll('#center_line_thickness, #center_line_overhang, #center_line_color');

    function updateCenterLineControls() {
        const isEnabled = showCenterLineCheckbox.checked;
        centerLineControls.forEach(control => {
            control.disabled = !isEnabled;
            control.parentElement.style.opacity = isEnabled ? '1' : '0.5';
        });
    }

    if (showCenterLineCheckbox) {
        // Set initial state
        updateCenterLineControls();

        // Update on change
        showCenterLineCheckbox.addEventListener('change', updateCenterLineControls);
    }

    // Handle logarithmic scale checkbox
    const useLogScaleCheckbox = document.getElementById('use_logarithmic_scale');
    const logScaleFactorControl = document.getElementById('log_scale_factor');

    function updateLogScaleControls() {
        const isEnabled = useLogScaleCheckbox.checked;
        logScaleFactorControl.disabled = !isEnabled;
        logScaleFactorControl.parentElement.style.opacity = isEnabled ? '1' : '0.5';
    }

    if (useLogScaleCheckbox && logScaleFactorControl) {
        // Set initial state
        updateLogScaleControls();

        // Update on change
        useLogScaleCheckbox.addEventListener('change', updateLogScaleControls);
    }

    // Initialize the shared processing UI
    const processingUI = window.ProcessingUI.init();

    // Form submission handling
    const form = document.getElementById('upload-form');

    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            // Validate required fields
            const fileInput = document.getElementById('file');
            if (!fileInput.files.length) {
                alert('Please select an audio file.');
                return;
            }

            // Use the shared form utilities to collect form data
            const formData = window.FormUtils.collectFormData(form);

            // Add file inputs using the shared utility
            window.FormUtils.addFileInputs(formData, ['file', 'background_media']);

            // Make sure the visualizer name is included
            if (!formData.has('visualizer_name')) {
                formData.append('visualizer_name', 'ClaudesSpectrumVisualizer');
            }

            // Debug: Log all form data
            console.log('Form data being sent:');
            for (let [key, value] of formData.entries()) {
                console.log(key, value);
            }

            // Use the shared processing UI to submit the form
            processingUI.submitForm(formData);
        });
    }

    // The shared processing UI handles progress polling, error handling, and button events

    // Handle video resolution dropdown
    const heightSelect = document.getElementById('height');
    const widthInput = document.getElementById('width');

    if (heightSelect && widthInput) {
        // Set initial width based on default height selection
        const initialHeight = heightSelect.value;
        switch(initialHeight) {
            case '480':
                widthInput.value = 854;
                break;
            case '720':
                widthInput.value = 1280;
                break;
            case '1080':
                widthInput.value = 1920;
                break;
            case '1440':
                widthInput.value = 2560;
                break;
            case '2160':
                widthInput.value = 3840;
                break;
        }

        heightSelect.addEventListener('change', function() {
            // Set width based on selected resolution
            switch(this.value) {
                case '480':
                    widthInput.value = 854;
                    break;
                case '720':
                    widthInput.value = 1280;
                    break;
                case '1080':
                    widthInput.value = 1920;
                    break;
                case '1440':
                    widthInput.value = 2560;
                    break;
                case '2160':
                    widthInput.value = 3840;
                    break;
            }
        });
    }

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    console.log('Claude\'s Spectrum form initialization complete');
});
