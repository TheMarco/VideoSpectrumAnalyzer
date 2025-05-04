// --- START OF FILE dual_bar_visualizer_form.js ---

document.addEventListener('DOMContentLoaded', function() {
    // Element references
    const uploadForm = document.getElementById('upload-form');
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
    const errorModal = document.getElementById('errorModal');

    // Make progressInterval accessible to the shared error handling code
    window.progressInterval = null;

    // Make sure the error modal is hidden on page load
    if (errorModal) {
        errorModal.style.display = 'none';
        errorModal.classList.remove('show');

        // Remove any existing backdrops
        document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
            backdrop.parentNode.removeChild(backdrop);
        });

        // Remove modal-open class from body
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    }

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
    progressInterval = null;

    // Function to reset the UI back to the form state with animations
    function resetToFormState() {
        // Fade out error and processing cards
        if (errorCard.style.display === 'block') {
            errorCard.style.opacity = '0';
            errorCard.style.transition = 'opacity 0.3s ease';
            setTimeout(() => { errorCard.style.display = 'none'; }, 300);
        }

        if (processingCard.style.display === 'block') {
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

        currentJobId = null;
    }


    // Handle form submission
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();

        // Validate form before submission
        if (!validateForm()) {
            return; // Stop submission if validation fails
        }

        const submitBtn = document.getElementById('submit-btn');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="bi bi-arrow-repeat spin me-2"></i> Processing...';

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
        processingCard.style.display = 'block';
        processingCard.style.opacity = '0';
        setTimeout(() => {
            processingCard.style.opacity = '1';
            processingCard.style.transition = 'opacity 0.5s ease';
        }, 50);

        errorCard.style.display = 'none';
        downloadSection.style.display = 'none';
        progressBar.style.width = '0%';
        progressBar.textContent = '';
        progressBar.classList.remove('bg-success', 'bg-danger');
        progressBar.classList.add('progress-bar-animated');
        statusMessage.textContent = 'Uploading files...';

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
            statusMessage.textContent = 'Upload complete. Starting processing...';
            startProgressPolling(currentJobId);
        })
        .catch(error => {
            showError('An error occurred during upload: ' + error.message);
        });
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

    // These functions are now imported from form-validation.js

    // Update the file input to clear validation styling when a file is selected
    const audioFileInput = document.getElementById('file');
    if (audioFileInput) {
        audioFileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                this.classList.remove('is-invalid');
            }
        });
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

    // Update progress UI (Unchanged)
    function updateProgress(data) {
        const progress = Math.min(100, Math.max(0, data.progress || 0));
        progressBar.style.width = `${progress}%`;
        progressBar.textContent = `${progress}%`;
        progressBar.setAttribute('aria-valuenow', progress);

        if (data.status === 'queued') statusMessage.textContent = 'Waiting in queue...';
        else if (data.status === 'processing') statusMessage.textContent = `Processing: ${progress}% complete`;
        else if (data.status === 'completed') {
            statusMessage.textContent = 'Processing complete!';
            downloadSection.style.display = 'block';
            downloadLink.href = `/download/${currentJobId}`;
            progressBar.classList.remove('progress-bar-animated');
            progressBar.classList.add('bg-success');
            const submitBtn = document.getElementById('submit-btn');
             if(submitBtn) {
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

    // showError function is now imported from form-validation.js

});
// --- END OF FILE dual_bar_visualizer_form.js ---
