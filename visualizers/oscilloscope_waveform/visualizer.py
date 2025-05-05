# visualizer.py for oscilloscope_waveform visualizer

import numpy as np
from core.base_visualizer import BaseVisualizer
from modules.audio_processor import load_audio
from modules.media_handler import load_background_media, process_video_frame, load_fonts
from modules.ffmpeg_handler import (
    setup_ffmpeg_process,
    write_frame_to_ffmpeg,
    finalize_ffmpeg_process,
    add_audio_to_video,
    cleanup_temp_files
)
from .config import process_config
from .renderer import OscilloscopeWaveformRenderer

class OscilloscopeWaveformVisualizer(BaseVisualizer):
    name = "OscilloscopeWaveformVisualizer"  # This must match the class name for proper registration
    display_name = "Oscilloscope Waveform"   # This is what will be shown to users
    description = "Displays a raw audio waveform similar to an oscilloscope."
    thumbnail = "static/images/thumbnails/oscilloscope_waveform.jpg"

    def __init__(self):
        super().__init__()
        self.renderer = None # Initialize in initialize_renderer
        self.audio_samples = None
        self.sample_rate = None
        self.total_frames = None
        self.samples_per_frame = None

    def process_config(self, config=None):
        """
        Process and validate the configuration for the oscilloscope visualizer.
        """
        return process_config(config if config is not None else {})

    def initialize_renderer(self, width, height, config):
        """
        Initialize the OscilloscopeWaveformRenderer.
        """
        # Load fonts with the text size from config
        text_size = config.get("text_size", "large")
        print(f"Initializing renderer with text_size: {text_size}")
        artist_font, title_font = load_fonts(text_size=text_size)

        # Initialize renderer with fonts
        self.renderer = OscilloscopeWaveformRenderer(width, height, config, artist_font, title_font)
        return self.renderer

    def update_frame_data(self, frame_data, frame_idx, conf):
        """
        Update frame data for the current frame based on raw audio samples.
        """
        if self.audio_samples is None or self.total_frames is None or self.samples_per_frame is None:
             raise ValueError("Audio data not loaded before updating frame data.")

        # Get audio data for the current frame
        # Use a slightly larger window to capture more audio data for a better waveform
        # This helps ensure we have enough data points for a good visualization
        window_size_factor = 1.5  # Use 1.5x the normal frame size for better waveform display

        # Calculate start and end samples with the larger window
        center_sample = int((frame_idx + 0.5) * self.samples_per_frame)  # Center of the frame
        half_window = int(self.samples_per_frame * window_size_factor / 2)

        start_sample = max(0, center_sample - half_window)
        end_sample = min(len(self.audio_samples), center_sample + half_window)

        # Get the audio data for this frame
        frame_audio_data = self.audio_samples[start_sample:end_sample]

        # Ensure we have enough data points for a good visualization
        if len(frame_audio_data) < 100 and len(self.audio_samples) > 100:
            # If we have too few points, use a minimum window size
            start_sample = max(0, center_sample - 50)
            end_sample = min(len(self.audio_samples), center_sample + 50)
            frame_audio_data = self.audio_samples[start_sample:end_sample]

        # For oscilloscope, the 'frame_data' will primarily contain the raw audio samples for the frame
        frame_data["raw_audio_samples"] = frame_audio_data

        # The base class's create_visualization expects certain keys in frame_data
        # We'll provide dummy data for the keys not relevant to the oscilloscope
        frame_data["mel_spec_norm"] = np.zeros((conf.get("n_bars", 40), 1)) # Dummy data
        frame_data["normalized_frame_energy"] = np.array([0.0]) # Dummy data
        frame_data["dynamic_thresholds"] = np.zeros((conf.get("n_bars", 40),)) # Dummy data
        frame_data["smoothed_spectrum"] = np.zeros((conf.get("n_bars", 40),)) # Dummy data
        frame_data["peak_values"] = np.zeros((conf.get("n_bars", 40),)) # Dummy data
        frame_data["peak_hold_counters"] = np.zeros((conf.get("n_bars", 40),), dtype=int) # Dummy data


    def render_frame(self, renderer, frame_data, background_image, metadata):
        """
        Render a single frame using the OscilloscopeWaveformRenderer.
        """
        if "raw_audio_samples" not in frame_data:
             raise ValueError("Raw audio samples not found in frame_data.")

        frame_audio_data = frame_data["raw_audio_samples"]

        # The renderer expects the raw audio data and the background image
        frame_image = renderer.render_frame(
            frame_audio_data,
            background_image,
            metadata # Pass metadata if needed by the renderer
        )
        return frame_image

    # Override create_visualization to load raw audio samples and calculate frame details
    def create_visualization(
        self,
        audio_file,
        output_file="output.mp4",
        background_image_path=None,
        background_video_path=None,
        background_shader_path=None,
        artist_name="Artist Name",
        track_title="Track Title",
        duration=None,
        fps=30,
        height=720,
        width=1280,
        config=None,
        progress_callback=None,
    ):
        """
        Create a visualization for an audio file, tailored for the oscilloscope.
        """
        # Process configuration
        conf = self.process_config(config)

        # Load Audio - we need raw samples for oscilloscope
        self.audio_samples, self.sample_rate, audio_duration = load_audio(audio_file, duration=duration, progress_callback=progress_callback)
        if self.audio_samples is None:
            raise Exception("Could not load audio file.")

        # Calculate total number of frames and samples per frame
        self.total_frames = int((duration if duration is not None else audio_duration) * fps)
        self.samples_per_frame = len(self.audio_samples) / self.total_frames

        # Call the base class's create_visualization to handle the rest of the process
        # Pass the loaded audio samples and calculated frame details
        return super().create_visualization(
            audio_file=audio_file, # Pass original audio file for audio merging
            output_file=output_file,
            background_image_path=background_image_path,
            background_video_path=background_video_path,
            background_shader_path=background_shader_path,
            artist_name=artist_name,
            track_title=track_title,
            duration=duration, # Pass duration to base class
            fps=fps,
            height=height,
            width=width,
            config=conf, # Pass processed config
            progress_callback=progress_callback,
        )


    def get_config_template(self):
        """Returns the path to the visualizer's configuration template."""
        return "oscilloscope_waveform_form.html"

    def get_js_module(self):
        """Returns the path to the visualizer's JavaScript module."""
        return "static/js/oscilloscope_waveform_form.js"

# Registration is handled by the registry discovery process