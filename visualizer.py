"""
Main module for the spectrum analyzer.
This module provides the main entry point for creating spectrum analyzer visualizations.
"""
import os
import numpy as np
from tqdm import tqdm
import time

# Import modules from the modules package
from modules.utils import hex_to_rgb
from modules.config_handler import process_config
from modules.audio_processor import load_audio, analyze_audio
from modules.media_handler import load_background_media, load_fonts, process_video_frame
from modules.renderer import SpectrumRenderer
from modules.ffmpeg_handler import (
    setup_ffmpeg_process,
    write_frame_to_ffmpeg,
    finalize_ffmpeg_process,
    add_audio_to_video,
    cleanup_temp_files
)


def create_spectrum_analyzer(
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
    Create a spectrum analyzer visualization for an audio file,
    optionally with a static image or looping video background.

    Args:
        audio_file (str): Path to the audio file
        output_file (str): Path to save the output video
        background_image_path (str, optional): Path to background image
        background_video_path (str, optional): Path to background video
        artist_name (str): Artist name to display
        track_title (str): Track title to display
        duration (float, optional): Duration in seconds to trim the audio to
        fps (int): Frames per second for the output video
        height (int): Height of the output video
        width (int): Width of the output video
        config (dict, optional): Configuration dictionary
        progress_callback (callable, optional): Callback function for progress updates

    Returns:
        str: Path to the output video file
    """
    # Process configuration
    conf = process_config(config)

    # Load audio
    y, sr, duration = load_audio(audio_file, duration, progress_callback)

    # Load background media
    background_pil, video_capture, bg_frame_count, bg_fps = load_background_media(
        background_image_path, background_video_path, width, height
    )

    # Analyze audio
    audio_analysis = analyze_audio(
        y, sr, conf["n_bars"], conf["min_freq"], conf["max_freq"], fps, progress_callback
    )

    mel_spec_norm = audio_analysis["mel_spec_norm"]
    normalized_frame_energy = audio_analysis["normalized_frame_energy"]
    actual_frames = audio_analysis["actual_frames"]
    dynamic_thresholds = audio_analysis["dynamic_thresholds"]

    # Load fonts with the text size from config
    text_size = conf.get("text_size", "large")
    print(f"Passing text_size to load_fonts: {text_size}")
    artist_font, title_font = load_fonts(text_size=text_size)

    # Print the text size being used for debugging
    print(f"Using text size: {conf.get('text_size', 'large')}")

    # Initialize renderer
    renderer = SpectrumRenderer(width, height, conf, artist_font, title_font)

    # Initialize visualization variables
    n_bars = conf["n_bars"]
    smoothed_spectrum = np.zeros((n_bars,))
    peak_values = np.zeros((n_bars,))
    peak_hold_counters = np.zeros((n_bars,), dtype=int)

    # Setup FFmpeg process
    process, temp_video_path = setup_ffmpeg_process(width, height, fps)

    # Generate frames
    print("Generating frames and piping to FFmpeg...")
    start_time = time.time()
    last_good_bg_frame_pil = None

    # Main loop
    for frame_idx in tqdm(range(actual_frames), desc="Generating Frames"):
        # Update spectrum and peaks
        current_spectrum = mel_spec_norm[:, frame_idx].copy()
        is_silent = normalized_frame_energy[frame_idx] < conf["silence_threshold"] if frame_idx < len(normalized_frame_energy) else True

        for i in range(n_bars):
            if is_silent:
                smoothed_spectrum[i] *= conf["silence_decay_factor"]
                peak_values[i] *= conf["silence_decay_factor"]
            else:
                if current_spectrum[i] > dynamic_thresholds[i]:
                    strength = np.clip((current_spectrum[i] - dynamic_thresholds[i]) / (1 - dynamic_thresholds[i] + 1e-6), 0, 1)
                    smoothed_spectrum[i] = max(
                        smoothed_spectrum[i] * (1 - conf["attack_speed"]),
                        conf["attack_speed"] * strength + smoothed_spectrum[i] * (1 - conf["attack_speed"])
                    )
                else:
                    smoothed_spectrum[i] = smoothed_spectrum[i] * (1 - conf["decay_speed"])

                if smoothed_spectrum[i] < conf["noise_gate"]:
                    smoothed_spectrum[i] = 0.0

                if smoothed_spectrum[i] > peak_values[i]:
                    peak_values[i] = smoothed_spectrum[i]
                    peak_hold_counters[i] = conf["peak_hold_frames"]
                elif peak_hold_counters[i] > 0:
                    peak_hold_counters[i] -= 1
                else:
                    peak_values[i] = max(peak_values[i] * (1 - conf["peak_decay_speed"]), smoothed_spectrum[i])

                if peak_values[i] < conf["noise_gate"]:
                    peak_values[i] = 0.0

        # Process video frame if using video background
        current_bg_frame_pil, last_good_bg_frame_pil = process_video_frame(
            video_capture, width, height, last_good_bg_frame_pil
        ) if video_capture else (background_pil, last_good_bg_frame_pil)

        # Render frame
        image = renderer.render_frame(
            smoothed_spectrum,
            peak_values,
            current_bg_frame_pil,
            artist_name,
            track_title
        )

        # Write frame to FFmpeg
        try:
            frame_bytes = image.tobytes()
            write_frame_to_ffmpeg(process, frame_bytes, frame_idx)
        except Exception as e:
            print(f"\nError writing frame {frame_idx} to FFmpeg: {e}")
            cleanup_temp_files(temp_video_path, video_capture)
            raise

        # Update progress callback
        if progress_callback and frame_idx % 5 == 0:
            progress = int(20 + (frame_idx / max(1, actual_frames)) * 70)
            progress_callback(progress)

    # Finalize video
    end_time = time.time()
    print(f"\nFrame generation completed in {end_time - start_time:.2f} seconds")

    if not finalize_ffmpeg_process(process, temp_video_path):
        cleanup_temp_files(temp_video_path, video_capture)
        raise RuntimeError("FFmpeg video encoding failed")

    if progress_callback:
        progress_callback(90)

    # Add audio to video
    if not add_audio_to_video(temp_video_path, audio_file, output_file):
        cleanup_temp_files(temp_video_path, video_capture)
        raise RuntimeError("Failed to add audio to video")

    # Cleanup
    cleanup_temp_files(temp_video_path, video_capture)

    if progress_callback:
        progress_callback(100)

    print(f"Visualization saved to: {output_file}")
    return output_file
