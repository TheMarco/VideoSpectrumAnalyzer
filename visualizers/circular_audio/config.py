"""
Configuration for the Circular Audio Visualizer.
"""

CIRCULAR_AUDIO_CONFIG = {
    "name": "Circular Audio Visualizer",
    "description": "A circular audio visualizer with configurable segments and bloom effects",

    # Default configuration values
    "defaults": {
        # Audio Settings
        "sensitivity": 1.4,  # Audio responsiveness: 0.5 to 5.0
        "use_log_scale": False,  # true = logarithmic, false = linear

        # Visual Settings
        "segment_size": 1.0,  # Segment size multiplier: 0.5 to 2.0
        "brightness": 3.5,  # Overall brightness: 1.0 to 8.0
        "bloom_size": 4.5,  # Bloom/glow size: 1.0 to 15.0
        "bloom_intensity": 0.7,  # Bloom intensity: 0.1 to 2.0
        "bloom_falloff": 2.0,  # Bloom falloff rate: 1.0 to 4.0
        "segment_gap": 0.4,  # Gap between segments: 0.0 to 3.0 (0.0 smallest gap)
        "inner_radius": 0.05,  # Inner radius of the circle: 0.01 to 0.2
        "scale": 1.5,  # Overall scale of the visualizer: 0.5 to 3.0

        # Color Settings
        "base_color": "#8000ff",  # Base segment color (purple)
        "hot_color": "#00ccff",  # High amplitude color (bright blue)

        # Text Settings
        "show_text": True,
        "text_size": "medium",
        "text_color": "#ffffff",
        "glow_effect": "black",
        "glow_blur_radius": 3,

        # Background Settings
        "background_shader": "",

        # Video Settings
        "fps": 30,
        "height": 720,
        "duration": None,

        # Audio Processing
        "n_bars": 64,  # Number of frequency bands
        "amplitude_scale": 1.0,
        "decay_speed": 0.2,
        "attack_speed": 1.0,
        "noise_gate": 0.03,
    },

    # Form field definitions
    "form_fields": [
        {
            "name": "sensitivity",
            "label": "Audio Sensitivity",
            "type": "range",
            "min": 0.5,
            "max": 5.0,
            "step": 0.1,
            "tooltip": "How responsive the visualizer is to audio changes"
        },
        {
            "name": "use_log_scale",
            "label": "Use Logarithmic Scale",
            "type": "checkbox",
            "tooltip": "Use logarithmic scaling for frequency response"
        },
        {
            "name": "segment_size",
            "label": "Segment Size",
            "type": "range",
            "min": 0.5,
            "max": 2.0,
            "step": 0.1,
            "tooltip": "Size multiplier for individual segments"
        },
        {
            "name": "brightness",
            "label": "Brightness",
            "type": "range",
            "min": 1.0,
            "max": 8.0,
            "step": 0.1,
            "tooltip": "Overall brightness of the visualization"
        },
        {
            "name": "bloom_size",
            "label": "Bloom Size",
            "type": "range",
            "min": 1.0,
            "max": 15.0,
            "step": 0.1,
            "tooltip": "Size of the glow/bloom effect around segments"
        },
        {
            "name": "bloom_intensity",
            "label": "Bloom Intensity",
            "type": "range",
            "min": 0.1,
            "max": 2.0,
            "step": 0.1,
            "tooltip": "Intensity of the glow/bloom effect"
        },
        {
            "name": "bloom_falloff",
            "label": "Bloom Falloff",
            "type": "range",
            "min": 1.0,
            "max": 4.0,
            "step": 0.1,
            "tooltip": "How quickly the bloom effect fades"
        },
        {
            "name": "segment_gap",
            "label": "Segment Gap",
            "type": "range",
            "min": 0.0,
            "max": 3.0,
            "step": 0.1,
            "tooltip": "Gap between segments (0.0 = smallest gap)"
        },
        {
            "name": "inner_radius",
            "label": "Inner Radius",
            "type": "range",
            "min": 0.01,
            "max": 0.2,
            "step": 0.01,
            "tooltip": "Size of the inner circle (smaller = bigger hole in center)"
        },
        {
            "name": "scale",
            "label": "Overall Scale",
            "type": "range",
            "min": 0.5,
            "max": 3.0,
            "step": 0.1,
            "tooltip": "Overall size of the visualizer (larger = bigger circle)"
        },
        {
            "name": "base_color",
            "label": "Base Color",
            "type": "color",
            "tooltip": "Base color for segments"
        },
        {
            "name": "hot_color",
            "label": "High Amplitude Color",
            "type": "color",
            "tooltip": "Color for high amplitude segments"
        },
        {
            "name": "show_text",
            "label": "Show Text",
            "type": "checkbox",
            "tooltip": "Display artist name and track title"
        },
        {
            "name": "text_size",
            "label": "Text Size",
            "type": "select",
            "options": [
                {"value": "small", "label": "Small"},
                {"value": "medium", "label": "Medium"},
                {"value": "large", "label": "Large"}
            ],
            "tooltip": "Size of the text overlay"
        },
        {
            "name": "text_color",
            "label": "Text Color",
            "type": "color",
            "tooltip": "Color of the text overlay"
        },
        {
            "name": "glow_effect",
            "label": "Text Glow Effect",
            "type": "select",
            "options": [
                {"value": "none", "label": "None"},
                {"value": "black", "label": "Black Glow"},
                {"value": "white", "label": "White Glow"}
            ],
            "tooltip": "Glow effect around text for better visibility"
        },
        {
            "name": "glow_blur_radius",
            "label": "Glow Blur Radius",
            "type": "range",
            "min": 1,
            "max": 10,
            "step": 1,
            "tooltip": "Blur radius for the text glow effect"
        }
    ]
}
