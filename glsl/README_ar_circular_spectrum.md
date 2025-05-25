# Circular Spectrum Analyzer Shader

This shader creates a circular audio spectrum analyzer visualization that reacts to music. It's designed to mimic the style of 1990s audio visualizers with a modern touch. The visualization includes audio in the final video output.

## Features

- Circular layout with bars arranged in a ring
- Each bar has multiple segments that light up based on audio amplitude
- Constant arc width for all segments regardless of radius
- Innermost segment of each bar is always lit for better visual appeal
- Customizable colors and sensitivity

## Usage

This shader is designed to be used with the Audio Reactive Visualizer in the Video Spectrum Analyzer application. To use it:

1. Go to the main application page
2. Enable developer mode by adding `?dev=true` to the URL
3. Select "Audioreactive Shader" from the visualizer options
4. Upload your audio file
5. Select "Circular Spectrum Analyzer" from the shader dropdown
6. Adjust other settings as desired
7. Click "Generate Visualization"

## Technical Details

The shader uses a polar coordinate system to create the circular layout. It maps audio frequency data from the audio texture (iChannel0) to the different bars around the circle. The amplitude of each frequency band determines how many segments of each bar are lit.

Key parameters that can be adjusted in the shader code:

- `NUM_BARS`: Number of bars around the circle (default: 36)
- `SEGMENTS_PER_BAR`: Number of segments in each bar (default: 15)
- `INNER_RADIUS`: Inner radius of the analyzer ring (default: 0.20)
- `OUTER_RADIUS`: Outer radius of the analyzer ring (default: 0.40)
- `BORDER_SIZE`: Size of borders between segments (default: 0.08)
- `COLOR_LIT_DARK`: Color for lit segments (inner) (default: vec3(0.4, 0.4, 0.4))
- `COLOR_LIT_BRIGHT`: Color for lit segments (outer) (default: vec3(1.0, 1.0, 1.0))
- `COLOR_UNLIT`: Color for unlit segments (default: vec3(0.08, 0.08, 0.08))
- `COLOR_BORDER`: Color for borders (default: vec3(0.0, 0.0, 0.0))

## Credits

Created by Marco van Hylckama Vlieg
Twitter/X: [@AIandDesign](https://x.com/AIandDesign)

Based on a variation of the shader at https://www.shadertoy.com/view/wfdGW8
