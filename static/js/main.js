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
    const showAdvancedBtn = document.getElementById('show-advanced');
    const advancedSettings = document.getElementById('advanced-settings');
    // Preset buttons removed
    // const presetBtns = document.querySelectorAll('.preset-btn');

    let currentJobId = null;
    let progressInterval = null;

    // Show/hide advanced settings
    showAdvancedBtn.addEventListener('click', function() {
        if (advancedSettings.style.display === 'none' || advancedSettings.style.display === '') {
            advancedSettings.style.display = 'block';
            showAdvancedBtn.textContent = 'Hide Advanced Settings';
        } else {
            advancedSettings.style.display = 'none';
            showAdvancedBtn.textContent = 'Show Advanced Settings';
        }
    });

    // Preset loading removed
    // presetBtns.forEach(btn => { ... });

    // Handle form submission
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();

        const submitBtn = document.getElementById('submit-btn');
        submitBtn.disabled = true; // Disable button during upload/process
        submitBtn.textContent = 'Processing...';

        // Show processing card
        uploadForm.style.display = 'none';
        processingCard.style.display = 'block';
        errorCard.style.display = 'none';
        downloadSection.style.display = 'none';
        progressBar.style.width = '0%';
        progressBar.textContent = ''; // Clear text
        progressBar.classList.remove('bg-success', 'bg-danger');
        progressBar.classList.add('progress-bar-animated');
        statusMessage.textContent = 'Uploading files...';

        // Submit form data
        const formData = new FormData(uploadForm);

        // Handle checkbox values correctly (important!)
        formData.set('always_on_bottom', document.getElementById('always_on_bottom').checked);
        formData.set('use_gradient', document.getElementById('use_gradient').checked);

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json().then(data => ({ status: response.status, body: data }))) // Keep status code
        .then(({ status, body }) => {
             if (status >= 400) { // Check for HTTP error status
                showError(body.error || `Server error: ${status}`);
                submitBtn.disabled = false;
                submitBtn.textContent = 'Generate Visualization';
                return;
            }
            if (body.error) { // Check for application-level error in JSON
                showError(body.error);
                 submitBtn.disabled = false;
                 submitBtn.textContent = 'Generate Visualization';
                return;
            }

            currentJobId = body.job_id;
            statusMessage.textContent = 'Upload complete. Starting processing...';
            startProgressPolling(currentJobId);
        })
        .catch(error => {
            showError('An error occurred during upload: ' + error.message);
             submitBtn.disabled = false;
             submitBtn.textContent = 'Generate Visualization';
        });
    });

    // Back button
    backBtn.addEventListener('click', function() {
        errorCard.style.display = 'none';
        uploadForm.style.display = 'block';
        const submitBtn = document.getElementById('submit-btn');
        submitBtn.disabled = false; // Re-enable button
        submitBtn.textContent = 'Generate Visualization';
    });

    // Poll for job progress
    function startProgressPolling(jobId) {
        // Clear any existing interval
        if (progressInterval) {
            clearInterval(progressInterval);
        }

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
                         // Re-enable submit button unless completed
                        if (data.status !== 'completed') {
                            const submitBtn = document.getElementById('submit-btn');
                            submitBtn.disabled = false;
                            submitBtn.textContent = 'Generate Visualization';
                        }
                    }
                })
                .catch(error => {
                    console.error('Error polling job status:', error);
                    // Optional: Show a less intrusive error or stop polling after N failures
                    // showError('Lost connection polling for status.');
                    // clearInterval(progressInterval);
                });
        }, 1500); // Poll every 1.5 seconds (slightly less aggressive)
    }

    // Update progress UI
    function updateProgress(data) {
        const progress = Math.min(100, Math.max(0, data.progress || 0)); // Clamp progress 0-100
        progressBar.style.width = `${progress}%`;
        progressBar.textContent = `${progress}%`; // Show percentage text
        progressBar.setAttribute('aria-valuenow', progress);

        if (data.status === 'queued') {
            statusMessage.textContent = 'Waiting in queue...';
        } else if (data.status === 'processing') {
            statusMessage.textContent = `Processing: ${progress}% complete`;
        } else if (data.status === 'completed') {
            statusMessage.textContent = 'Processing complete!';
            downloadSection.style.display = 'block';
            downloadLink.href = `/download/${currentJobId}`;
            progressBar.classList.remove('progress-bar-animated');
            progressBar.classList.add('bg-success');
             const submitBtn = document.getElementById('submit-btn'); // Keep disabled after success until Back is pressed
             submitBtn.disabled = true;
             submitBtn.textContent = 'Completed!';

        } else if (data.status === 'failed') {
            showError(data.error || 'An unknown error occurred during processing.');
            progressBar.classList.remove('progress-bar-animated');
            progressBar.classList.add('bg-danger');
            statusMessage.textContent = 'Processing Failed';
        }
    }

    // Show error message
    function showError(message) {
        console.error("Error displayed:", message); // Log error to console for debugging
        uploadForm.style.display = 'none';
        processingCard.style.display = 'none';
        errorCard.style.display = 'block';
        errorMessage.textContent = message; // Use textContent to prevent HTML injection

        if (progressInterval) {
            clearInterval(progressInterval);
        }
    }

    // Preset loading function removed
    // function loadPreset(presetName) { ... }
});
