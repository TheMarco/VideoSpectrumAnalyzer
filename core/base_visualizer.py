"""
Base visualizer class for the Audio Visualizer Suite.
All visualizers must inherit from this class.
"""
import os
import numpy as np
from abc import ABC, abstractmethod
from PIL import Image
from tqdm import tqdm
import time

from modules.audio_processor import load_audio, analyze_audio
from modules.media_handler import load_background_media, process_video_frame
from modules.ffmpeg_handler import (
    setup_ffmpeg_process,
    write_frame_to_ffmpeg,
    finalize_ffmpeg_process,
    add_audio_to_video,
    cleanup_temp_files
)
from modules.progress_tracker import ProgressTracker

class BaseVisualizer(ABC):
    """
    Base class for all visualizers.
    """

    def __init__(self):
        """Initialize the base visualizer."""
        self.name = self.__class__.__name__
        # Use display_name if defined, otherwise use name
        self.display_name = getattr(self, 'display_name', self.name)
        # Only set description and thumbnail if not already defined in the class
        if not hasattr(self, 'description'):
            self.description = "Base visualizer class"
        if not hasattr(self, 'thumbnail'):
            self.thumbnail = None

    @abstractmethod
    def process_config(self, config=None):
        """
        Process and validate the configuration.

        Args:
            config (dict, optional): User-provided configuration

        Returns:
            dict: Processed configuration with all required parameters
        """
        pass

    @abstractmethod
    def initialize_renderer(self, width, height, config):
        """
        Initialize the renderer for this visualizer.

        Args:
            width (int): Frame width
            height (int): Frame height
            config (dict): Configuration dictionary

        Returns:
            object: Renderer instance
        """
        pass

    @abstractmethod
    def render_frame(self, renderer, frame_data, background_image, metadata):
        """
        Render a single frame.

        Args:
            renderer: Renderer instance
            frame_data (dict): Frame data (spectrum, peaks, etc.)
            background_image (PIL.Image): Background image
            metadata (dict): Additional metadata (artist, title, etc.)

        Returns:
            PIL.Image: Rendered frame
        """
        pass

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
        Create a visualization for an audio file.

        Args:
            audio_file (str): Path to the audio file
            output_file (str, optional): Path to the output video file
            background_image_path (str, optional): Path to the background image
            background_video_path (str, optional): Path to the background video
            background_shader_path (str, optional): Path to the GLSL shader file
            artist_name (str, optional): Artist name to display
            track_title (str, optional): Track title to display
            duration (float, optional): Duration in seconds to trim the audio to
            fps (int, optional): Frames per second for the output video
            height (int, optional): Height of the output video
            width (int, optional): Width of the output video
            config (dict, optional): Configuration dictionary
            progress_callback (callable, optional): Callback function for progress updates

        Returns:
            str: Path to the output video file
        """
        # Initialize progress tracker
        progress = ProgressTracker(callback=progress_callback)

        # Process configuration
        conf = self.process_config(config)

        # Start audio loading stage
        progress.start_stage("audio_loading", "Loading audio file...")

        # Load audio
        y, sr, duration = load_audio(audio_file, duration,
                                     lambda p, m=None: progress.update_stage_progress(p, m))

        # Complete audio loading stage
        progress.complete_stage("Audio loaded successfully")

        # Start audio analysis stage
        progress.start_stage("audio_analysis", "Analyzing audio...")

        # Analyze audio
        audio_analysis = analyze_audio(
            y, sr, conf.get("n_bars", 40), conf.get("min_freq", 30),
            conf.get("max_freq", 16000), fps,
            lambda p, m=None: progress.update_stage_progress(p, m)
        )

        # Complete audio analysis stage
        progress.complete_stage("Audio analysis complete")

        # Start background preparation stage
        progress.start_stage("background_preparation", "Preparing background media...")

        # Load background media
        background_pil, video_capture, bg_frame_count, bg_fps, shader_renderer = load_background_media(
            background_image_path, background_video_path, background_shader_path, width, height,
            duration=duration, fps=fps,
            progress_callback=lambda p, m=None: progress.update_stage_progress(p, m)
        )

        # Initialize renderer
        renderer = self.initialize_renderer(width, height, conf)

        # Setup FFmpeg process
        process, temp_video_path = setup_ffmpeg_process(width, height, fps)

        # Complete background preparation stage
        progress.complete_stage("Background preparation complete")

        # Start frame generation stage
        progress.start_stage("frame_generation", f"Generating frames for {self.name} visualization...")

        # Generate frames
        print(f"Generating frames for {self.name} visualization...")
        start_time = time.time()
        last_good_bg_frame_pil = None

        # Extract audio analysis data
        mel_spec_norm = audio_analysis["mel_spec_norm"]
        normalized_frame_energy = audio_analysis["normalized_frame_energy"]
        actual_frames = audio_analysis["actual_frames"]
        dynamic_thresholds = audio_analysis["dynamic_thresholds"]

        # Initialize frame data
        frame_data = {
            "mel_spec_norm": mel_spec_norm,
            "normalized_frame_energy": normalized_frame_energy,
            "dynamic_thresholds": dynamic_thresholds,
            "smoothed_spectrum": np.zeros((conf.get("n_bars", 40),)),
            "peak_values": np.zeros((conf.get("n_bars", 40),)),
            "peak_hold_counters": np.zeros((conf.get("n_bars", 40),), dtype=int)
        }

        # Metadata for rendering
        metadata = {
            "artist_name": artist_name,
            "track_title": track_title
        }

        # Main loop
        for frame_idx in tqdm(range(actual_frames), desc="Generating Frames"):
            # Update frame data
            self.update_frame_data(frame_data, frame_idx, conf)

            # Calculate current time for shader rendering
            current_time = frame_idx / fps

            # Process video frame if using video background or shader
            current_bg_frame_pil, last_good_bg_frame_pil = process_video_frame(
                video_capture, shader_renderer, width, height, current_time, last_good_bg_frame_pil
            ) if (video_capture or shader_renderer) else (background_pil, last_good_bg_frame_pil)

            # Render frame
            image = self.render_frame(renderer, frame_data, current_bg_frame_pil, metadata)

            # Write frame to FFmpeg
            try:
                frame_bytes = image.tobytes()
                write_frame_to_ffmpeg(process, frame_bytes, frame_idx)
            except Exception as e:
                print(f"\nError writing frame {frame_idx} to FFmpeg: {e}")
                cleanup_temp_files(temp_video_path, video_capture)
                raise

            # Update progress
            if frame_idx % 5 == 0 or frame_idx == actual_frames - 1:  # Update every 5 frames to reduce overhead
                progress_percent = (frame_idx + 1) / actual_frames * 100
                frame_message = f"Rendering frame {frame_idx+1}/{actual_frames}"
                progress.update_stage_progress(progress_percent, frame_message)

        # Complete frame generation stage
        progress.complete_stage(f"Frame generation complete (took {time.time() - start_time:.2f}s)")

        # Start video finalization stage
        progress.start_stage("video_finalization", "Finalizing video...")

        # Finalize video
        print(f"Finalizing video... (took {time.time() - start_time:.2f}s to generate frames)")
        finalize_ffmpeg_process(process, temp_video_path)

        # Add audio to video
        print("Adding audio to video...")
        progress.update_stage_progress(50, "Adding audio to video...")
        add_audio_to_video(temp_video_path, audio_file, output_file)

        # Cleanup
        progress.update_stage_progress(90, "Cleaning up temporary files...")
        cleanup_temp_files(temp_video_path, video_capture)

        # Cleanup shader renderer if used
        if shader_renderer:
            shader_renderer.cleanup()

        # Complete video finalization stage
        progress.complete_stage("Video saved successfully")

        print(f"Video saved to: {output_file}")
        return output_file

    @abstractmethod
    def update_frame_data(self, frame_data, frame_idx, conf):
        """
        Update frame data for the current frame.

        Args:
            frame_data (dict): Frame data to update
            frame_idx (int): Current frame index
            conf (dict): Configuration dictionary
        """
        raise NotImplementedError("Subclasses must implement update_frame_data")
