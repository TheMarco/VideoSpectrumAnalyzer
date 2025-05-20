"""
Test script for the Circular Equalizer visualizer.
This script creates a simple test visualization to debug the audio data processing.
"""
import os
import sys
import numpy as np
from PIL import Image
import moderngl
import math
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the patched renderer
from visualizers.circular_equalizer.test_patched_renderer import PatchedGLCircularEqualizerRenderer

def create_test_spectrum(n_bars, pattern='sine', frequency=1.0, offset=0.0, amplitude=1.0):
    """
    Create a test spectrum with a specific pattern.

    Args:
        n_bars (int): Number of bars in the spectrum
        pattern (str): Pattern type ('sine', 'ramp', 'constant', 'alternating')
        frequency (float): Frequency of the pattern (for sine)
        offset (float): Offset/phase of the pattern
        amplitude (float): Maximum amplitude

    Returns:
        numpy.ndarray: Test spectrum data
    """
    x = np.arange(n_bars)

    if pattern == 'sine':
        # Sine wave pattern
        spectrum = amplitude * 0.5 * (1 + np.sin(2 * np.pi * frequency * x / n_bars + offset))
    elif pattern == 'ramp':
        # Linear ramp
        spectrum = amplitude * x / (n_bars - 1)
    elif pattern == 'constant':
        # Constant value
        spectrum = np.ones(n_bars) * amplitude
    elif pattern == 'alternating':
        # Alternating values
        spectrum = np.zeros(n_bars)
        spectrum[::2] = amplitude
    elif pattern == 'single':
        # Single bar
        spectrum = np.zeros(n_bars)
        bar_idx = int(offset) % n_bars
        spectrum[bar_idx] = amplitude
    elif pattern == 'silence':
        # Complete silence - all zeros
        spectrum = np.zeros(n_bars)
    else:
        # Default to sine
        spectrum = amplitude * 0.5 * (1 + np.sin(2 * np.pi * frequency * x / n_bars + offset))

    return spectrum

def debug_spectrum_processing(renderer, spectrum):
    """
    Debug the spectrum processing by printing detailed information about each bar.

    Args:
        renderer (GLCircularEqualizerRenderer): The renderer instance
        spectrum (numpy.ndarray): Input spectrum data

    Returns:
        list: Processed amplitudes for each bar
    """
    print("\n=== Spectrum Processing Debug ===")
    print(f"Input spectrum shape: {spectrum.shape}")
    print(f"Input spectrum min: {np.min(spectrum):.6f}, max: {np.max(spectrum):.6f}")

    # Print a few sample values
    sample_indices = np.linspace(0, len(spectrum)-1, min(10, len(spectrum)), dtype=int)
    sample_values = [f"{i}: {spectrum[i]:.6f}" for i in sample_indices]
    print(f"Sample input values: {', '.join(sample_values)}")

    # Track processed amplitudes
    processed_amplitudes = []

    # Process each bar similar to how the renderer does it
    for i in range(renderer.n_bars):
        # Get the spectrum index for this bar
        spectrum_idx = min(i, len(spectrum) - 1)

        # Get the raw amplitude
        raw_amplitude = spectrum[spectrum_idx]

        # Apply noise gate
        noise_gate = 0.01
        raw_amplitude = max(0.0, raw_amplitude - noise_gate)

        # Apply simplified processing to match the updated renderer
        processed_amplitude = pow(raw_amplitude, renderer.amplitude_compression_power)
        amplitude_after_gain = processed_amplitude * renderer.overall_master_gain
        final_amplitude = pow(amplitude_after_gain, renderer.bar_height_power)

        # Apply the same noise gate as in the renderer
        if raw_amplitude < 0.002:
            final_amplitude = 0.0

        # Apply consistent gain to ensure all bars have the same maximum height
        if final_amplitude > 0.0:
            final_amplitude = min(1.0, final_amplitude * 1.2)

        # Clamp the final amplitude
        final_amplitude = max(0.0, min(1.0, final_amplitude))

        # Store the processed amplitude
        processed_amplitudes.append(final_amplitude)

        # Print detailed information for each bar
        if i < 5 or i > renderer.n_bars - 6 or i % 10 == 0:
            print(f"Bar {i:2d}: raw={raw_amplitude:.6f}, processed={processed_amplitude:.6f}, "
                  f"after_gain={amplitude_after_gain:.6f}, final={final_amplitude:.6f}")

    return processed_amplitudes

