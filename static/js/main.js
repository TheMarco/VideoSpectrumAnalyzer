// --- START OF FILE main.js ---

document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    const processingCard = document.getElementById('processing-card');
    const errorCard = document.getElementById('error-card');
    const progressBar = document.getElementById('progress-bar');
    const statusMessage = document.getElementById('status-message');
    const errorMessage = document.getElementById('error-message');
    const downloadSection = document.getElementById('download-section');
    const downloadLink = document.getElementById('download-link');
    const backBtn = document.getElementById('back-btn');
    // const showAdvancedBtn = document.getElementById('show-advanced'); // No longer needed
    // const advancedSettings = document.getElementById('advanced-settings'); // No longer needed

    // REMOVED: Background Type Elements and Toggle Logic
    // const imageRadio = ...
    // const videoRadio = ...
    // const imageInput = ...
    // const videoInput = ...

    let currentJobId = null;
    let progressInterval = null;

    // REMOVED: Show/hide advanced settings logic
    // showAdvancedBtn.addEventListener(...)

    // Handle form submission
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();

        const submitBtn = document.getElementById('submit-btn');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Processing...';

        // Hide form sections, show processing
        const configTabsContent = document.getElementById('configTabsContent');
        const configTabs = document.getElementById('configTabs');
        if (configTabs) configTabs.style.display = 'none';
        if (configTabsContent) configTabsContent.style.display = 'none';

        processingCard.style.display = 'block';
        errorCard.style.display = 'none';
        downloadSection.style.display = 'none';
        progressBar.style.width = '0%';
        progressBar.textContent = '';
        progressBar.classList.remove('bg-success', 'bg-danger');
        progressBar.classList.add('progress-bar-animated');
        statusMessage.textContent = 'Uploading files...';

        const formData = new FormData();

        // Append all non-file fields from the form
        const formElements = uploadForm.elements;
        for (let i = 0; i < formElements.length; i++) {
            const element = formElements[i];
            // Skip files, submit, radio (handled separately or not needed)
            if (element.name && element.type !== 'file' && element.type !== 'submit' && element.type !== 'radio') {
                 // Handle checkboxes correctly
                if (element.type === 'checkbox') {
                    formData.append(element.name, element.checked ? 'on' : 'off');
                } else {
                    formData.append(element.name, element.value);
                }
            }
        }

         // Append the main audio file
        const audioFileInput = document.getElementById('file');
        if (audioFileInput && audioFileInput.files.length > 0) {
            formData.append('file', audioFileInput.files[0]);
        } else {
             showError('Please select an audio file.');
             // Re-enable form for correction
             if (configTabs) configTabs.style.display = 'flex'; // or 'block' depending on layout needs
             if (configTabsContent) configTabsContent.style.display = 'block';
             processingCard.style.display = 'none';
             submitBtn.disabled = false;
             submitBtn.textContent = 'Generate Visualization';
             return; // Stop submission
        }

        // Append the unified background media file (if selected)
        const backgroundMediaInput = document.getElementById('background_media');
        if (backgroundMediaInput && backgroundMediaInput.files.length > 0) {
            formData.append('background_media', backgroundMediaInput.files[0]);
            console.log("Appending background media:", backgroundMediaInput.files[0].name);
        } else {
            console.log("No background media selected.");
        }

        // --- Fetch Request (Unchanged) ---
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(({ status, body }) => {
             if (status >= 400) {
                showError(body.error || `Server error: ${status}`);
                // Don't re-enable submit button here, use Back button
                return;
            }
            if (body.error) {
                showError(body.error);
                // Don't re-enable submit button here, use Back button
                return;
            }

            currentJobId = body.job_id;
            statusMessage.textContent = 'Upload complete. Starting processing...';
            startProgressPolling(currentJobId);
        })
        .catch(error => {
            showError('An error occurred during upload: ' + error.message);
             // Don't re-enable submit button here, use Back button
        });
    });

    // Back button
    backBtn.addEventListener('click', function() {
        errorCard.style.display = 'none';
        // Show form sections again
        const configTabsContent = document.getElementById('configTabsContent');
        const configTabs = document.getElementById('configTabs');
        if (configTabs) configTabs.style.display = 'flex'; // or 'block'
        if (configTabsContent) configTabsContent.style.display = 'block';

        const submitBtn = document.getElementById('submit-btn');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Generate Visualization';
        // Reset progress bar just in case
        progressBar.style.width = '0%';
        progressBar.textContent = '';
        progressBar.classList.remove('bg-success', 'bg-danger');
    });

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
                        // No need to touch submit button state here anymore
                    }
                })
                .catch(error => {
                    showError('Error polling job status: ' + error.message); // Show polling errors
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
            // Keep submit button disabled, user should use Back button to restart
            const submitBtn = document.getElementById('submit-btn');
             if(submitBtn) submitBtn.textContent = 'Completed!';
        } else if (data.status === 'failed') {
            showError(data.error || 'An unknown error occurred during processing.');
            progressBar.classList.remove('progress-bar-animated');
            progressBar.classList.add('bg-danger');
            statusMessage.textContent = 'Processing Failed';
        }
    }

    // Show error message
    function showError(message) {
        console.error("Error displayed:", message);
        // Hide form sections
        const configTabsContent = document.getElementById('configTabsContent');
        const configTabs = document.getElementById('configTabs');
        if (configTabs) configTabs.style.display = 'none';
        if (configTabsContent) configTabsContent.style.display = 'none';

        processingCard.style.display = 'none'; // Hide processing card
        errorCard.style.display = 'block'; // Show error card
        errorMessage.textContent = message; // Use textContent for safety
        if (progressInterval) clearInterval(progressInterval);
         // Back button is now the primary way to retry
         const submitBtn = document.getElementById('submit-btn');
         if (submitBtn) {
            submitBtn.disabled = true; // Keep disabled until Back is clicked
            submitBtn.textContent = 'Error Occurred';
         }
    }

});
// --- END OF FILE main.js ---
