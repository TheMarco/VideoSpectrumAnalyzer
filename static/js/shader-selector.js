// --- START OF FILE shader-selector.js ---
/**
 * Shader selector functionality
 * This module handles selecting a shader from the URL parameters
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
});
// --- END OF FILE shader-selector.js ---
