# visualizer.py for oscilloscope_waveform visualizer

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
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
from .simple_gl_renderer import SimpleGLOscilloscopeRenderer

class OscilloscopeWaveformVisualizer(BaseVisualizer):
    name = "OscilloscopeWaveformVisualizer"  # This must match the class name for proper registration
    display_name = "Oscilloscope Waveform (GL)"   # This is what will be shown to users
    description = "Displays a raw audio waveform similar to an oscilloscope using GL rendering."
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
        Initialize the GL renderer for the oscilloscope waveform and the PIL renderer for text.
        """
        # Load fonts with the text size from config
        text_size = config.get("text_size", "large")
        print(f"Initializing renderer with text_size: {text_size}")
        artist_font, title_font = load_fonts(text_size=text_size)

        # Initialize PIL renderer for text only
        self.text_renderer = OscilloscopeWaveformRenderer(width, height, config, artist_font, title_font)

        # Initialize GL renderer for the waveform
        try:
            print("Attempting to initialize GL renderer...")
            self.gl_renderer = SimpleGLOscilloscopeRenderer(width, height, config)
            print("GL renderer initialized successfully")
            self.use_gl_renderer = True
        except Exception as e:
            print(f"Error initializing GL renderer: {e}")
            print("Falling back to PIL renderer for waveform")
            self.gl_renderer = None
            self.use_gl_renderer = False
            # Return the PIL renderer as fallback
            return self.text_renderer

        # Return the GL renderer as the primary renderer
        return self.gl_renderer

    def update_frame_data(self, frame_data, frame_idx, conf):
        """
        Update frame data for the current frame based on raw audio samples.
        """
        if self.audio_samples is None or self.total_frames is None or self.samples_per_frame is None:
             raise ValueError("Audio data not loaded before updating frame data.")

        # Get the waveform update rate from config
        # Make sure to convert values to integers to avoid type errors
        try:
            video_fps = int(conf.get("fps", 30))
        except (ValueError, TypeError):
            print("Warning: Invalid fps value, using default 30")
            video_fps = 30

        try:
            waveform_update_rate = int(conf.get("waveform_update_rate", 15))
        except (ValueError, TypeError):
            print("Warning: Invalid waveform_update_rate value, using default 15")
            waveform_update_rate = 15

        # Calculate how many frames to skip between waveform updates
        # For example, if video is 30fps and waveform updates at 15fps, we update every 2 frames
        update_interval = max(1, round(video_fps / waveform_update_rate))

        # Debug print to help diagnose issues
        print(f"Oscilloscope waveform update settings: video_fps={video_fps}, waveform_update_rate={waveform_update_rate}, update_interval={update_interval}")

        # Determine which "update frame" this current frame belongs to
        update_frame_idx = frame_idx // update_interval

        # Get audio data for the current frame
        # Use a more focused window to reduce the "double waveform" effect
        # This helps ensure we're showing a more consistent segment of audio
        window_size_factor = 1.2  # Reduced from 1.5 to get a more focused view

        # Calculate start and end samples based on the update frame index, not the actual frame index
        # This makes the waveform update less frequently than the video frame rate
        center_sample = int((update_frame_idx * update_interval + 0.5) * self.samples_per_frame)  # Center of the update frame
        half_window = int(self.samples_per_frame * window_size_factor / 2)

        # Ensure we're getting a consistent segment of audio
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
        Render a single frame using the GL renderer for the waveform and the PIL renderer for text.
        If GL renderer failed to initialize, fall back to PIL renderer for everything.
        """
        if "raw_audio_samples" not in frame_data:
             raise ValueError("Raw audio samples not found in frame_data.")

        frame_audio_data = frame_data["raw_audio_samples"]

        # Extract metadata
        artist_name = metadata.get("artist_name", "")
        track_title = metadata.get("track_title", "")

        # Debug logging for background image
        if background_image is not None:
            print(f"Oscilloscope visualizer received background image: size={background_image.size}, mode={background_image.mode}")
        else:
            print("Oscilloscope visualizer received no background image")

        # Check if we're using GL renderer or falling back to PIL
        if hasattr(self, 'use_gl_renderer') and self.use_gl_renderer and self.gl_renderer:
            try:
                # Render the waveform using the GL renderer with background image
                print("Using GL renderer for oscilloscope waveform")
                waveform_image = self.gl_renderer.render_frame(frame_audio_data, background_image)

                # Create a blank image for text only
                text_image = Image.new("RGBA", (self.gl_renderer.width, self.gl_renderer.height), (0, 0, 0, 0))

                # Draw text with glow effect
                if (artist_name or track_title) and hasattr(self.text_renderer, '_draw_text'):
                    print(f"Drawing text: artist='{artist_name}', title='{track_title}'")
                    # Create a text glow layer first if glow effect is enabled
                    if self.text_renderer.glow_effect and self.text_renderer.glow_color:
                        text_glow_layer = Image.new("RGBA", (self.gl_renderer.width, self.gl_renderer.height), (0, 0, 0, 0))
                        self.text_renderer._draw_text_mask(text_glow_layer, artist_name, track_title)

                        # Apply blur to the text glow layer
                        text_glow_blurred = text_glow_layer.filter(ImageFilter.GaussianBlur(self.text_renderer.glow_blur_radius))

                        # Composite the text glow layer onto the text image first
                        text_image = Image.alpha_composite(text_image, text_glow_blurred)

                    # Then draw the text on top of the glow
                    self.text_renderer._draw_text(text_image, artist_name, track_title)

                # Composite the text onto the waveform image
                result = Image.alpha_composite(waveform_image, text_image)
                print(f"Final composited result: size={result.size}, mode={result.mode}")

                return result
            except Exception as e:
                print(f"Error rendering with GL renderer: {e}")
                print("Falling back to PIL renderer for this frame")
                import traceback
                traceback.print_exc()
                # Fall back to PIL renderer
                return self.text_renderer.render_frame(frame_audio_data, background_image, metadata)
        else:
            # Use PIL renderer for everything
            print("Using PIL renderer for oscilloscope waveform (GL renderer not available)")
            return self.text_renderer.render_frame(frame_audio_data, background_image, metadata)

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

        # Override fps with the value from config if available
        if "fps" in conf:
            print(f"Using fps from config: {conf['fps']}")
            fps = conf["fps"]
        else:
            print(f"Using default fps: {fps}")

        # Load Audio - we need raw samples for oscilloscope
        self.audio_samples, self.sample_rate, audio_duration = load_audio(audio_file, duration=duration, progress_callback=progress_callback)
        if self.audio_samples is None:
            raise Exception("Could not load audio file.")

        # Calculate total number of frames and samples per frame
        # Ensure duration is a float
        if isinstance(duration, str):
            try:
                duration = float(duration)
            except (ValueError, TypeError):
                print(f"Warning: Invalid duration value '{duration}', using audio_duration")
                duration = None

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

    def cleanup(self):
        """Clean up resources when the visualizer is no longer needed."""
        # Clean up GL renderer resources
        if hasattr(self, 'gl_renderer') and self.gl_renderer:
            try:
                self.gl_renderer.cleanup()
            except Exception as e:
                print(f"Error cleaning up GL renderer: {e}")

        # Clean up any other resources
        self.renderer = None
        self.text_renderer = None
        self.gl_renderer = None
        self.audio_samples = None
        self.sample_rate = None
        self.total_frames = None
        self.samples_per_frame = None

# Registration is handled by the registry discovery process