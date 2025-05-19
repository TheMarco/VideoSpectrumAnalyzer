"""
Test script for the Circular Spectrum visualizer.
This script creates a simple test visualization to check if all bars are moving.
"""
import os
import sys
import numpy as np
from PIL import Image
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the visualizer
from visualizers.circular_spectrum.visualizer import CircularSpectrumVisualizer
from visualizers.circular_spectrum.gl_renderer import SimpleGLCircularRenderer

def generate_test_audio_data(num_frames=100, num_bars=36):
    """
    Generate test audio data with varying amplitudes for all bars.

    Returns:
        numpy.ndarray: Test audio data with shape (num_bars, num_frames)
    """
    # Create a time array
    t = np.linspace(0, 10, num_frames)

    # Create an array to hold the audio data
    audio_data = np.zeros((num_bars, num_frames))

    # Generate different frequency sine waves for each bar
    for i in range(num_bars):
        # Use different frequencies and phases for each bar
        freq = 0.5 + i * 0.1
        phase = i * 0.2

        # Generate the sine wave
        audio_data[i, :] = 0.5 + 0.5 * np.sin(2 * np.pi * freq * t + phase)

    return audio_data

def generate_sequential_test_data(num_frames=36, num_bars=36):
    """
    Generate test data where each bar lights up sequentially.
    This helps identify if all bars are working.

    Returns:
        numpy.ndarray: Test audio data with shape (num_bars, num_frames)
    """
    # Create an array to hold the audio data
    audio_data = np.zeros((num_frames, num_bars))

    # For each frame, light up one bar fully
    for i in range(min(num_frames, num_bars)):
        # Set the i-th bar to 1.0 for the i-th frame
        audio_data[i, i] = 1.0

        # Print the data for debugging
        print(f"Frame {i}: Setting bar {i} to 1.0")

    return audio_data

def generate_amplitude_test_data(num_frames=36, num_bars=36):
    """
    Generate test data with varying amplitudes for all bars.
    Each frame has all bars lit with different amplitudes.

    Returns:
        numpy.ndarray: Test audio data with shape (num_frames, num_bars)
    """
    # Create an array to hold the audio data
    audio_data = np.zeros((num_frames, num_bars))

    # For each frame, set all bars to different amplitudes
    for i in range(num_frames):
        # Set all bars to different amplitudes based on their index
        for j in range(num_bars):
            # Calculate amplitude: 0.2, 0.4, 0.6, 0.8, 1.0, 0.8, 0.6, 0.4, 0.2, ...
            amplitude = 0.2 + 0.2 * (j % 5)
            audio_data[i, j] = amplitude

    # For the first few frames, set specific patterns to test
    if num_frames >= 5:
        # Frame 0: All bars at full amplitude
        audio_data[0, :] = 1.0

        # Frame 1: Alternating bars (even indices at full amplitude)
        audio_data[1, ::2] = 1.0
        audio_data[1, 1::2] = 0.0

        # Frame 2: Alternating bars (odd indices at full amplitude)
        audio_data[2, ::2] = 0.0
        audio_data[2, 1::2] = 1.0

        # Frame 3: Gradient from 0.0 to 1.0
        audio_data[3, :] = np.linspace(0.0, 1.0, num_bars)

        # Frame 4: Gradient from 1.0 to 0.0
        audio_data[4, :] = np.linspace(1.0, 0.0, num_bars)

    return audio_data

def test_circular_spectrum():
    """
    Test the Circular Spectrum visualizer with generated audio data.
    """
    print("Testing Circular Spectrum visualizer...")

    # Create a configuration
    config = {
        "num_bars": 36,
        "segments_per_bar": 15,
        "inner_radius": 0.20,
        "outer_radius": 0.40,
        "overall_master_gain": 1.0,
        "freq_gain_min_mult": 0.4,
        "freq_gain_max_mult": 1.8,
        "freq_gain_curve_power": 0.6,
        "bar_height_power": 1.1,
        "amplitude_compression_power": 1.0,
        "font_size": 24,
        "title_color": "#FFFFFF",
        "artist_color": "#FFFFFF",
        "text_padding": 20
    }

    # Create a visualizer
    visualizer = CircularSpectrumVisualizer()

    # Initialize the renderer
    width, height = 800, 600
    renderer = visualizer.initialize_renderer(width, height, config)

    # Generate test audio data
    num_frames = 36

    # Choose which test data to use
    test_type = "sequential"  # Options: "sequential", "amplitude", "sine"

    if test_type == "sequential":
        # Use sequential test data to check if all bars are working
        audio_data = generate_sequential_test_data(num_frames, config["num_bars"])
    elif test_type == "amplitude":
        # Use amplitude test data to check if all bars show different amplitudes
        audio_data = generate_amplitude_test_data(num_frames, config["num_bars"])
    else:  # "sine"
        # Use sine wave test data for a more realistic visualization
        audio_data = generate_test_audio_data(num_frames, config["num_bars"])

    # Create a directory for test output
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)

    # Render frames
    print(f"Rendering {num_frames} test frames...")
    for i in range(num_frames):
        # Get audio data for this frame
        frame_audio_data = audio_data[i]

        # Print the frame audio data for debugging
        print(f"Frame {i} audio data: {frame_audio_data}")

        # Create frame data dictionary
        frame_data = {"raw_audio_samples": frame_audio_data}

        # Create metadata
        metadata = {
            "artist_name": "Test Artist",
            "track_title": "Test Track"
        }

        # Print the shape of the audio data for debugging
        print(f"Audio data shape: {frame_audio_data.shape}")

        # Render the frame
        frame = visualizer.render_frame(renderer, frame_data, None, metadata)

        # Save the frame
        frame_path = os.path.join(output_dir, f"frame_{i:03d}.png")
        frame.save(frame_path)

        print(f"Rendered frame {i+1}/{num_frames}")

    print(f"Test frames saved to {output_dir}")
    print("Test completed successfully!")

if __name__ == "__main__":
    test_circular_spectrum()
