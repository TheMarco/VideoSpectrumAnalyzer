// --- START OF FILE main.js ---

document.addEventListener('DOMContentLoaded', function() {
    console.log("%c DOM LOADED - SCRIPT STARTING", "background: #ff00ff; color: white; font-size: 16px; padding: 5px;");
    // Element references - using optional chaining to prevent null reference errors
    const uploadForm = document.getElementById('upload-form');
    console.log("%c FORM FOUND:", "background: #0000ff; color: white;", uploadForm ? "YES" : "NO");

    const processingCard = document.getElementById('processing-card');
    const errorCard = document.getElementById('error-card');
    const progressBar = document.getElementById('progress-bar');
    const statusMessage = document.getElementById('status-message');
    const errorMessage = document.getElementById('error-message');
    const downloadSection = document.getElementById('download-section');
    const downloadLink = document.getElementById('download-link');
    const backBtn = document.getElementById('back-btn');
    const createAnotherBtn = document.getElementById('create-another-btn');
    const configTabs = document.getElementById('configTabs');
    const configTabsContent = document.getElementById('configTabsContent');

    // Add fade-in animation to cards
    document.querySelectorAll('.card').forEach(card => {
        card.classList.add('fade-in');
    });

    // Add subtle hover effects to form controls
    document.querySelectorAll('.form-control, .form-select').forEach(input => {
        input.addEventListener('focus', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.transition = 'all 0.3s ease';
        });

        input.addEventListener('blur', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    let currentJobId = null;
    let progressInterval = null;

    // Function to reset the UI back to the form state with animations
    function resetToFormState() {
        // Fade out error and processing cards
        if (errorCard && errorCard.style.display === 'block') {
            errorCard.style.opacity = '0';
            errorCard.style.transition = 'opacity 0.3s ease';
            setTimeout(() => { errorCard.style.display = 'none'; }, 300);
        }

        if (processingCard && processingCard.style.display === 'block') {
            processingCard.style.opacity = '0';
            processingCard.style.transition = 'opacity 0.3s ease';
            setTimeout(() => { processingCard.style.display = 'none'; }, 300);
        }

        // Fade in form elements
        if (configTabs) {
            configTabs.style.display = 'flex';
            configTabs.style.opacity = '0';
            setTimeout(() => {
                configTabs.style.opacity = '1';
                configTabs.style.transition = 'opacity 0.5s ease';
            }, 350);
        }

        if (configTabsContent) {
            configTabsContent.style.display = 'block';
            configTabsContent.style.opacity = '0';
            setTimeout(() => {
                configTabsContent.style.opacity = '1';
                configTabsContent.style.transition = 'opacity 0.5s ease';
            }, 350);
        }

        // Reset submit button
        const submitBtn = document.getElementById('submit-btn');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="bi bi-magic me-2"></i> Generate Visualization';
        }

        // Reset progress elements
        if (progressBar) {
            progressBar.style.width = '0%';
            progressBar.textContent = '';
            progressBar.classList.remove('bg-success', 'bg-danger');
            progressBar.classList.add('progress-bar-animated');
        }

        if (statusMessage) statusMessage.textContent = 'Processing your audio file...';

        // Reset file inputs
        const audioFileInput = document.getElementById('file');
        const backgroundMediaInput = document.getElementById('background_media');
        if (audioFileInput) audioFileInput.value = '';
        if (backgroundMediaInput) backgroundMediaInput.value = '';

        // Clear any error indicators on tabs
        clearErrorIndicators();

        currentJobId = null;
    }


    // Handle form submission - only if the form exists
    if (uploadForm) {
        console.log("%c SETTING UP FORM VALIDATION", "background: #ff00ff; color: white; font-size: 14px;");
        // Function to manually validate a field
        function validateField(field) {
            console.log("VALIDATING FIELD:", field.name, field.type, field.value);

            // Skip fields that don't need validation
            if (field.type === 'hidden' || field.type === 'submit' || !field.name) {
                return true;
            }

            // Check required attribute
            if (field.required && !field.value.trim()) {
                console.log("FIELD REQUIRED ERROR:", field.name);
                return {
                    valid: false,
                    message: 'This field is required'
                };
            }

            // Check min/max for number inputs
            if (field.type === 'number' || field.type === 'range') {
                const value = parseFloat(field.value);

                // Check if it's a valid number
                if (isNaN(value)) {
                    return {
                        valid: false,
                        message: 'Please enter a valid number'
                    };
                }

                // Check min constraint
                if (field.hasAttribute('min') && value < parseFloat(field.getAttribute('min'))) {
                    console.log("MIN VALUE ERROR:", field.name, value, field.getAttribute('min'));
                    return {
                        valid: false,
                        message: `Value must be at least ${field.getAttribute('min')}`
                    };
                }

                // Check max constraint
                if (field.hasAttribute('max') && value > parseFloat(field.getAttribute('max'))) {
                    console.log("MAX VALUE ERROR:", field.name, value, field.getAttribute('max'));
                    return {
                        valid: false,
                        message: `Value must be at most ${field.getAttribute('max')}`
                    };
                }

                // Check step constraint if specified
                if (field.hasAttribute('step') && field.getAttribute('step') !== 'any') {
                    const step = parseFloat(field.getAttribute('step'));
                    const min = field.hasAttribute('min') ? parseFloat(field.getAttribute('min')) : 0;

                    // Check if the value is a valid step from the min value
                    const remainder = Math.abs((value - min) % step);
                    if (remainder > 0.00001 && remainder < step - 0.00001) { // Using small epsilon for floating point comparison
                        return {
                            valid: false,
                            message: `Value must be in steps of ${step} from ${min}`
                        };
                    }
                }
            }

            // Check pattern
            if (field.hasAttribute('pattern') && field.value) {
                const regex = new RegExp(field.getAttribute('pattern'));
                if (!regex.test(field.value)) {
                    console.log("PATTERN ERROR:", field.name, field.getAttribute('pattern'));
                    return {
                        valid: false,
                        message: field.title || 'Please match the requested format'
                    };
                }
            }

            // Check specific field validations based on name
            if (field.name === 'n_bars') {
                const value = parseInt(field.value);
                if (value < 10 || value > 100) {
                    return {
                        valid: false,
                        message: 'Number of bars must be between 10 and 100'
                    };
                }
            } else if (field.name === 'bar_width') {
                const value = parseInt(field.value);
                if (value < 5 || value > 100) {
                    return {
                        valid: false,
                        message: 'Bar width must be between 5 and 100 pixels'
                    };
                }
            }

            // If we get here, the field is valid
            return true;
        }

        // Function to show a validation error message
        function showValidationError(field, message) {
            // Get field name
            const fieldName = field.name || 'This field';
            const friendlyFieldName = fieldName
                .replace(/_/g, ' ')
                .replace(/\b\w/g, l => l.toUpperCase());

            // Find which tab contains this field
            const tabPane = field.closest('.tab-pane');
            if (tabPane) {
                // Get the tab ID and corresponding tab button
                const tabId = tabPane.id;
                const tabButton = document.querySelector(`[data-bs-target="#${tabId}"]`);

                if (tabButton) {
                    // Activate the tab containing the invalid field
                    const tab = new bootstrap.Tab(tabButton);
                    tab.show();

                    // Focus the field
                    setTimeout(() => {
                        field.focus();
                        field.scrollIntoView({ behavior: 'smooth', block: 'center' });

                        // Add visual highlight
                        field.classList.add('highlight-error');
                        setTimeout(() => field.classList.remove('highlight-error'), 2000);
                    }, 100);
                }
            }

            // Create notification
            const notification = document.createElement('div');
            notification.className = 'validation-notification';
            notification.innerHTML = `
                <div class="validation-notification-content">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    <div>
                        <strong>${friendlyFieldName}:</strong> ${message}
                    </div>
                </div>
            `;
            document.body.appendChild(notification);

            // Remove after 5 seconds
            setTimeout(() => {
                notification.classList.add('fade-out');
                setTimeout(() => notification.remove(), 500);
            }, 5000);
        }

        // Add a submit event listener
        uploadForm.addEventListener('submit', function(e) {
            console.log("%c FORM SUBMIT EVENT TRIGGERED", "background: #ff0000; color: white; font-size: 16px; padding: 5px;");

            // Always prevent the default submission
            e.preventDefault();

            // Get all form fields
            const fields = Array.from(uploadForm.elements).filter(el =>
                el.tagName === 'INPUT' ||
                el.tagName === 'SELECT' ||
                el.tagName === 'TEXTAREA'
            );

            console.log("%c FOUND FIELDS: " + fields.length, "background: #0000ff; color: white; font-size: 14px;");

            // Log all fields for debugging
            fields.forEach(field => {
                console.log(`Field: ${field.name}, Type: ${field.type}, Value: ${field.value}`);
                if (field.type === 'number' || field.type === 'range') {
                    console.log(`  Min: ${field.getAttribute('min')}, Max: ${field.getAttribute('max')}, Step: ${field.getAttribute('step')}`);
                }
            });

            // DEBUG: Test validation on a specific field
            const testField = document.getElementById('n_bars');
            if (testField) {
                console.log("%c TESTING VALIDATION ON n_bars", "background: #ff00ff; color: white;");
                console.log("Original value:", testField.value);

                // Test with invalid value
                const originalValue = testField.value;
                testField.value = "5"; // Below min of 10
                const testResult = validateField(testField);
                console.log("Test validation with value 5:", testResult);

                // Restore original value
                testField.value = originalValue;
            }

            // Validate each field manually
            let hasValidationErrors = false;

            for (const field of fields) {
                console.log("%c CHECKING FIELD: " + field.name, "background: #00aa00; color: white;");
                const result = validateField(field);
                console.log("VALIDATION RESULT:", field.name, result);

                if (result !== true) {
                    // Field is invalid
                    console.log("%c FIELD IS INVALID: " + field.name + " - " + result.message, "background: #ff0000; color: white; font-weight: bold;");
                    showValidationError(field, result.message);
                    hasValidationErrors = true;
                    break;
                }
            }

            if (hasValidationErrors) {
                console.log("%c VALIDATION FAILED - STOPPING SUBMISSION", "background: #ff0000; color: white; font-size: 16px;");
                return false;
            }

            console.log("%c ALL FIELDS PASSED VALIDATION", "background: #00aa00; color: white; font-size: 16px;");

            // If we get here, all fields passed our manual validation
            // Now proceed with our custom validation
            if (!validateForm()) {
                console.log("%c CUSTOM VALIDATION FAILED", "background: #ff0000; color: white; font-size: 16px;");
                return false;
            }

            console.log("%c FORM SUBMISSION PROCEEDING", "background: #00aa00; color: white; font-size: 16px;");

            // If all validation passes, continue with form processing
            const submitBtn = document.getElementById('submit-btn');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="bi bi-arrow-repeat spin me-2"></i> Processing...';
            }

            // Smooth transition to processing card
            if (configTabs) {
                configTabs.style.opacity = '0';
                configTabs.style.transition = 'opacity 0.3s ease';
                setTimeout(() => { configTabs.style.display = 'none'; }, 300);
            }

            if (configTabsContent) {
                configTabsContent.style.opacity = '0';
                configTabsContent.style.transition = 'opacity 0.3s ease';
                setTimeout(() => { configTabsContent.style.display = 'none'; }, 300);
            }

            // Show processing card with animation
            if (processingCard) {
                processingCard.style.display = 'block';
                processingCard.style.opacity = '0';
                setTimeout(() => {
                    processingCard.style.opacity = '1';
                    processingCard.style.transition = 'opacity 0.5s ease';
                }, 50);
            }

            if (errorCard) errorCard.style.display = 'none';
            if (downloadSection) downloadSection.style.display = 'none';

            if (progressBar) {
                progressBar.style.width = '0%';
                progressBar.textContent = '';
                progressBar.classList.remove('bg-success', 'bg-danger');
                progressBar.classList.add('progress-bar-animated');
            }

            if (statusMessage) statusMessage.textContent = 'Uploading files...';

            const formData = new FormData();
            const formElements = uploadForm.elements;
            for (let i = 0; i < formElements.length; i++) {
                const element = formElements[i];
                if (element.name && element.type !== 'file' && element.type !== 'submit' && element.type !== 'radio') {
                    if (element.type === 'checkbox') {
                        formData.append(element.name, element.checked ? 'on' : 'off');
                    } else {
                        formData.append(element.name, element.value);
                    }
                }
            }

            const audioFileInput = document.getElementById('file');
            if (audioFileInput && audioFileInput.files.length > 0) {
                formData.append('file', audioFileInput.files[0]);
            } else {
                showError('Please select an audio file.');
                return; // Stop submission
            }

            const backgroundMediaInput = document.getElementById('background_media');
            if (backgroundMediaInput && backgroundMediaInput.files.length > 0) {
                formData.append('background_media', backgroundMediaInput.files[0]);
                console.log("Appending background media:", backgroundMediaInput.files[0].name);
            } else {
                console.log("No background media selected.");
            }

            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json().then(data => ({ status: response.status, body: data })))
            .then(({ status, body }) => {
                if (status >= 400 || body.error) {
                    showError(body.error || `Server error: ${status}`);
                    return;
                }
                currentJobId = body.job_id;
                if (statusMessage) statusMessage.textContent = 'Upload complete. Starting processing...';
                startProgressPolling(currentJobId);
            })
            .catch(error => {
                showError('An error occurred during upload: ' + error.message);
            });
        });
    }

    // Function to validate the form (simplified to just check for audio file)
    function validateForm() {
        const audioFileInput = document.getElementById('file');
        if (!audioFileInput || audioFileInput.files.length === 0) {
            showError('Please select an audio file.');
            return false;
        }
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

    // Add input event listeners to all form fields to clear validation styling
    if (uploadForm) {
        const formFields = uploadForm.querySelectorAll('input, select, textarea');
        formFields.forEach(field => {
            field.addEventListener('input', function() {
                // Remove invalid styling when user starts typing
                this.classList.remove('is-invalid');

                // Remove any validation alerts
                const alerts = document.querySelectorAll('.validation-alert');
                alerts.forEach(alert => {
                    alert.style.opacity = '0';
                    setTimeout(() => alert.remove(), 500);
                });
            });
        });
    }

    // Function to clear all error indicators
    function clearErrorIndicators() {
        const indicators = document.querySelectorAll('.error-indicator');
        indicators.forEach(indicator => indicator.remove());
    }

    // Back button (from error card) - Calls resetToFormState (Unchanged)
    if (backBtn) {
        backBtn.addEventListener('click', resetToFormState);
    }

    // Create Another Button - Calls resetToFormState (Unchanged)
    if (createAnotherBtn) {
        createAnotherBtn.addEventListener('click', resetToFormState);
    }

    // Poll for job progress (Unchanged)
    function startProgressPolling(jobId) {
        if (progressInterval) clearInterval(progressInterval);
        progressInterval = setInterval(() => {
            fetch(`/job_status/${jobId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        showError(data.error);
                        clearInterval(progressInterval);
                        return;
                    }
                    updateProgress(data);
                    if (data.status === 'completed' || data.status === 'failed') {
                        clearInterval(progressInterval);
                    }
                })
                .catch(error => {
                    showError('Error polling job status: ' + error.message);
                    clearInterval(progressInterval);
                 });
        }, 1500);
    }

    // Update progress UI
    function updateProgress(data) {
        if (!progressBar || !statusMessage) return;

        const progress = Math.min(100, Math.max(0, data.progress || 0));
        progressBar.style.width = `${progress}%`;
        progressBar.textContent = `${progress}%`;
        progressBar.setAttribute('aria-valuenow', progress);

        if (data.status === 'queued') statusMessage.textContent = 'Waiting in queue...';
        else if (data.status === 'processing') statusMessage.textContent = `Processing: ${progress}% complete`;
        else if (data.status === 'completed') {
            statusMessage.textContent = 'Processing complete!';
            if (downloadSection) downloadSection.style.display = 'block';
            if (downloadLink) downloadLink.href = `/download/${currentJobId}`;
            progressBar.classList.remove('progress-bar-animated');
            progressBar.classList.add('bg-success');
            const submitBtn = document.getElementById('submit-btn');
            if (submitBtn) {
                submitBtn.textContent = 'Completed!';
                submitBtn.disabled = true;
            }
        } else if (data.status === 'failed') {
            showError(data.error || 'An unknown error occurred during processing.');
            progressBar.classList.remove('progress-bar-animated');
            progressBar.classList.add('bg-danger');
            statusMessage.textContent = 'Processing Failed';
        }
    }

    // Show error message with animations
    function showError(message) {
        console.error("Error displayed:", message);

        // Fade out other elements
        if (configTabs) {
            configTabs.style.opacity = '0';
            configTabs.style.transition = 'opacity 0.3s ease';
            setTimeout(() => { configTabs.style.display = 'none'; }, 300);
        }

        if (configTabsContent) {
            configTabsContent.style.opacity = '0';
            configTabsContent.style.transition = 'opacity 0.3s ease';
            setTimeout(() => { configTabsContent.style.display = 'none'; }, 300);
        }

        if (processingCard && processingCard.style.display === 'block') {
            processingCard.style.opacity = '0';
            processingCard.style.transition = 'opacity 0.3s ease';
            setTimeout(() => { processingCard.style.display = 'none'; }, 300);
        }

        // Show error card with animation
        if (errorCard && errorMessage) {
            setTimeout(() => {
                errorCard.style.display = 'block';
                errorCard.style.opacity = '0';
                errorMessage.textContent = message;

                setTimeout(() => {
                    errorCard.style.opacity = '1';
                    errorCard.style.transition = 'opacity 0.5s ease';
                }, 50);
            }, 350);
        }

        if (progressInterval) clearInterval(progressInterval);

        const submitBtn = document.getElementById('submit-btn');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="bi bi-x-circle me-2"></i> Error Occurred';
        }
    }

});
// --- END OF FILE main.js ---
