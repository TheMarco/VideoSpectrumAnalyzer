# Audio Visualizer Suite - Module Structure Design Document

## Overview

This document outlines the module structure of the Audio Visualizer Suite application, focusing on proper separation of concerns and how to avoid entanglement between modules. It serves as a guide for developers to understand how to maintain clean boundaries between components and how to properly share code across the application.

## Core Architecture Principles

1. **Separation of Concerns**: Each module should have a single, well-defined responsibility
2. **Modularity**: Components should be self-contained with clear interfaces
3. **Reusability**: Common functionality should be shared through well-defined utilities
4. **Independence**: Visualizers should not depend on each other
5. **Extensibility**: New visualizers should be easy to add without modifying existing code

## Application Structure

The Audio Visualizer Suite is structured as follows:

```
AudioVisualizerSuite/
├── app.py                  # Main Flask application
├── core/                   # Core framework components
│   ├── __init__.py
│   ├── base_visualizer.py  # Base class for all visualizers
│   ├── registry.py         # Visualizer discovery and registration
│   └── utils.py            # Core utility functions
├── modules/                # Shared processing modules
│   ├── __init__.py
│   ├── audio_processor.py  # Audio processing utilities
│   ├── config_handler.py   # Configuration processing
│   ├── ffmpeg_handler.py   # FFmpeg integration
│   ├── media_handler.py    # Media file handling
│   ├── renderer.py         # Base rendering functionality
│   └── utils.py            # General utility functions
├── static/                 # Static assets
│   ├── css/
│   ├── js/
│   │   ├── form-validation.js      # Shared form validation
│   │   ├── form-utilities.js       # Shared form utilities
│   │   ├── modal-manager.js        # Shared modal dialog management
│   │   ├── processing-ui.js        # Shared processing UI and video playback
│   │   ├── tab-navigation.js       # Shared tab navigation utilities
│   │   ├── tooltip-manager.js      # Shared tooltip management
│   │   ├── ui-effects.js           # Shared UI animations and effects
│   │   ├── main.js                 # Main application JS
│   │   └── [visualizer]_form.js    # Visualizer-specific form handling
│   └── images/
├── templates/              # HTML templates
│   ├── partials/           # Shared template components
│   │   └── error_modal.html        # Shared error modal
│   ├── index.html          # Home page
│   ├── error.html          # Error page
│   └── [visualizer]_form.html      # Visualizer-specific forms
├── uploads/                # User uploaded files
├── outputs/                # Generated visualizations
└── visualizers/            # Visualizer implementations
    ├── __init__.py
    └── [visualizer_name]/  # Each visualizer in its own directory
        ├── __init__.py
        ├── config.py       # Visualizer-specific configuration
        ├── renderer.py     # Visualizer-specific renderer
        └── visualizer.py   # Main visualizer implementation
```

## Component Responsibilities

### Core Components

The `core` package provides the foundation for the application:

- **base_visualizer.py**: Defines the `BaseVisualizer` abstract class that all visualizers must inherit from. It provides common functionality and defines the interface that all visualizers must implement.
- **registry.py**: Handles discovery and registration of visualizers. It scans the `visualizers` directory for implementations and makes them available to the application.
- **utils.py**: Contains utility functions used across the core framework.

### Shared Modules

The `modules` package contains shared functionality used by all visualizers:

- **audio_processor.py**: Handles audio file loading and analysis.
- **config_handler.py**: Processes configuration parameters with defaults.
- **ffmpeg_handler.py**: Manages FFmpeg processes for video generation.
- **media_handler.py**: Handles loading and processing of media files (images, videos).
- **renderer.py**: Provides base rendering functionality.
- **utils.py**: Contains general utility functions.

### Visualizers

Each visualizer is contained in its own directory under the `visualizers` package:

- **visualizer.py**: Main implementation that inherits from `BaseVisualizer`.
- **config.py**: Visualizer-specific configuration processing.
- **renderer.py**: Visualizer-specific rendering logic.

### Frontend Components

