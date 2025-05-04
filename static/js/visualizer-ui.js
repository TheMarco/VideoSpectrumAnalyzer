// Visualizer-specific UI handling

document.addEventListener('DOMContentLoaded', function() {
    // Get the visualizer name from the hidden input
    const visualizerNameInput = document.querySelector('input[name="visualizer_name"]');
    if (!visualizerNameInput) return;

    const visualizerName = visualizerNameInput.value;

    // Elements that should be shown/hidden based on visualizer type
    const segmentElements = {
        maxSegmentsRow: document.querySelector('#max_segments').closest('.col-md-3'),
        segmentHeightRow: document.querySelector('#segment_height').closest('.col-md-3'),
        segmentGapRow: document.querySelector('#segment_gap').closest('.col-md-3'),
        alwaysOnBottomRow: document.querySelector('#always_on_bottom').closest('.col-md-3')
    };

    const maxAmplitudeRow = document.querySelector('#max_amplitude').closest('.row');

    // Function to update UI based on visualizer type
    function updateVisualizerUI() {
        if (visualizerName === "Dual Bar Visualizer") {
            // Hide segment-related elements for Dual Bar Visualizer
            for (const key in segmentElements) {
                if (segmentElements[key]) {
                    segmentElements[key].style.display = 'none';
                }
            }

            // Show max amplitude for Dual Bar Visualizer
            if (maxAmplitudeRow) {
                maxAmplitudeRow.style.display = 'flex';
            }

            // Update labels and descriptions for Dual Bar Visualizer
            updateDualBarLabels();

            // Set default values for Dual Bar Visualizer
            setDualBarDefaults();
        } else {
            // Show segment-related elements for other visualizers
            for (const key in segmentElements) {
                if (segmentElements[key]) {
                    segmentElements[key].style.display = '';
                }
            }

            // Hide max amplitude for other visualizers
            if (maxAmplitudeRow) {
                maxAmplitudeRow.style.display = 'none';
            }
        }
    }

    // Function to update labels and descriptions for Dual Bar Visualizer
    function updateDualBarLabels() {
        // Update n_bars label
        const nBarsLabel = document.querySelector('label[for="n_bars"]');
        if (nBarsLabel) {
            nBarsLabel.innerHTML = 'Number of Bars <i class="bi bi-question-circle help-icon" data-bs-toggle="tooltip" data-bs-placement="top" title="Number of bars in the visualizer. More bars show more frequency detail but may be slower."></i>';
        }

        // Update bar_width label
        const barWidthLabel = document.querySelector('label[for="bar_width"]');
        if (barWidthLabel) {
            barWidthLabel.innerHTML = 'Bar Width (px) <i class="bi bi-question-circle help-icon" data-bs-toggle="tooltip" data-bs-placement="top" title="Width of each bar in pixels."></i>';
        }

        // Update bar_gap label
        const barGapLabel = document.querySelector('label[for="bar_gap"]');
        if (barGapLabel) {
            barGapLabel.innerHTML = 'Bar Gap (px) <i class="bi bi-question-circle help-icon" data-bs-toggle="tooltip" data-bs-placement="top" title="Gap between bars in pixels."></i>';
        }

        // Update corner_radius label
        const cornerRadiusLabel = document.querySelector('label[for="corner_radius"]');
        if (cornerRadiusLabel) {
            cornerRadiusLabel.innerHTML = 'Corner Radius (px) <i class="bi bi-question-circle help-icon" data-bs-toggle="tooltip" data-bs-placement="top" title="Rounded corner radius for bars. Set to 0 for sharp corners."></i>';
        }

        // Reinitialize tooltips
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    }

    // Function to set default values for Dual Bar Visualizer
    function setDualBarDefaults() {
        // Always set defaults for Dual Bar Visualizer

        // Set default values
        const nBarsInput = document.querySelector('#n_bars');
        if (nBarsInput) {
            nBarsInput.value = '60';
        }

        const barWidthInput = document.querySelector('#bar_width');
        if (barWidthInput) {
            barWidthInput.value = '5';
        }

        const barGapInput = document.querySelector('#bar_gap');
        if (barGapInput) {
            barGapInput.value = '5';
        }

        const maxAmplitudeInput = document.querySelector('#max_amplitude');
        if (maxAmplitudeInput) {
            maxAmplitudeInput.value = '250';
        }

        const cornerRadiusInput = document.querySelector('#corner_radius');
        if (cornerRadiusInput) {
            cornerRadiusInput.value = '0';
        }

        // Set decay speed for faster response
        const decaySpeedInput = document.querySelector('#decay_speed');
        if (decaySpeedInput) {
            decaySpeedInput.value = '0.4';
        }

        // Set peak hold frames
        const peakHoldFramesInput = document.querySelector('#peak_hold_frames');
        if (peakHoldFramesInput) {
            peakHoldFramesInput.value = '3';
        }

        // Set peak decay speed
        const peakDecaySpeedInput = document.querySelector('#peak_decay_speed');
        if (peakDecaySpeedInput) {
            peakDecaySpeedInput.value = '0.25';
        }

        // Set silence decay factor
        const silenceDecayFactorInput = document.querySelector('#silence_decay_factor');
        if (silenceDecayFactorInput) {
            silenceDecayFactorInput.value = '0.7';
        }
    }

    // Run on page load
    updateVisualizerUI();
});
