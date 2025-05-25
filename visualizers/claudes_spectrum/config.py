"""
Configuration for Claude's Spectrum Visualizer.
"""

CLAUDES_SPECTRUM_CONFIG = {
    "name": "Claude's Spectrum Visualizer",
    "description": "A horizontal spectrum analyzer with configurable bars, bloom effects, and color schemes",

    # Default configuration values
    "defaults": {
        # Visual Settings
        "bar_width": 10,  # Width of each bar in pixels (at 1280px width): 3 to 25
        "bar_spacing": 18,  # Spacing between bars in pixels (at 1280px width): 5 to 40
        "max_bar_height": 0.7,  # Maximum bar height: 0.3 to 1.0
        "num_bars": 48,  # Number of frequency bars: 24 to 128
        "waveform_width": 0.8,  # Total width of waveform: 0.5 to 1.0

        # Bloom/Glow Settings
        "bloom_size": 8.0,  # Bloom/glow size: 5.0 to 50.0
        "bloom_intensity": 0.3,  # Bloom intensity: 0.1 to 2.0
        "bloom_falloff": 2.0,  # Bloom falloff rate: 0.5 to 4.0

        # Color Scheme Settings
        "color_scheme": 0,  # 0=current, 1=single, 2=rainbow, 3=purple, 4=green, 5=blue
        "single_color": "#ffffff",  # White for single color mode
        "color_low": "#ff3319",  # Red/Orange for low frequencies
        "color_mid": "#ffff33",  # Yellow for mid frequencies
        "color_high": "#3366ff",  # Blue for high frequencies

        # Scaling Settings
        "use_logarithmic_scale": True,  # Use logarithmic frequency scaling
        "log_scale_factor": 0.5,  # Logarithmic scale factor: 0.1 to 1.0

        # Center Line Settings
        "show_center_line": True,  # Show horizontal center line
        "center_line_thickness": 4,  # Thickness of center line in pixels: 1 to 10
        "center_line_overhang": 0.05,  # Line extension beyond bars: 0.0 to 0.1
        "center_line_color": "#999999",  # Gray color for center line

        # Audio Settings
        "sensitivity": 1.0,  # Audio responsiveness: 0.5 to 3.0

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
        "n_bars": 64,  # Number of frequency bands for analysis
        "amplitude_scale": 1.0,
        "decay_speed": 0.2,
        "attack_speed": 1.0,
        "noise_gate": 0.03,
    },

    # Form field definitions
    "form_fields": [
        {
            "name": "bar_width",
            "label": "Bar Width (pixels)",
            "type": "range",
            "min": 3,
            "max": 25,
            "step": 1,
            "tooltip": "Width of each frequency bar in pixels (based on 1280px width, scales for other resolutions)"
        },
        {
            "name": "bar_spacing",
            "label": "Bar Spacing (pixels)",
            "type": "range",
            "min": 5,
            "max": 40,
            "step": 1,
            "tooltip": "Spacing between frequency bars in pixels (based on 1280px width, scales for other resolutions)"
        },
        {
            "name": "max_bar_height",
            "label": "Maximum Bar Height",
            "type": "range",
            "min": 0.3,
            "max": 1.0,
            "step": 0.05,
            "tooltip": "Maximum height that bars can reach"
        },
        {
            "name": "num_bars",
            "label": "Number of Bars",
            "type": "range",
            "min": 24,
            "max": 128,
            "step": 4,
            "tooltip": "Number of frequency bars to display"
        },
        {
            "name": "waveform_width",
            "label": "Waveform Width",
            "type": "range",
            "min": 0.5,
            "max": 1.0,
            "step": 0.05,
            "tooltip": "Total width of the spectrum display"
        },
        {
            "name": "bloom_size",
            "label": "Bloom Size",
            "type": "range",
            "min": 5.0,
            "max": 50.0,
            "step": 1.0,
            "tooltip": "Size of the glow/bloom effect around bars"
        },
        {
            "name": "bloom_intensity",
            "label": "Bloom Intensity",
            "type": "range",
            "min": 0.1,
            "max": 2.0,
            "step": 0.05,
            "tooltip": "Intensity of the glow/bloom effect"
        },
        {
            "name": "bloom_falloff",
            "label": "Bloom Falloff",
            "type": "range",
            "min": 0.5,
            "max": 4.0,
            "step": 0.1,
            "tooltip": "How quickly the bloom effect fades"
        },
        {
            "name": "color_scheme",
            "label": "Color Scheme",
            "type": "select",
            "options": [
                {"value": 0, "label": "Gradient (Red-Yellow-Blue)"},
                {"value": 1, "label": "Single Color"},
                {"value": 2, "label": "Rainbow"},
                {"value": 3, "label": "Purple Gradient"},
                {"value": 4, "label": "Green Gradient"},
                {"value": 5, "label": "Blue Gradient"}
            ],
            "tooltip": "Color scheme for the frequency bars"
        },
        {
            "name": "single_color",
            "label": "Single Color",
            "type": "color",
            "tooltip": "Color to use when Single Color scheme is selected"
        },
        {
            "name": "color_low",
            "label": "Low Frequency Color",
            "type": "color",
            "tooltip": "Color for low frequencies in gradient mode"
        },
        {
            "name": "color_mid",
            "label": "Mid Frequency Color",
            "type": "color",
            "tooltip": "Color for mid frequencies in gradient mode"
        },
        {
            "name": "color_high",
            "label": "High Frequency Color",
            "type": "color",
            "tooltip": "Color for high frequencies in gradient mode"
        },
        {
            "name": "use_logarithmic_scale",
            "label": "Use Logarithmic Scale",
            "type": "checkbox",
            "tooltip": "Use logarithmic scaling for frequency response"
        },
        {
            "name": "log_scale_factor",
            "label": "Log Scale Factor",
            "type": "range",
            "min": 0.1,
            "max": 1.0,
            "step": 0.05,
            "tooltip": "Logarithmic scale factor (higher = more emphasis on low frequencies)"
        },
        {
            "name": "show_center_line",
            "label": "Show Center Line",
            "type": "checkbox",
            "tooltip": "Display horizontal center line"
        },
        {
            "name": "center_line_thickness",
            "label": "Center Line Thickness (pixels)",
            "type": "range",
            "min": 1,
            "max": 10,
            "step": 1,
            "tooltip": "Thickness of the horizontal center line in pixels (based on 720px height, scales for other resolutions)"
        },
        {
            "name": "center_line_overhang",
            "label": "Center Line Overhang",
            "type": "range",
            "min": 0.0,
            "max": 0.1,
            "step": 0.01,
            "tooltip": "How much the center line extends beyond the bars"
        },
        {
            "name": "center_line_color",
            "label": "Center Line Color",
            "type": "color",
            "tooltip": "Color of the horizontal center line"
        },
        {
            "name": "sensitivity",
            "label": "Audio Sensitivity",
            "type": "range",
            "min": 0.5,
            "max": 3.0,
            "step": 0.1,
            "tooltip": "How responsive the visualizer is to audio changes"
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
