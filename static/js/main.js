// --- START OF FILE main.js ---

document.addEventListener('DOMContentLoaded', function() {
    // ... (references to elements remain the same) ...
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

    let currentJobId = null;
    let progressInterval = null;

    // Function to reset the UI back to the form state (Unchanged)
    function resetToFormState() {
        errorCard.style.display = 'none';
        processingCard.style.display = 'none';
        if (configTabs) configTabs.style.display = 'flex';
        if (configTabsContent) configTabsContent.style.display = 'block';
        const submitBtn = document.getElementById('submit-btn');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Generate Visualization';
        }
        if (progressBar) {
            progressBar.style.width = '0%';
            progressBar.textContent = '';
            progressBar.classList.remove('bg-success', 'bg-danger');
            progressBar.classList.add('progress-bar-animated');
        }
        if (statusMessage) statusMessage.textContent = 'Processing your audio file...';
        const audioFileInput = document.getElementById('file');
        const backgroundMediaInput = document.getElementById('background_media');
        if (audioFileInput) audioFileInput.value = '';
        if (backgroundMediaInput) backgroundMediaInput.value = '';
        currentJobId = null;
    }


    // Handle form submission
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();

        const submitBtn = document.getElementById('submit-btn');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Processing...';

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
        // ****** MODIFIED THIS BLOCK ******
        if (audioFileInput && audioFileInput.files.length > 0) {
            formData.append('file', audioFileInput.files[0]);
        } else {
             showError('Please select an audio file.');
             // REMOVED: resetToFormState(); // DO NOT reset here, let showError handle UI
             return; // Stop submission
        }
        // ****** END MOD ******

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

    // Show error message (Unchanged from previous correct version)
    function showError(message) {
        console.error("Error displayed:", message);
        if (configTabs) configTabs.style.display = 'none';
        if (configTabsContent) configTabsContent.style.display = 'none';
        processingCard.style.display = 'none';
        errorCard.style.display = 'block';
        errorMessage.textContent = message;
        if (progressInterval) clearInterval(progressInterval);
         const submitBtn = document.getElementById('submit-btn');
         if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Error Occurred';
         }
    }

});
// --- END OF FILE main.js ---
