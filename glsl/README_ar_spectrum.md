# Classic Spectrum Analyzer Shader

This shader creates a classic bar-style audio spectrum analyzer visualization that reacts to music. It features a clean, modern design with peak indicators and smooth color gradients.

## Features

- Classic bar-style spectrum analyzer with 24 frequency bands
- Each bar has 20 segments that light up based on audio amplitude
- Peak indicators that show the highest recent level for each frequency band
- Smooth color gradient from dark teal at the bottom to bright cyan at the top
- Customizable colors, sensitivity, and layout

## Technical Details

This shader consists of two parts:
1. **Main Shader (ar_spectrum.glsl)**: Renders the visual spectrum analyzer display
2. **Buffer Shader (ar_spectrum_buffer.glsl)**: Processes audio data and maintains peak values

The buffer shader processes the audio data from iChannel0 and stores peak values in a small texture (24x1 pixels). The main shader reads both the current audio data and the peak values to render the visualization.

### Key Parameters

#### Layout
- `NUM_BARS`: Number of frequency bands (default: 24)
- `SEGMENTS_PER_BAR`: Number of segments in each bar (default: 20)
- `ANALYZER_BOTTOM_Y`, `ANALYZER_HEIGHT`: Vertical position and size
- `ANALYZER_LEFT_X`, `ANALYZER_WIDTH_X`: Horizontal position and size
- `BORDER_SIZE`: Size of borders between segments (default: 0.2)

#### Audio Processing
- `OVERALL_MASTER_GAIN`: Overall sensitivity (default: 1.8)
- `FREQ_GAIN_MIN_MULT`, `FREQ_GAIN_MAX_MULT`: Frequency-specific gain multipliers
- `FREQ_GAIN_CURVE_POWER`: Controls the curve of frequency gain (default: 0.4)
- `BAR_HEIGHT_POWER`: Controls the response curve of bar heights (default: 1.0)
- `AMPLITUDE_COMPRESSION_POWER`: Controls audio compression (default: 1.0)
- `PEAK_FALLOFF_RATE`: Rate at which peaks fall (default: 0.4)

#### Colors
- `COLOR_LIT_DARK`: Color for lit segments at the bottom (default: vec3(0.0, 0.4, 0.4))
- `COLOR_LIT_BRIGHT`: Color for lit segments at the top (default: vec3(0.2, 1.0, 1.0))
- `COLOR_UNLIT`: Color for unlit segments (default: vec3(0.0, 0.08, 0.08))
- `COLOR_BORDER`: Color for borders (default: vec3(0.0, 0.0, 0.0))
- `COLOR_PEAK`: Color for peak indicators (default: vec3(0.0, 0.8, 0.8))
- `LIT_BRIGHTNESS_MULTIPLIER`: Brightness multiplier for lit segments (default: 1.2)

## Usage

This shader is designed to be used with the Audio Reactive Visualizer in the Video Spectrum Analyzer application. To use it:

1. Go to the main application page
2. Enable developer mode by adding `?dev=true` to the URL
3. Select "Audioreactive Shader" from the visualizer options
4. Upload your audio file
5. Select "Classic Spectrum Analyzer" from the shader dropdown
6. Adjust other settings as desired
7. Click "Generate Visualization"

## Customization

You can customize the shader by modifying the constants at the top of the ar_spectrum.glsl file. For example:

- To change the colors, modify the `COLOR_*` constants
- To adjust sensitivity, modify the `OVERALL_MASTER_GAIN` constant
- To change the layout, modify the `ANALYZER_*` constants

## Credits

Created by Marco van Hylckama Vlieg
Twitter/X: [@AIandDesign](https://x.com/AIandDesign)
