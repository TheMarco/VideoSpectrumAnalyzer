// --- START OF FILE shader-selector.js ---
/**
 * Shader selector functionality
 * This module handles selecting a shader from the URL parameters
 * and loading the shader explorer in a modal
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if there's a shader parameter in the URL
    const urlParams = new URLSearchParams(window.location.search);
    const shaderPath = urlParams.get('shader');
    
    if (shaderPath) {
        // Find the background shader select element
        const backgroundShaderSelect = document.getElementById('background_shader');
        
        if (backgroundShaderSelect) {
            // Find the option with the matching value
            const options = Array.from(backgroundShaderSelect.options);
            const matchingOption = options.find(option => option.value === shaderPath);
            
            if (matchingOption) {
                // Select the option
                backgroundShaderSelect.value = shaderPath;
                
                // Trigger the change event to update any dependent UI
                const event = new Event('change');
                backgroundShaderSelect.dispatchEvent(event);
                
                console.log(`Selected shader: ${shaderPath}`);
                
                // Scroll to the shader dropdown
                backgroundShaderSelect.scrollIntoView({ behavior: 'smooth', block: 'center' });
                
                // Highlight the shader dropdown briefly
                backgroundShaderSelect.classList.add('highlight-selection');
                setTimeout(() => {
                    backgroundShaderSelect.classList.remove('highlight-selection');
                }, 2000);
            } else {
                console.warn(`Shader not found in options: ${shaderPath}`);
            }
        } else {
            console.warn('Background shader select element not found');
        }
        
        // Remove the shader parameter from the URL to avoid reselection on page refresh
        urlParams.delete('shader');
        const newUrl = window.location.pathname + (urlParams.toString() ? `?${urlParams.toString()}` : '');
        window.history.replaceState({}, '', newUrl);
    }
    
    // Set up modal shader explorer
    setupModalShaderExplorer();
});

/**
 * Set up the modal shader explorer functionality
 */
function setupModalShaderExplorer() {
    // Find all links to the shader explorer
    const shaderExplorerLinks = document.querySelectorAll('a[href^="/shader-explorer"]');
    
    shaderExplorerLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault(); // Prevent default navigation
            
            // Get the current visualizer name from the URL
            const currentPath = window.location.pathname;
            const visualizerMatch = currentPath.match(/\/visualizer\/([^\/]+)/);
            const visualizerName = visualizerMatch ? visualizerMatch[1] : '';
            
            // Create the modal if it doesn't exist
            let shaderModal = document.getElementById('shaderExplorerModal');
            if (!shaderModal) {
                shaderModal = document.createElement('div');
                shaderModal.id = 'shaderExplorerModal';
                shaderModal.className = 'modal fade';
                shaderModal.setAttribute('tabindex', '-1');
                shaderModal.setAttribute('aria-labelledby', 'shaderExplorerModalLabel');
                shaderModal.setAttribute('aria-hidden', 'true');
                shaderModal.style.zIndex = '1100'; // Higher than Bootstrap's default
                
                shaderModal.innerHTML = `
                    <div class="modal-dialog modal-xl modal-dialog-centered">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title" id="shaderExplorerModalLabel">
                                    <i class="bi bi-palette me-2"></i>Background Shader Explorer
                                </h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body p-0">
                                <iframe id="shaderExplorerFrame" style="width:100%; height:80vh; border:none;"></iframe>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            </div>
                        </div>
                    </div>
                `;
                
                document.body.appendChild(shaderModal);
                
                // Initialize the Bootstrap modal with proper options
                const modalOptions = {
                    backdrop: true,
                    keyboard: true,
                    focus: true
                };
                
                const modalInstance = new bootstrap.Modal(shaderModal, modalOptions);
                
                // Handle messages from the iframe
                window.addEventListener('message', function(event) {
                    // Check if the message is from our iframe
                    if (event.data && event.data.type === 'shaderSelected') {
                        const selectedShader = event.data.shader;
                        
                        // Find the background shader select element
                        const backgroundShaderSelect = document.getElementById('background_shader');
                        
                        if (backgroundShaderSelect) {
                            // Find the option with the matching value
                            const options = Array.from(backgroundShaderSelect.options);
                            const matchingOption = options.find(option => option.value === selectedShader);
                            
                            if (matchingOption) {
                                // Select the option
                                backgroundShaderSelect.value = selectedShader;
                                
                                // Trigger the change event to update any dependent UI
                                const event = new Event('change');
                                backgroundShaderSelect.dispatchEvent(event);
                                
                                console.log(`Selected shader: ${selectedShader}`);
                                
                                // Highlight the shader dropdown briefly
                                backgroundShaderSelect.classList.add('highlight-selection');
                                setTimeout(() => {
                                    backgroundShaderSelect.classList.remove('highlight-selection');
                                }, 2000);
                            }
                        }
                        
                        // Close the modal
                        const modal = bootstrap.Modal.getInstance(shaderModal);
                        if (modal) {
                            modal.hide();
                        }
                    }
                });
                
                // Clean up when modal is hidden
                shaderModal.addEventListener('hidden.bs.modal', function() {
                    // Remove any lingering backdrops
                    const backdrops = document.querySelectorAll('.modal-backdrop');
                    backdrops.forEach(backdrop => {
                        backdrop.remove();
                    });
                    
                    // Reset body styles
                    document.body.classList.remove('modal-open');
                    document.body.style.overflow = '';
                    document.body.style.paddingRight = '';
                });
            }
            
            // Set the iframe src
            const iframe = document.getElementById('shaderExplorerFrame');
            iframe.src = `/shader-explorer?visualizer_name=${visualizerName}&modal=true`;
            
            // Show the modal
            const modalInstance = bootstrap.Modal.getInstance(shaderModal);
            if (modalInstance) {
                modalInstance.show();
            } else {
                const newModalInstance = new bootstrap.Modal(shaderModal);
                newModalInstance.show();
            }
        });
    });
}