def test_circular_equalizer():
    """
    Test the Circular Equalizer visualizer with generated audio data.
    """
    print("Testing Circular Equalizer visualizer...")

    # Create output directory for test frames
    output_dir = os.path.join(os.path.dirname(__file__), "test_output")
    os.makedirs(output_dir, exist_ok=True)

    # Configuration for the renderer
    width, height = 800, 600
    config = {
        "n_bars": 36,
        "segments_per_bar": 15,
        "circle_diameter": 400,
        "bar_width": 8,
        "bar_gap": 2,
        "segment_height": 10,
        "segment_gap": 1,
        "corner_radius": 2,
        "always_on_inner": True,
        "overall_master_gain": 1.0,
        "freq_gain_min_mult": 0.4,
        "freq_gain_max_mult": 1.8,
        "freq_gain_curve_power": 0.6,
        "bar_height_power": 1.1,
        "amplitude_compression_power": 1.0,
        "freq_pos_power": 1.7,
    }

    # Create a ModernGL context
    ctx = moderngl.create_standalone_context()

    # Create the renderer
    renderer = PatchedGLCircularEqualizerRenderer(ctx, width, height, config)

    # Test patterns to try
    test_patterns = [
        ('constant', 0, 0, 1.0),  # Constant value
        ('sine', 1.0, 0, 1.0),    # Sine wave
        ('ramp', 0, 0, 1.0),      # Linear ramp
        ('alternating', 0, 0, 1.0),  # Alternating values
        ('silence', 0, 0, 0.0)  # Complete silence (all zeros)
    ]

    # Generate and render frames for each test pattern
    for pattern, freq, offset, amplitude in test_patterns:
        print(f"\n=== Testing pattern: {pattern} ===")

        # Create test spectrum
        test_spectrum = create_test_spectrum(
            config["n_bars"],
            pattern=pattern,
            frequency=freq,
            offset=offset,
            amplitude=amplitude
        )

        # Debug the spectrum processing
        processed_amplitudes = debug_spectrum_processing(renderer, test_spectrum)

        try:
            # Create a framebuffer to render into
            texture = ctx.texture((width, height), 4)
            fbo = ctx.framebuffer(texture)

            # Bind the framebuffer (different API in standalone context)
            fbo.use()

            # Render a frame with the test spectrum
            # Pass the framebuffer directly to the render method
            renderer.render_frame(test_spectrum)

            # Read the pixels from the framebuffer
            frame_data = fbo.read(components=4, dtype='f1')

            # Convert the frame to a PIL Image
            frame_image = Image.frombytes('RGBA', (width, height), frame_data)
        except Exception as e:
            print(f"Error rendering frame: {e}")
            # Create a blank image with text showing the error
            frame_image = Image.new('RGBA', (width, height), (0, 0, 0, 255))
            # We'll still save the image to show we tried

        # Save the frame
        frame_path = os.path.join(output_dir, f"test_{pattern}.png")
        frame_image.save(frame_path)

        print(f"Saved test frame to {frame_path}")

    # Test individual bars to identify problematic ones
    print("\n=== Testing individual bars ===")
    for i in range(config["n_bars"]):
        # Create a spectrum with only one bar active
        test_spectrum = create_test_spectrum(
            config["n_bars"],
            pattern='single',
            offset=i,
            amplitude=1.0
        )

        # Debug the spectrum processing for this bar
        processed_amplitudes = debug_spectrum_processing(renderer, test_spectrum)

        try:
            # Create a framebuffer to render into
            texture = ctx.texture((width, height), 4)
            fbo = ctx.framebuffer(texture)

            # Bind the framebuffer (different API in standalone context)
            fbo.use()

            # Render a frame with the test spectrum
            # Pass the framebuffer directly to the render method
            renderer.render_frame(test_spectrum)

            # Read the pixels from the framebuffer
            frame_data = fbo.read(components=4, dtype='f1')

            # Convert the frame to a PIL Image
            frame_image = Image.frombytes('RGBA', (width, height), frame_data)
        except Exception as e:
            print(f"Error rendering frame for bar {i}: {e}")
            # Create a blank image with text showing the error
            frame_image = Image.new('RGBA', (width, height), (0, 0, 0, 255))
            # We'll still save the image to show we tried

        # Save the frame
        frame_path = os.path.join(output_dir, f"test_bar_{i:02d}.png")
        frame_image.save(frame_path)

        print(f"Tested bar {i}")

    # Clean up
    renderer.cleanup()
    ctx.release()

    print("Test completed successfully!")

if __name__ == "__main__":
    test_circular_equalizer()
