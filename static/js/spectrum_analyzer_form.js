// --- START OF FILE main.js ---

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

        if (processingCard.style.display === 'block') {
            processingCard.style.opacity = '0';
            processingCard.style.transition = 'opacity 0.3s ease';
            setTimeout(() => { processingCard.style.display = 'none'; }, 300);
        }

        // Show error card with animation
        setTimeout(() => {
            errorCard.style.display = 'block';
            errorCard.style.opacity = '0';
            errorMessage.textContent = message;

            setTimeout(() => {
                errorCard.style.opacity = '1';
                errorCard.style.transition = 'opacity 0.5s ease';
            }, 50);
        }, 350);

        if (progressInterval) clearInterval(progressInterval);

        const submitBtn = document.getElementById('submit-btn');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="bi bi-x-circle me-2"></i> Error Occurred';
        }
    }

});
// --- END OF FILE main.js ---
