"""
Audio processing functions for the spectrum analyzer.
"""
import os
import numpy as np
import librosa
import time

def load_audio(audio_file, duration=None, progress_callback=None):
    """
    Load an audio file and optionally trim it to a specified duration.

    Args:
        audio_file (str): Path to the audio file
        duration (float, optional): Duration in seconds to trim the audio to
        progress_callback (callable, optional): Callback function for progress updates

    Returns:
        tuple: (audio_data, sample_rate, audio_duration)
    """
    if progress_callback:
        progress_callback(0, "Loading audio file...")
        print("Loading audio file...")

    try:
        # Update progress at the start of loading
        if progress_callback:
            progress_callback(5, f"Reading audio data from {os.path.basename(audio_file)}...")

        y, sr = librosa.load(audio_file, sr=None)

        # Update progress after loading
        if progress_callback:
            progress_callback(30, "Audio file loaded, processing...")

    except Exception as e:
        print(f"ERROR Loading Audio: {e}")
        raise

    # Convert stereo to mono if needed
    if len(y.shape) > 1:
        if progress_callback:
            progress_callback(40, "Converting stereo to mono...")
        y = np.mean(y, axis=1)

    # Get audio duration
    audio_duration = librosa.get_duration(y=y, sr=sr)

    if progress_callback:
        progress_callback(50, f"Audio duration: {audio_duration:.2f} seconds")

    # Trim audio if duration is specified
    if duration is not None:
        # Convert duration to float if it's a string
        if isinstance(duration, str):
            try:
                duration = float(duration)
            except (ValueError, TypeError):
                print(f"Warning: Invalid duration value '{duration}', using full audio duration")
                duration = None

        # Now check if we need to trim
        if duration is not None and duration > 0 and duration < audio_duration:
            if progress_callback:
                progress_callback(70, f"Trimming audio to {duration:.2f} seconds...")
            sample_count = int(duration * sr)
            y = y[:sample_count]
        else:
            duration = audio_duration
    else:
        duration = audio_duration

    if progress_callback:
        progress_callback(90, f"Audio loaded: {duration:.2f} seconds at {sr} Hz")

    return y, sr, duration

def analyze_audio(y, sr, n_bars, min_freq, max_freq, fps, progress_callback=None):
    """
    Analyze audio data to create a mel spectrogram and other audio features.

    Args:
        y (numpy.ndarray): Audio data
        sr (int): Sample rate
        n_bars (int): Number of frequency bars
        min_freq (int): Minimum frequency to analyze
        max_freq (int): Maximum frequency to analyze
        fps (int): Frames per second for the output video
        progress_callback (callable, optional): Callback function for progress updates

    Returns:
        dict: Audio analysis results including mel spectrogram, frame energy, etc.
    """
    # Calculate total frames and hop length
    duration = len(y) / sr
    total_frames = int(duration * fps)
    hop_length = max(1, int(len(y) / total_frames))
    n_fft = 2048

    if progress_callback:
        progress_callback(0, f"Preparing to analyze {duration:.2f} seconds of audio...")

    print(f"Performing STFT (approx {total_frames} frames)...")
    start_time = time.time()

    # Compute Short-Time Fourier Transform
    if progress_callback:
        progress_callback(10, "Computing Short-Time Fourier Transform...")

    D = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length))

    if progress_callback:
        progress_callback(30, "STFT complete, filtering frequencies...")

    # Filter frequencies
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    freq_mask = (freqs >= min_freq) & (freqs <= max_freq)
    D_filtered = D[freq_mask] if np.any(freq_mask) else D

    if D_filtered.shape[0] == 0:
        print("Warning: No frequency bins selected.")
        D_filtered = np.zeros((1, D.shape[1]))

    if D_filtered.size == 0:
        raise ValueError("Filtered spectrum is empty.")

    if progress_callback:
        progress_callback(40, "Computing mel spectrogram...")

    # Compute mel spectrogram
    mel_spec = librosa.feature.melspectrogram(
        S=np.maximum(0, D_filtered) ** 2,
        sr=sr,
        n_mels=n_bars,
        fmin=min_freq,
        fmax=max_freq
    )

    if progress_callback:
        progress_callback(50, "Normalizing spectrogram...")

    # Normalize mel spectrogram
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
    min_db = np.min(mel_spec_db)
    max_db = np.max(mel_spec_db)

    if max_db > min_db:
        mel_spec_norm = (mel_spec_db - min_db) / (max_db - min_db + 1e-6)
    else:
        mel_spec_norm = np.zeros_like(mel_spec_db)
        print("Warning: Spectrum has constant value.")

    if progress_callback:
        progress_callback(60, "Calculating frame energy...")

    # Calculate frame energy
    frame_energy = np.mean(mel_spec_norm, axis=0)
    energy_95th_percentile = np.percentile(frame_energy, 95) if frame_energy.size > 0 else 1.0
    normalized_frame_energy = frame_energy / (energy_95th_percentile + 1e-6)
    normalized_frame_energy = np.clip(normalized_frame_energy, 0, 1)

    # Ensure we have enough frames
    actual_frames = mel_spec_norm.shape[1]
    print(f"STFT produced {actual_frames} frames.")

    if actual_frames == 0:
        raise ValueError("Audio analysis resulted in 0 frames.")

    if progress_callback:
        progress_callback(70, f"Calculating dynamic thresholds for {n_bars} frequency bands...")

    # Calculate dynamic thresholds with more extreme adjustments and boosted highs
    bass_limit = int(n_bars * 0.2)
    mid_limit = int(n_bars * 0.7)
    threshold_adjustments = np.ones(n_bars)
    threshold_adjustments[:bass_limit] = 1.3  # Increased bass threshold adjustment
    threshold_adjustments[bass_limit:mid_limit] = 1.1  # Increased mid threshold adjustment
    threshold_adjustments[mid_limit:] = 0.6  # Further decreased high threshold adjustment to boost highs

    freq_avg_energy = np.mean(mel_spec_norm, axis=1)
    # Use a higher threshold factor (0.35 instead of 0.3) to make low signals less visible
    dynamic_thresholds = freq_avg_energy * 0.35 * threshold_adjustments
    # Set a higher minimum threshold to suppress more low signals
    dynamic_thresholds = np.maximum(dynamic_thresholds, 0.08)

    analysis_time = time.time() - start_time
    print(f"Audio analysis completed in {analysis_time:.2f} seconds")

    if progress_callback:
        progress_callback(90, f"Audio analysis complete: {actual_frames} frames at {fps} fps")

    return {
        "mel_spec_norm": mel_spec_norm,
        "normalized_frame_energy": normalized_frame_energy,
        "actual_frames": actual_frames,
        "dynamic_thresholds": dynamic_thresholds
    }
