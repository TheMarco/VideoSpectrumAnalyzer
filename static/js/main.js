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
    const showAdvancedBtn = document.getElementById('show-advanced');
    const advancedSettings = document.getElementById('advanced-settings');

    // Background Type Elements
    const imageRadio = document.getElementById('bg_type_image');
    const videoRadio = document.getElementById('bg_type_video');
    const imageInput = document.getElementById('background_image');
    const videoInput = document.getElementById('background_video');


    let currentJobId = null;
    let progressInterval = null;

    // Show/hide advanced settings (Unchanged)
    showAdvancedBtn.addEventListener('click', function() {
        if (advancedSettings.style.display === 'none' || advancedSettings.style.display === '') {
            advancedSettings.style.display = 'block';
            showAdvancedBtn.textContent = 'Hide Advanced Settings';
        } else {
            advancedSettings.style.display = 'none';
            showAdvancedBtn.textContent = 'Show Advanced Settings';
        }
    });


    // Handle form submission
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();

        const submitBtn = document.getElementById('submit-btn');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Processing...';

        // Show processing card
        uploadForm.style.display = 'none';
        processingCard.style.display = 'block';
        errorCard.style.display = 'none';
        downloadSection.style.display = 'none';
        progressBar.style.width = '0%';
        progressBar.textContent = '';
        progressBar.classList.remove('bg-success', 'bg-danger');
        progressBar.classList.add('progress-bar-animated');
        statusMessage.textContent = 'Uploading files...';

        // --- Create FormData and Append Background File ---
        const formData = new FormData(); // Create empty FormData

        // Append all non-file fields from the form
        const formElements = uploadForm.elements;
        for (let i = 0; i < formElements.length; i++) {
            const element = formElements[i];
            if (element.name && element.type !== 'file' && element.type !== 'submit' && element.type !== 'radio' && element.type !== 'checkbox') {
                 formData.append(element.name, element.value);
            }
             // Handle checkboxes correctly
            else if (element.type === 'checkbox' && element.name) {
                formData.append(element.name, element.checked ? 'on' : 'off'); // Send 'on' or 'off' consistently
            }
             // Radio buttons for background_type are handled implicitly by checking which file input is active
        }

         // Append the main audio file
        const audioFileInput = document.getElementById('file');
        if (audioFileInput.files.length > 0) {
            formData.append('file', audioFileInput.files[0]);
        } else {
             showError('Please select an audio file.');
             submitBtn.disabled = false;
             submitBtn.textContent = 'Generate Visualization';
             return; // Stop submission
        }


        // Append the correct background file based on radio selection
        if (imageRadio.checked && imageInput.files.length > 0) {
            formData.append('background_image', imageInput.files[0]);
            console.log("Appending background image:", imageInput.files[0].name);
        } else if (videoRadio.checked && videoInput.files.length > 0) {
            formData.append('background_video', videoInput.files[0]);
            console.log("Appending background video:", videoInput.files[0].name);
        } else {
            console.log("No background media selected or file missing.");
        }
        // --- End FormData Creation ---

        // --- Fetch Request (Unchanged) ---
        fetch('/upload', {
            method: 'POST',
            body: formData // Send the manually constructed FormData
        })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(({ status, body }) => {
             if (status >= 400) {
                showError(body.error || `Server error: ${status}`);
                submitBtn.disabled = false; submitBtn.textContent = 'Generate Visualization';
                return;
            }
            if (body.error) {
                showError(body.error);
                 submitBtn.disabled = false; submitBtn.textContent = 'Generate Visualization';
                return;
            }

            currentJobId = body.job_id;
            statusMessage.textContent = 'Upload complete. Starting processing...';
            startProgressPolling(currentJobId);
        })
        .catch(error => {
            showError('An error occurred during upload: ' + error.message);
             submitBtn.disabled = false; submitBtn.textContent = 'Generate Visualization';
        });
    });

    // Back button (Unchanged)
    backBtn.addEventListener('click', function() {
        errorCard.style.display = 'none';
        uploadForm.style.display = 'block';
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
                    if (data.error) { showError(data.error); clearInterval(progressInterval); return; }
                    updateProgress(data);
                    if (data.status === 'completed' || data.status === 'failed') {
                        clearInterval(progressInterval);
                        if (data.status !== 'completed') {
                            const submitBtn = document.getElementById('submit-btn');
                            submitBtn.disabled = false; submitBtn.textContent = 'Generate Visualization';
                        }
                    }
                })
                .catch(error => { console.error('Error polling job status:', error); });
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
             submitBtn.disabled = true; submitBtn.textContent = 'Completed!';
        } else if (data.status === 'failed') {
            showError(data.error || 'An unknown error occurred during processing.');
            progressBar.classList.remove('progress-bar-animated');
            progressBar.classList.add('bg-danger');
            statusMessage.textContent = 'Processing Failed';
        }
    }

    // Show error message (Unchanged)
    function showError(message) {
        console.error("Error displayed:", message);
        uploadForm.style.display = 'none';
        processingCard.style.display = 'none';
        errorCard.style.display = 'block';
        errorMessage.textContent = message; // Use textContent for safety
        if (progressInterval) clearInterval(progressInterval);
         // Ensure back button allows retry
         const submitBtn = document.getElementById('submit-btn');
         if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = 'Generate Visualization'; }
    }

});
// --- END OF FILE main.js ---
