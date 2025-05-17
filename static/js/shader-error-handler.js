/**
 * Shader Error Handler
 * A simple, standalone implementation for displaying shader errors
 */

// Create a self-executing function to avoid polluting the global namespace
(function() {
    // Create the error modal if it doesn't exist
    function ensureErrorModalExists() {
        if (document.getElementById('shader-error-modal')) {
            return; // Modal already exists
        }

        // Create the modal element
        const modalHtml = `
        <div class="modal fade" id="shader-error-modal" tabindex="-1" aria-labelledby="shaderErrorModalLabel" aria-hidden="true" data-bs-backdrop="static">
            <div class="modal-dialog modal-dialog-centered modal-lg">
                <div class="modal-content">
                    <div class="modal-header" style="background: linear-gradient(90deg, rgba(255, 82, 82, 0.1), rgba(255, 82, 82, 0.2));">
                        <h5 class="modal-title" id="shaderErrorModalLabel"><i class="bi bi-exclamation-triangle-fill me-2"></i>Shader Error</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <!-- Error message will be inserted here -->
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="bi bi-x me-2"></i>Close
                        </button>
                    </div>
                </div>
            </div>
        </div>`;

        // Append the modal to the body
        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = modalHtml;
        document.body.appendChild(modalContainer.firstElementChild);
    }

    // Function to show a shader error
    function showShaderError(shaderName, errorDetails) {
        console.log("Showing shader error:", shaderName, errorDetails);

        // Make sure the modal exists
        ensureErrorModalExists();

        // Get the modal element
        const modalElement = document.getElementById('shader-error-modal');
        if (!modalElement) {
            console.error("Failed to create shader error modal");
            alert(`Shader Error: ${shaderName}\n\n${errorDetails}`);
            return;
        }

        // Format the error message
        const formattedError = `
            <div class="shader-error">
                <h4 class="text-danger"><i class="bi bi-exclamation-triangle-fill me-2"></i>Shader Error: ${shaderName}</h4>
                <p>The shader failed to render properly. This could be due to:</p>
                <ul>
                    <li>Syntax errors in the shader code</li>
                    <li>Compatibility issues with your graphics hardware</li>
                    <li>Resource limitations</li>
                </ul>
                <div class="alert alert-secondary">
                    <p><strong>Technical Details:</strong></p>
                    <pre style="max-height: 200px; overflow-y: auto;">${errorDetails}</pre>
                </div>
            </div>`;

        // Set the modal content
        const modalBody = modalElement.querySelector('.modal-body');
        if (modalBody) {
            modalBody.innerHTML = formattedError;
        }

        // Show the modal using Bootstrap
        try {
            const bsModal = new bootstrap.Modal(modalElement);
            bsModal.show();
        } catch (e) {
            console.error("Error showing modal:", e);
            // Fallback to alert
            alert(`Shader Error: ${shaderName}\n\n${errorDetails}`);
        }
    }

    // Function to handle shader errors from the job status data
    function handleShaderError(data) {
        if (!data) return false;

        console.log("ShaderErrorHandler: Checking data for shader errors:", data);

        // Handle undefined error case
        if (data.error === undefined) {
            console.log("ShaderErrorHandler: Detected undefined error");

            // Try to get shader name from the data
            let shaderName = "Unknown Shader";
            if (data.shader_path) {
                const pathParts = data.shader_path.split('/');
                shaderName = pathParts[pathParts.length - 1];
            }

            // Show a generic shader error
            showShaderError(shaderName, "The shader failed to render. This could be due to compatibility issues with your graphics hardware or syntax errors in the shader code.");
            return true;
        }

        // Check if this is a shader error
        if (data.error_type === 'shader_error') {
            console.log("ShaderErrorHandler: Detected error_type === 'shader_error'");

            // Get the shader name
            const shaderName = data.shader_name ||
                (data.shader_error_details ? data.shader_error_details.shader_name : "Unknown Shader");

            // Get the error message
            const errorMessage = data.error ||
                (data.shader_error_details ? data.shader_error_details.error_message : "Unknown error");

            // Show the error
            showShaderError(shaderName, errorMessage);
            return true;
        }

        // Check if the error message contains shader error indicators
        if (data.error && (
            data.error.includes('SHADER ERROR') ||
            data.error.includes('shader') ||
            data.error.includes('.glsl')
        )) {
            console.log("ShaderErrorHandler: Detected shader-related keywords in error message");

            // Extract the shader name if possible
            let shaderName = "Unknown shader";
            const shaderMatch = data.error.match(/SHADER ERROR: ([^'\n]+)/);
            if (shaderMatch && shaderMatch[1]) {
                shaderName = shaderMatch[1];
            }

            // Show the error
            showShaderError(shaderName, data.error);
            return true;
        }

        // Check if we have a shader_path in the data
        if (data.shader_path) {
            console.log("ShaderErrorHandler: Found shader_path in data");

            // Extract the shader name from the path
            const pathParts = data.shader_path.split('/');
            const shaderName = pathParts[pathParts.length - 1];

            // Show a generic shader error
            showShaderError(shaderName, data.error || "The shader failed to render. This could be due to compatibility issues with your graphics hardware or syntax errors in the shader code.");
            return true;
        }

        return false;
    }

    // Export the functions to the global scope
    window.ShaderErrorHandler = {
        showShaderError: showShaderError,
        handleShaderError: handleShaderError
    };
})();