- **Templates**: HTML templates for the application UI.
  - **partials/**: Contains shared template components like the error modal.
  - **[visualizer]_form.html**: Visualizer-specific form templates.

- **JavaScript**:
  - **Shared Modules**:
    - **form-validation.js**: Form validation and error handling.
    - **form-utilities.js**: Form data collection and manipulation utilities.
    - **modal-manager.js**: Modal dialog management and interaction.
    - **processing-ui.js**: Processing UI, progress tracking, and video playback.
    - **tab-navigation.js**: Tab navigation and error indication.
    - **tooltip-manager.js**: Bootstrap tooltip initialization and management.
    - **ui-effects.js**: UI animations and visual effects.
  - **Visualizer-Specific**:
    - **[visualizer]_form.js**: Visualizer-specific form handling and validation.

## Shared vs. Visualizer-Specific Code

### What Should Be Shared

1. **Core Framework**: The base visualizer class, registry, and core utilities.
2. **Processing Modules**: Audio processing, media handling, FFmpeg integration.
3. **UI Components**: Error handling, form validation, common UI elements.
4. **Utility Functions**: General-purpose functions like color conversion.

### What Should Be Visualizer-Specific

1. **Rendering Logic**: How the visualizer draws its specific visualization.
2. **Configuration**: Default values and processing specific to the visualizer.
3. **Form Handling**: Validation specific to the visualizer's parameters.
4. **UI Elements**: Visualizer-specific controls and displays.

## Guidelines for Adding New Visualizers

1. **Create a New Directory**: Add a new directory under `visualizers/` with your visualizer name.
2. **Implement Required Files**:
   - `__init__.py`: Package initialization.
   - `visualizer.py`: Main visualizer class inheriting from `BaseVisualizer`.
   - `config.py`: Configuration processing.
   - `renderer.py`: Rendering implementation.
3. **Create Templates**:
   - Add a form template in `templates/[visualizer_name]_form.html`.
   - Use the shared error modal via `{% include 'partials/error_modal.html' %}`.
4. **Add JavaScript**:
   - Create `static/js/[visualizer_name]_form.js` for form handling.
   - Include all shared modules in your template:
     ```html
     <!-- Shared Modules -->
     <script src="{{ url_for('static', filename='js/ui-effects.js') }}"></script>
     <script src="{{ url_for('static', filename='js/modal-manager.js') }}"></script>
     <script src="{{ url_for('static', filename='js/form-utilities.js') }}"></script>
     <script src="{{ url_for('static', filename='js/tab-navigation.js') }}"></script>
     <script src="{{ url_for('static', filename='js/tooltip-manager.js') }}"></script>
     <script src="{{ url_for('static', filename='js/form-validation.js') }}"></script>
     <script src="{{ url_for('static', filename='js/processing-ui.js') }}"></script>
     ```
   - Initialize and use the shared modules in your form JS:
     ```javascript
     // Initialize the shared processing UI module
     const processingUI = window.ProcessingUI.init();

     // Use form utilities for data collection
     const formData = window.FormUtils.collectFormData(formElement);

     // Use tab navigation for managing tabs
     window.TabNavigation.showFirstTab();
     ```

## Avoiding Entanglement

To prevent visualizers from becoming entangled with each other:

1. **No Direct Dependencies**: Visualizers should never import from or reference each other.
2. **Use the Core Framework**: All communication should go through the core framework.
3. **Shared Code in Modules**: Common functionality should be moved to the `modules` package.
4. **Clear Interfaces**: Use well-defined interfaces for all components.
5. **Consistent Structure**: Follow the established directory and file structure.

## Shared JavaScript Modules

The application uses a modular JavaScript architecture to promote code reuse and maintainability:

### UI and Interaction Modules

1. **UI Effects (`ui-effects.js`)**:
   - Handles animations and visual effects across the application
   - Provides consistent fade-in/out transitions
   - Manages hover effects and other UI animations

2. **Modal Management (`modal-manager.js`)**:
   - Handles modal dialog initialization and cleanup
   - Manages modal backdrops and accessibility
   - Provides a consistent API for showing/hiding modals

3. **Tab Navigation (`tab-navigation.js`)**:
   - Manages tab switching and activation
   - Handles error indicators on tabs
   - Provides utilities for finding and navigating to tabs

4. **Tooltip Management (`tooltip-manager.js`)**:
   - Initializes Bootstrap tooltips
   - Handles tooltip refreshing for dynamic content
   - Ensures consistent tooltip behavior

### Form Handling Modules

1. **Form Utilities (`form-utilities.js`)**:
   - Collects form data consistently
   - Handles file input validation
   - Provides form reset functionality

2. **Form Validation (`form-validation.js`)**:
   - Validates form inputs
   - Shows validation errors with proper UI feedback
   - Integrates with tab navigation for error indication

3. **Processing UI (`processing-ui.js`)**:
   - Manages the processing interface
   - Handles progress tracking and updates
   - Controls video playback after processing

### Using the Shared Modules

Example of proper form handling using the shared modules:

```javascript
// In [visualizer]_form.js
document.addEventListener('DOMContentLoaded', function() {
    // Initialize shared modules
    const processingUI = window.ProcessingUI.init();

    // Get form element
    const uploadForm = document.getElementById('upload-form');

    // Handle form submission
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();

        // Validate form
        if (!validateForm()) {
            return; // Stop submission if validation fails
        }

        // Prepare form data using shared utilities
        const formData = window.FormUtils.collectFormData(uploadForm);
        window.FormUtils.addFileInputs(formData, ['file', 'background_media']);

        // Submit the form using the shared processing UI
        processingUI.submitForm(formData);
    });

    // Form validation function
    function validateForm() {
        // Validate required file input
        if (!window.FormUtils.validateFileInput('file', {
            errorMessage: 'Please select an audio file to process'
        })) {
            return false;
        }

        // Additional validation logic...

        return true;
    }
});
```

## FFmpeg Processing

FFmpeg processing is handled by the shared `ffmpeg_handler.py` module:

1. **Process Setup**: Use `setup_ffmpeg_process()` to initialize FFmpeg.
2. **Frame Writing**: Use `write_frame_to_ffmpeg()` to write frames.
3. **Process Finalization**: Use `finalize_ffmpeg_process()` to complete processing.
4. **Audio Addition**: Use `add_audio_to_video()` to add audio to the video.

## Configuration Handling

Configuration handling follows a consistent pattern:

1. **Default Configuration**: Define default values in `config.py`.
2. **Configuration Processing**: Use `process_config()` to merge user input with defaults.
3. **Validation**: Validate configuration values before use.

Example of proper configuration handling:

```python
def process_config(config):
    """Process and validate configuration."""
    # Default configuration
    default_config = {
        "n_bars": 40,
        "bar_width": 25,
        "bar_gap": 2,
        # Other defaults...
    }

    # Merge with user config
    merged_config = {**default_config, **config}

    # Validate and transform values
    merged_config["bar_color_rgb"] = hex_to_rgb(merged_config["bar_color"])

    return merged_config
```

## Renderer Implementation

Renderers should follow a consistent pattern:

1. **Initialization**: Set up the renderer with dimensions and configuration.
2. **Frame Rendering**: Implement a `render_frame()` method that takes frame data and returns an image.
3. **Cleanup**: Properly clean up resources when done.

Example of proper renderer implementation:

```python
class VisualizerRenderer:
    def __init__(self, width, height, config, artist_font, title_font):
        self.width = width
        self.height = height
        self.config = config
        self.artist_font = artist_font
        self.title_font = title_font

    def render_frame(self, frame_data, background_image, metadata):
        # Create a new image
        image = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))

        # Draw on the image
        draw = ImageDraw.Draw(image)

        # Render visualizer elements
        self._render_bars(draw, frame_data)
        self._render_text(draw, metadata)

        # Composite with background
        result = Image.alpha_composite(background_image.convert("RGBA"), image)

        return result

    def _render_bars(self, draw, frame_data):
        # Visualizer-specific bar rendering
        pass

    def _render_text(self, draw, metadata):
        # Text rendering
        pass
```

## Conclusion

By following these guidelines, the Audio Visualizer Suite can maintain a clean, modular structure where visualizers are independent of each other but share common functionality through well-defined interfaces. This approach makes the application easier to maintain, extend, and debug.

The modular JavaScript architecture provides several benefits:
- **Reduced Code Duplication**: Common functionality is defined in a single place
- **Improved Maintainability**: Changes to shared functionality only need to be made in one place
- **Consistent Behavior**: All parts of the application have consistent animations, modal behavior, and form handling
- **Easier Extension**: New visualizer types can reuse the shared modules
- **Separation of Concerns**: Each module focuses on a specific aspect of the UI

Remember:
- Keep visualizers independent
- Share code through the core framework and modules
- Use the shared JavaScript modules for frontend functionality
- Use consistent patterns for configuration, rendering, and validation
- Follow the established directory and file structure
- Use shared components for common UI elements like error handling and processing UI
