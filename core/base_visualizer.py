"""
Base visualizer class for the Video Spectrum Analyzer.
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

class BaseVisualizer(ABC):
    """
    Base class for all visualizers.
    """

    def __init__(self):
        """Initialize the base visualizer."""
        self.name = self.__class__.__name__
        self.description = "Base visualizer class"
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
        # Process configuration
        conf = self.process_config(config)

        # Load audio
        y, sr, duration = load_audio(audio_file, duration, progress_callback)

        # Load background media
        background_pil, video_capture, bg_frame_count, bg_fps = load_background_media(
            background_image_path, background_video_path, width, height
        )

        # Analyze audio
        audio_analysis = analyze_audio(
            y, sr, conf.get("n_bars", 40), conf.get("min_freq", 30),
            conf.get("max_freq", 16000), fps, progress_callback
        )

        # Initialize renderer
        renderer = self.initialize_renderer(width, height, conf)

        # Setup FFmpeg process
        process, temp_video_path = setup_ffmpeg_process(width, height, fps)

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

            # Process video frame if using video background
            current_bg_frame_pil, last_good_bg_frame_pil = process_video_frame(
                video_capture, width, height, last_good_bg_frame_pil
            ) if video_capture else (background_pil, last_good_bg_frame_pil)

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
            if progress_callback:
                progress_percent = 20 + int(70 * (frame_idx + 1) / actual_frames)
                progress_callback(progress_percent)

        # Finalize video
        print(f"Finalizing video... (took {time.time() - start_time:.2f}s to generate frames)")
        finalize_ffmpeg_process(process, temp_video_path)

        # Add audio to video
        print("Adding audio to video...")
        add_audio_to_video(temp_video_path, audio_file, output_file)

        # Cleanup
        cleanup_temp_files(temp_video_path, video_capture)

        print(f"Video saved to: {output_file}")
        return output_file

    def update_frame_data(self, frame_data, frame_idx, conf):
        """
        Update frame data for the current frame.

        Args:
            frame_data (dict): Frame data to update
            frame_idx (int): Current frame index
            conf (dict): Configuration dictionary
        """
        # Extract data from frame_data
        mel_spec_norm = frame_data["mel_spec_norm"]
        normalized_frame_energy = frame_data["normalized_frame_energy"]
        dynamic_thresholds = frame_data["dynamic_thresholds"]
        smoothed_spectrum = frame_data["smoothed_spectrum"]
        peak_values = frame_data["peak_values"]
        peak_hold_counters = frame_data["peak_hold_counters"]

        # Update spectrum and peaks
        current_spectrum = mel_spec_norm[:, frame_idx].copy()
        is_silent = normalized_frame_energy[frame_idx] < conf.get("silence_threshold", 0.04) if frame_idx < len(normalized_frame_energy) else True

        # Debug prints (every 100 frames)
        if frame_idx % 100 == 0:
            print(f"Frame {frame_idx}: Max spectrum value: {np.max(current_spectrum):.4f}, Is silent: {is_silent}")

        # Process each frequency band
        n_bars = len(current_spectrum)
        for i in range(n_bars):
            if is_silent:
                # Apply silence decay to both spectrum and peaks
                smoothed_spectrum[i] *= conf.get("silence_decay_factor", 0.5)
                peak_values[i] *= conf.get("silence_decay_factor", 0.5)
            else:
                # Apply dynamic threshold (this is the key difference from our previous implementation)
                if current_spectrum[i] > dynamic_thresholds[i]:
                    # Calculate strength based on how much the signal exceeds the threshold
                    strength = np.clip(
                        (current_spectrum[i] - dynamic_thresholds[i]) / (1 - dynamic_thresholds[i] + 1e-6),
                        0, 1
                    )

                    # Apply attack speed
                    attack_speed = conf.get("attack_speed", 0.95)
                    smoothed_spectrum[i] = max(
                        smoothed_spectrum[i] * (1 - attack_speed),
                        attack_speed * strength + smoothed_spectrum[i] * (1 - attack_speed)
                    )
                else:
                    # Apply decay if signal is below threshold
                    decay_speed = conf.get("decay_speed", 0.25)
                    smoothed_spectrum[i] = smoothed_spectrum[i] * (1 - decay_speed)

                # Apply noise gate
                if smoothed_spectrum[i] < conf.get("noise_gate", 0.04):
                    smoothed_spectrum[i] = 0.0

                # Update peak values
                if smoothed_spectrum[i] > peak_values[i]:
                    peak_values[i] = smoothed_spectrum[i]
                    peak_hold_counters[i] = conf.get("peak_hold_frames", 5)
                elif peak_hold_counters[i] > 0:
                    peak_hold_counters[i] -= 1
                else:
                    peak_values[i] = max(peak_values[i] * (1 - conf.get("peak_decay_speed", 0.15)), smoothed_spectrum[i])

                if peak_values[i] < conf.get("noise_gate", 0.04):
                    peak_values[i] = 0.0

        # Update frame_data with new values
        frame_data["smoothed_spectrum"] = smoothed_spectrum
        frame_data["peak_values"] = peak_values
        frame_data["peak_hold_counters"] = peak_hold_counters
