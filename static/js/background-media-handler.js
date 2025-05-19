// --- START OF FILE background-media-handler.js ---
/**
 * Background Media Handler
 * This module handles the interaction between background media (image/video) and shader selection
 * When a background media is selected, the shader selection is reset to "None"
 */

document.addEventListener('DOMContentLoaded', function() {
    // Find the background media input and shader select elements
    const backgroundMediaInput = document.getElementById('background_media');
    const backgroundShaderSelect = document.getElementById('background_shader');
    
    // If both elements exist, set up the interaction
    if (backgroundMediaInput && backgroundShaderSelect) {
        // When a background media file is selected, reset the shader selection
        backgroundMediaInput.addEventListener('change', function() {
            if (this.files && this.files.length > 0) {
                // A file was selected, reset the shader selection to "None"
                backgroundShaderSelect.value = '';
                
                // Trigger the change event to update any dependent UI
                const event = new Event('change');
                backgroundShaderSelect.dispatchEvent(event);
                
                console.log('Background media selected, shader reset to None');
            }
        });
    }
});
// --- END OF FILE background-media-handler.js ---
