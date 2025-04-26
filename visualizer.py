# --- START OF FILE visualizer.py ---
import numpy as np
import librosa
import os
from tqdm import tqdm
import subprocess
import tempfile
import shutil
import time
from PIL import Image, ImageDraw, ImageFont
import io # For piping bytes
import traceback # For detailed error reporting
import pprint # For debugging config

# Helper to parse hex color string to RGB tuple (from provided file)
def hex_to_rgb(hex_color, default=(255, 255, 255)):
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        try:
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        except ValueError:
            pass # Fallback to default
    return default

# Function signature exactly as provided by user
def create_spectrum_analyzer(audio_file,
                            output_file="output.mp4",
                            background_image_path=None, # Accepts background image path
                            artist_name="Artist Name",
                            track_title="Track Title",
                            duration=None,
                            fps=30,
                            height=720,
                            width=1280,
                            config=None,
                            progress_callback=None):
    """
    Create a spectrum analyzer visualization for an audio file.
    """
    # Default configuration (from provided file)
    default_config = {
        'n_bars': 40, 'bar_width': 25, 'bar_gap': 2, 'bar_color': '#FFFFFF',
        'background_color': (0, 0, 0), 'artist_color': '#FFFFFF', 'title_color': '#FFFFFF',
        'amplitude_scale': 0.6, 'sensitivity': 1.0, 'analyzer_alpha': 1.0,
        'segment_height': 6, 'segment_gap': 6, 'corner_radius': 4,
        'min_freq': 30, 'max_freq': 16000, 'threshold_factor': 0.3,
        'attack_speed': 0.95, 'decay_speed': 0.25,
        'always_on_bottom': True, # Default value
        'peak_hold_frames': 5, 'peak_decay_speed': 0.15,
        'bass_threshold_adjust': 1.2, 'mid_threshold_adjust': 1.0, 'high_threshold_adjust': 0.9,
        'silence_threshold': 0.04, 'silence_decay_factor': 0.5, 'noise_gate': 0.08,
        'use_gradient': False,
        'gradient_top_color': (200, 200, 255), # Default Light blue top
        'gradient_bottom_color': (255, 255, 255), # Default White bottom
        'gradient_exponent': 0.7 # Controls gradient curve (1.0 = linear)
    }

    # --- Config Handling (with improved boolean fix) ---
    if config and isinstance(config, dict):
        bool_keys = ['always_on_bottom', 'use_gradient']
        float_keys = ['amplitude_scale', 'sensitivity', 'analyzer_alpha', 'threshold_factor',
                      'attack_speed', 'decay_speed', 'peak_decay_speed', 'bass_threshold_adjust',
                      'mid_threshold_adjust', 'high_threshold_adjust', 'silence_threshold',
                      'silence_decay_factor', 'noise_gate', 'gradient_exponent', 'duration']
        int_keys = ['n_bars', 'bar_width', 'bar_gap', 'segment_height', 'segment_gap',
                    'corner_radius', 'min_freq', 'max_freq', 'peak_hold_frames', 'fps',
                    'height', 'width']
        color_tuple_keys = ['gradient_top_color', 'gradient_bottom_color', 'background_color']
        color_hex_keys = ['bar_color', 'artist_color', 'title_color']
        processed_config = {}
        for key, value in config.items():
             if key in default_config:
                try:
                    if key in bool_keys:
                        if isinstance(value, str):
                            processed_config[key] = value.lower() in ('true', '1', 'on', 'yes')
                        else:
                            processed_config[key] = bool(value)
                    elif key in float_keys:
                        if key == 'duration' and float(value) == 0: processed_config[key] = None
                        else: processed_config[key] = float(value)
                    elif key in int_keys: processed_config[key] = int(value)
                    elif key in color_tuple_keys:
                         if isinstance(value, (list, tuple)) and len(value) == 3: processed_config[key] = tuple(int(v) for v in value)
                         else: processed_config[key] = default_config[key]
                    elif key in color_hex_keys: processed_config[key] = str(value)
                    else: processed_config[key] = value
                except (ValueError, TypeError): processed_config[key] = default_config[key]
        default_config.update(processed_config)
        if 'gradient_exponent' not in processed_config: default_config['gradient_exponent'] = 0.7

    # --- Extract and Process Configuration ---
    conf = default_config

    # +++ DEBUG PRINT 1: Check value right after extracting from 'conf' +++
    print("\n--- DEBUG: Post-Config Extraction ---")
    temp_flag_value = conf.get('always_on_bottom', 'Key Missing!') # Check value directly from dict
    print(f"    Value from conf['always_on_bottom']: {temp_flag_value} (Type: {type(temp_flag_value)})")
    ALWAYS_ON_BOTTOM_FLAG = conf.get('always_on_bottom', False) # Assign (using .get for safety)
    print(f"    Assigned ALWAYS_ON_BOTTOM_FLAG: {ALWAYS_ON_BOTTOM_FLAG} (Type: {type(ALWAYS_ON_BOTTOM_FLAG)})")
    print("--- END DEBUG ---\n")
    # +++ END DEBUG PRINT 1 +++

    N_BARS = conf['n_bars']; BAR_WIDTH = conf['bar_width']; BAR_GAP = conf['bar_gap']
    BACKGROUND_COLOR = conf['background_color']; AMPLITUDE_SCALE = conf['amplitude_scale']
    SENSITIVITY = conf['sensitivity']; ANALYZER_ALPHA = max(0.0, min(1.0, conf['analyzer_alpha']))
    SEGMENT_HEIGHT = conf['segment_height']; SEGMENT_GAP = conf['segment_gap']
    CORNER_RADIUS = conf['corner_radius']; MIN_FREQ = conf['min_freq']; MAX_FREQ = conf['max_freq']
    THRESHOLD_FACTOR = conf['threshold_factor']; ATTACK_SPEED = conf['attack_speed']
    DECAY_SPEED = conf['decay_speed']
    # ALWAYS_ON_BOTTOM_FLAG assigned above
    PEAK_HOLD_FRAMES = conf['peak_hold_frames']; PEAK_DECAY_SPEED = conf['peak_decay_speed']
    BASS_THRESHOLD_ADJUST = conf['bass_threshold_adjust']; MID_THRESHOLD_ADJUST = conf['mid_threshold_adjust']
    HIGH_THRESHOLD_ADJUST = conf['high_threshold_adjust']; SILENCE_THRESHOLD = conf['silence_threshold']
    SILENCE_DECAY_FACTOR = conf['silence_decay_factor']; NOISE_GATE = conf['noise_gate']
    USE_GRADIENT = conf.get('use_gradient', False) # Use .get for safety
    GRADIENT_TOP_COLOR = tuple(conf['gradient_top_color']) if isinstance(conf['gradient_top_color'], (list, tuple)) else (200, 200, 255)
    GRADIENT_BOTTOM_COLOR = tuple(conf['gradient_bottom_color']) if isinstance(conf['gradient_bottom_color'], (list, tuple)) else (255, 255, 255)
    GRADIENT_EXPONENT = conf['gradient_exponent']
    BAR_COLOR_RGB = hex_to_rgb(conf.get('bar_color', '#FFFFFF'))
    ARTIST_COLOR_RGB = hex_to_rgb(conf.get('artist_color', '#FFFFFF'))
    TITLE_COLOR_RGB = hex_to_rgb(conf.get('title_color', '#FFFFFF'))
    EFFECTIVE_AMPLITUDE_SCALE = AMPLITUDE_SCALE * SENSITIVITY
    PIL_ALPHA = int(ANALYZER_ALPHA * 255) # Alpha for compositing

    # --- Load Audio ---
    if progress_callback: progress_callback(5); print("Loading audio file...")
    try:
        y, sr = librosa.load(audio_file, sr=None)
    except Exception as e:
        print(f"ERROR Loading Audio: {e}")
        raise
    if len(y.shape) > 1:
        y = np.mean(y, axis=1)
    audio_duration = librosa.get_duration(y=y, sr=sr)
    if duration is None or duration <= 0 or duration > audio_duration:
        duration = audio_duration
    sample_count = int(duration * sr)
    y = y[:sample_count]
    if progress_callback:
        progress_callback(10)

    # --- Load Background Image ---
    background_pil = None
    if background_image_path and os.path.exists(background_image_path):
        try:
            print(f"Loading background image: {background_image_path}")
            with Image.open(background_image_path) as _img:
                if _img.mode != 'RGBA':
                    background_pil = _img.convert('RGBA')
                else:
                    background_pil = _img.copy()
            img_ratio = background_pil.width / background_pil.height
            vid_ratio = width / height
            if img_ratio > vid_ratio:
                new_width = int(vid_ratio * background_pil.height)
                left = (background_pil.width - new_width) / 2
                background_pil = background_pil.crop((left, 0, left + new_width, background_pil.height))
            elif img_ratio < vid_ratio:
                new_height = int(background_pil.width / vid_ratio)
                top = (background_pil.height - new_height) / 2
                background_pil = background_pil.crop((0, top, background_pil.width, top + new_height))
            background_pil = background_pil.resize((width, height), Image.Resampling.LANCZOS)
            print("Background image loaded, converted to RGBA, and resized.")
        except Exception as e:
            print(f"Warning: Could not load or process background image: {e}. Using solid color.")
            background_pil = None

    # --- Audio Analysis ---
    total_frames = int(duration * fps)
    hop_length = max(1, int(len(y) / total_frames))
    n_fft = 2048
    print(f"Performing STFT (approx {total_frames} frames)...")
    D = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop_length))
    if progress_callback:
        progress_callback(15)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    freq_mask = (freqs >= MIN_FREQ) & (freqs <= MAX_FREQ)
    D_filtered = D[freq_mask] if np.any(freq_mask) else D
    if D_filtered.shape[0] == 0:
        print("Warning: No frequency bins selected after filtering.")
        D_filtered = np.zeros((1, D.shape[1])) # Fallback
    if D_filtered.size == 0:
        raise ValueError("Filtered spectrum is empty. Check frequency range or audio content.")
    mel_spec = librosa.feature.melspectrogram(S=np.maximum(0, D_filtered)**2, sr=sr, n_mels=N_BARS, fmin=MIN_FREQ, fmax=MAX_FREQ)
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
    min_db = np.min(mel_spec_db); max_db = np.max(mel_spec_db)
    if max_db <= min_db:
        mel_spec_norm = np.zeros_like(mel_spec_db)
        print("Warning: Spectrum has constant value.")
    else:
        mel_spec_norm = (mel_spec_db - min_db) / (max_db - min_db + 1e-6)
    if progress_callback:
        progress_callback(20)
    bass_limit=int(N_BARS*0.2); mid_limit=int(N_BARS*0.7); threshold_adjustments=np.ones(N_BARS)
    threshold_adjustments[:bass_limit]=BASS_THRESHOLD_ADJUST; threshold_adjustments[bass_limit:mid_limit]=MID_THRESHOLD_ADJUST
    threshold_adjustments[mid_limit:]=HIGH_THRESHOLD_ADJUST; freq_avg_energy=np.mean(mel_spec_norm, axis=1)
    dynamic_thresholds=freq_avg_energy*THRESHOLD_FACTOR*threshold_adjustments; dynamic_thresholds=np.maximum(dynamic_thresholds, 0.05)
    frame_energy=np.mean(mel_spec_norm, axis=0); energy_95th_percentile = np.percentile(frame_energy, 95) if frame_energy.size > 0 else 1.0
    normalized_frame_energy = frame_energy / (energy_95th_percentile + 1e-6); normalized_frame_energy = np.clip(normalized_frame_energy, 0, 1)
    actual_frames = mel_spec_norm.shape[1]; print(f"STFT produced {actual_frames} frames.")
    if actual_frames == 0:
        raise ValueError("Audio analysis resulted in 0 frames. Cannot create video.")

    # --- Setup Visualization --- (Font loading)
    print("--- FONT LOADING ---")
    font_size_artist = 72; font_size_title = 36; artist_font = None; title_font = None; font_load_success = False
    local_font_path_bold = "DejaVuSans-Bold.ttf"; local_font_path_regular = "DejaVuSans.ttf"
    fallback_font_paths = [ ("arialbd.ttf", "arial.ttf"), ("Arial Bold.ttf", "Arial.ttf"), ("Helvetica-Bold.ttf", "Helvetica.ttf"), ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),]
    try:
        print(f"Attempting local: Bold='{local_font_path_bold}', Regular='{local_font_path_regular}'")
        if os.path.exists(local_font_path_bold) and os.path.exists(local_font_path_regular):
            artist_font = ImageFont.truetype(local_font_path_bold, font_size_artist)
            title_font = ImageFont.truetype(local_font_path_regular, font_size_title)
            font_load_success = True
            print("   Success loading local fonts.")
        else:
            print("   Local fonts not found.")
            raise IOError("Local fonts not found")
    except Exception as e:
         print(f"   Error loading local fonts: {e}\nAttempting fallback system fonts...")
         for bold_path, regular_path in fallback_font_paths:
             if font_load_success:
                 break
             try:
                 print(f"   Trying pair: Bold='{bold_path}', Regular='{regular_path}'")
                 artist_font = ImageFont.truetype(bold_path, font_size_artist)
                 title_font = ImageFont.truetype(regular_path, font_size_title)
                 font_load_success = True
                 print(f"   Success loading fallback pair.")
                 break
             except IOError:
                 print(f"      Failed.")
             except Exception as fe:
                 print(f"      Error with fallback pair: {fe}")
    if not font_load_success:
        print("--- All font loading attempts failed. Falling back to default font (will be small). ---")
        artist_font = ImageFont.load_default()
        title_font = ImageFont.load_default()

    if artist_font and artist_font != ImageFont.load_default():
        try:
             print(f"Final Artist Font 'A' Height: {artist_font.getbbox('A')[3] - artist_font.getbbox('A')[1]}")
        except: pass
    else: print("Final Artist Font: Default (small)")
    if title_font and title_font != ImageFont.load_default():
        try: print(f"Final Title Font 'A' Height: {title_font.getbbox('A')[3] - title_font.getbbox('A')[1]}")
        except: pass
    else: print("Final Title Font: Default (small)")
    print("--- FONT LOADING COMPLETE ---")

    # --- Visualization Variables ---
    smoothed_spectrum = np.zeros((N_BARS,)); peak_values = np.zeros((N_BARS,)); peak_hold_counters = np.zeros((N_BARS,), dtype=int)
    viz_bottom = int(height * 0.65); total_bar_width_gap = BAR_WIDTH + BAR_GAP
    total_bars_width = N_BARS * total_bar_width_gap - BAR_GAP; start_x = (width - total_bars_width) // 2
    segment_unit = SEGMENT_HEIGHT + SEGMENT_GAP; max_viz_height = int(height * 0.6)
    max_segments = max(1, max_viz_height // segment_unit) if segment_unit > 0 else 1
    corner_radius = min(CORNER_RADIUS, SEGMENT_HEIGHT // 2, BAR_WIDTH // 2) if CORNER_RADIUS > 0 else 0
    corner_radius = max(0, corner_radius) # Ensure non-negative

    # --- Setup FFmpeg Process for Piping ---
    temp_video_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    temp_video_path = temp_video_file.name
    temp_video_file.close()
    print(f"Temporary video path (no audio): {temp_video_path}")
    ffmpeg_cmd = [ 'ffmpeg', '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo', '-s', f'{width}x{height}', '-pix_fmt', 'rgb24', '-r', str(fps), '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', '-pix_fmt', 'yuv420p', temp_video_path ]
    print("Starting FFmpeg process for video frames...")
    try:
        process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    except FileNotFoundError:
        print("\n"+"="*60+"\n FATAL ERROR: ffmpeg command not found.\n"+"="*60+"\n")
        raise
    except Exception as e:
        print(f"ERROR: Failed to start FFmpeg process: {e}")
        raise

    # --- Generate Frames and Pipe to FFmpeg ---
    print("Generating frames and piping to FFmpeg...")

    # +++ DEBUG PRINT 2: Check value right before the loop starts +++
    print(f"\n--- DEBUG: Pre-Frame Loop ---")
    print(f"    Value of ALWAYS_ON_BOTTOM_FLAG just before loop: {ALWAYS_ON_BOTTOM_FLAG} (Type: {type(ALWAYS_ON_BOTTOM_FLAG)})")
    print(f"--- END DEBUG ---\n")
    # +++ END DEBUG PRINT 2 +++

    start_time = time.time(); seg_width = int(BAR_WIDTH); seg_height = int(SEGMENT_HEIGHT)
    if seg_width <= 0 or seg_height <= 0:
        raise ValueError(f"Invalid segment dimensions: {seg_width}x{seg_height}")

    # Main loop
    for frame_idx in tqdm(range(actual_frames), desc="Generating Frames"):
        # --- Update spectrum and peaks ---
        current_spectrum = mel_spec_norm[:, frame_idx].copy()
        if frame_idx < len(normalized_frame_energy):
            is_silent = normalized_frame_energy[frame_idx] < SILENCE_THRESHOLD
        else:
            is_silent = True
            print(f"Warning: frame_idx {frame_idx} out of bounds for energy array")
        for i in range(N_BARS):
            if is_silent:
                smoothed_spectrum[i]*=SILENCE_DECAY_FACTOR
                peak_values[i]*=SILENCE_DECAY_FACTOR
            else:
                if current_spectrum[i] > dynamic_thresholds[i]:
                    strength = np.clip((current_spectrum[i]-dynamic_thresholds[i])/(1-dynamic_thresholds[i]+1e-6), 0, 1)
                    smoothed_spectrum[i] = max(smoothed_spectrum[i] * (1-ATTACK_SPEED), ATTACK_SPEED*strength + smoothed_spectrum[i]*(1-ATTACK_SPEED))
                else:
                    smoothed_spectrum[i] = smoothed_spectrum[i] * (1-DECAY_SPEED)
                if smoothed_spectrum[i] < NOISE_GATE:
                    smoothed_spectrum[i] = 0.0
                if smoothed_spectrum[i] > peak_values[i]:
                    peak_values[i]=smoothed_spectrum[i]
                    peak_hold_counters[i]=PEAK_HOLD_FRAMES
                elif peak_hold_counters[i] > 0:
                    peak_hold_counters[i] -= 1
                else:
                    peak_values[i]=max(peak_values[i]*(1-PEAK_DECAY_SPEED), smoothed_spectrum[i])
                if peak_values[i] < NOISE_GATE:
                    peak_values[i] = 0.0

        # Create base image
        if background_pil:
            image = background_pil.copy()
        else:
            image = Image.new('RGBA', (width, height), color=BACKGROUND_COLOR + (255,))

        # ================================================================
        # --- DRAWING LOGIC ---
        # ================================================================
        for i in range(N_BARS):
            bar_x = start_x + i * total_bar_width_gap
            signal = smoothed_spectrum[i]
            peak_signal = peak_values[i]

            # --- STEP 1: Draw Static Bottom Segment (if flag is set) ---
            # Check the flag value here inside the loop condition
            if ALWAYS_ON_BOTTOM_FLAG and max_segments >= 1:
                # If the code reaches here, the flag MUST be True for this iteration
                static_bottom_y = viz_bottom - SEGMENT_HEIGHT; static_dest_xy = (int(bar_x), int(static_bottom_y))
                static_color_rgb = GRADIENT_BOTTOM_COLOR if USE_GRADIENT else BAR_COLOR_RGB
                static_color_rgba = static_color_rgb + (PIL_ALPHA,)
                static_seg_img = Image.new('RGBA', (seg_width, seg_height), (0, 0, 0, 0)); static_seg_draw = ImageDraw.Draw(static_seg_img)
                if corner_radius == 0: static_seg_draw.rectangle((0, 0, seg_width, seg_height), fill=static_color_rgba)
                else: static_seg_draw.rounded_rectangle((0, 0, seg_width, seg_height), radius=corner_radius, fill=static_color_rgba)
                image.alpha_composite(static_seg_img, static_dest_xy)

            # --- STEP 2: Draw Dynamic Segments and Peak ABOVE the static bottom ---
            num_segments_available_above = max(0, max_segments - 1) if ALWAYS_ON_BOTTOM_FLAG else max_segments
            num_dynamic_segments_to_draw = 0
            if signal > NOISE_GATE and num_segments_available_above > 0:
                dynamic_segments_float = signal * num_segments_available_above * EFFECTIVE_AMPLITUDE_SCALE
                num_dynamic_segments_to_draw = int(np.ceil(dynamic_segments_float)); num_dynamic_segments_to_draw = min(num_dynamic_segments_to_draw, num_segments_available_above)
            for k in range(num_dynamic_segments_to_draw):
                j = k + 1 if ALWAYS_ON_BOTTOM_FLAG else k; segment_y = viz_bottom - (j + 1) * SEGMENT_HEIGHT - j * SEGMENT_GAP; dest_xy = (int(bar_x), int(segment_y))
                segment_color_rgb = BAR_COLOR_RGB
                if USE_GRADIENT:
                    if max_segments <= 1: gradient_factor_raw = 0.0
                    else: gradient_factor_raw = j / (max_segments - 1); gradient_factor_raw = min(1.0, max(0.0, gradient_factor_raw))
                    gradient_factor = gradient_factor_raw ** GRADIENT_EXPONENT; r = int(GRADIENT_BOTTOM_COLOR[0]*(1-gradient_factor) + GRADIENT_TOP_COLOR[0]*gradient_factor); g = int(GRADIENT_BOTTOM_COLOR[1]*(1-gradient_factor) + GRADIENT_TOP_COLOR[1]*gradient_factor); b = int(GRADIENT_BOTTOM_COLOR[2]*(1-gradient_factor) + GRADIENT_TOP_COLOR[2]*gradient_factor); segment_color_rgb = (max(0,min(r,255)), max(0,min(g,255)), max(0,min(b,255)))
                segment_color_rgba = segment_color_rgb + (PIL_ALPHA,)
                segment_img = Image.new('RGBA', (seg_width, seg_height), (0, 0, 0, 0)); segment_draw_alpha = ImageDraw.Draw(segment_img)
                if corner_radius == 0: segment_draw_alpha.rectangle((0, 0, seg_width, seg_height), fill=segment_color_rgba)
                else: segment_draw_alpha.rounded_rectangle((0, 0, seg_width, seg_height), radius=corner_radius, fill=segment_color_rgba)
                image.alpha_composite(segment_img, dest_xy)
            peak_segment_index_abs = -1
            if peak_signal > NOISE_GATE:
                peak_total_segments_float = peak_signal * max_segments * EFFECTIVE_AMPLITUDE_SCALE; peak_total_segments = int(np.ceil(peak_total_segments_float)); peak_total_segments = min(peak_total_segments, max_segments); peak_segment_index_abs = peak_total_segments - 1
            highest_dynamic_segment_index_abs = -1
            if num_dynamic_segments_to_draw > 0: highest_dynamic_segment_index_abs = (num_dynamic_segments_to_draw - 1) + 1 if ALWAYS_ON_BOTTOM_FLAG else (num_dynamic_segments_to_draw - 1)
            if peak_segment_index_abs >= 0 and peak_segment_index_abs > highest_dynamic_segment_index_abs:
                if not (ALWAYS_ON_BOTTOM_FLAG and peak_segment_index_abs == 0):
                    peak_j = peak_segment_index_abs; peak_y = viz_bottom - (peak_j + 1) * SEGMENT_HEIGHT - peak_j * SEGMENT_GAP; peak_dest_xy = (int(bar_x), int(peak_y))
                    peak_color_rgb = BAR_COLOR_RGB
                    if USE_GRADIENT:
                        if max_segments <= 1: gradient_factor_raw = 0.0
                        else: gradient_factor_raw = peak_j / (max_segments - 1); gradient_factor_raw = min(1.0, max(0.0, gradient_factor_raw))
                        gradient_factor = gradient_factor_raw ** GRADIENT_EXPONENT; r = int(GRADIENT_BOTTOM_COLOR[0]*(1-gradient_factor) + GRADIENT_TOP_COLOR[0]*gradient_factor); g = int(GRADIENT_BOTTOM_COLOR[1]*(1-gradient_factor) + GRADIENT_TOP_COLOR[1]*gradient_factor); b = int(GRADIENT_BOTTOM_COLOR[2]*(1-gradient_factor) + GRADIENT_TOP_COLOR[2]*gradient_factor); peak_color_rgb = (max(0,min(r,255)), max(0,min(g,255)), max(0,min(b,255)))
                    peak_color_rgba = peak_color_rgb + (PIL_ALPHA,)
                    peak_img = Image.new('RGBA', (seg_width, seg_height), (0, 0, 0, 0)); peak_draw = ImageDraw.Draw(peak_img)
                    if corner_radius == 0: peak_draw.rectangle((0, 0, seg_width, seg_height), fill=peak_color_rgba)
                    else: peak_draw.rounded_rectangle((0, 0, seg_width, seg_height), radius=corner_radius, fill=peak_color_rgba)
                    image.alpha_composite(peak_img, peak_dest_xy)
        # ================================================================
        # --- END: DRAWING LOGIC ---
        # ================================================================


        # Add Text
        draw_text = ImageDraw.Draw(image)
        if artist_font and title_font:
            try:
                anchor_artist = "ma"; anchor_title = "ma"
                if artist_font == ImageFont.load_default() or title_font == ImageFont.load_default():
                    anchor_artist = "mm"; anchor_title = "mm"
                artist_bbox = draw_text.textbbox((0,0), artist_name, font=artist_font) if artist_name else (0,0,0,0)
                title_bbox = draw_text.textbbox((0,0), track_title, font=title_font) if track_title else (0,0,0,0)
                artist_text_width=artist_bbox[2]-artist_bbox[0]; artist_text_height=artist_bbox[3]-artist_bbox[1]
                title_text_width=title_bbox[2]-title_bbox[0]
                artist_text_x=width//2; artist_text_y=viz_bottom+20 + artist_text_height // 2
                title_text_x=width//2; title_text_y = artist_text_y + artist_text_height // 2 + 10 + (title_bbox[3]-title_bbox[1]) // 2
                if artist_name:
                    draw_text.text((artist_text_x, artist_text_y), artist_name, fill=ARTIST_COLOR_RGB, font=artist_font, anchor=anchor_artist)
                if track_title:
                    draw_text.text((title_text_x, title_text_y), track_title, fill=TITLE_COLOR_RGB, font=title_font, anchor=anchor_title)
            except Exception as text_err:
                print(f"Warning: Error drawing text on frame {frame_idx}: {text_err}")

        # --- Pipe Frame to FFmpeg ---
        try:
            image_rgb = image.convert('RGB')
            frame_bytes = image_rgb.tobytes()
            process.stdin.write(frame_bytes)
        except (BrokenPipeError, OSError) as e:
            print(f"\nError writing frame {frame_idx} to FFmpeg: {e}")
            try: process.stdin.close()
            except OSError: pass
            process.wait()
            print(f"FFmpeg exit code (after pipe error): {process.returncode}")
            if os.path.exists(temp_video_path):
                try: os.remove(temp_video_path)
                except OSError as remove_e: print(f"Warning: Could not remove temp file after error: {remove_e}")
            raise RuntimeError(f"FFmpeg process failed during frame writing. Error: {e}") from e
        except Exception as e:
             print(f"\nUnexpected error during frame piping: {e}")
             if process.stdin:
                 try: process.stdin.close()
                 except Exception as close_e: print(f"Warning: Error closing stdin during general exception: {close_e}")
             process.poll()
             if process.returncode is None:
                 print("Terminating ffmpeg process due to unexpected error...")
                 process.terminate()
                 process.wait(timeout=5)
             if os.path.exists(temp_video_path):
                 try: os.remove(temp_video_path)
                 except OSError as remove_e: print(f"Warning: Could not remove temp file after error: {remove_e}")
             raise

        # Update progress callback
        if progress_callback and frame_idx % 5 == 0:
            progress = int(20 + (frame_idx / max(1, actual_frames)) * 70)
            progress_callback(progress)

    # --- Finalize FFmpeg Video ---
    end_time = time.time()
    print(f"\nFrame generation and piping completed in {end_time - start_time:.2f} seconds")
    print("Closing FFmpeg stdin and waiting for video process to finish...")
    if process.stdin:
        try:
            process.stdin.close()
        except (OSError, BrokenPipeError) as e:
             print(f"Warning: Error closing ffmpeg stdin (might be okay): {e}")

    process.wait()
    if process.returncode != 0:
        print(f"ERROR: FFmpeg video encoding failed with exit code {process.returncode}")
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
        raise subprocess.CalledProcessError(process.returncode, ffmpeg_cmd)
    else:
        print("FFmpeg video encoding successful.")

    if progress_callback:
        progress_callback(90)

    # --- Add Audio ---
    print("Adding audio to the video...")
    final_ffmpeg_cmd = [ 'ffmpeg', '-y', '-i', temp_video_path, '-i', audio_file, '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', output_file ]
    try:
        print(f"Running command: {' '.join(final_ffmpeg_cmd)}")
        result = subprocess.run(final_ffmpeg_cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
        print("Audio added successfully.")
        if result.stderr:
            print(f"FFmpeg warnings (audio merge):\n{result.stderr}")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: FFmpeg audio merging failed with exit code {e.returncode}\nFFmpeg stderr:\n{e.stderr}\nTemp video at: {temp_video_path}")
        raise
    except FileNotFoundError:
        print("ERROR: ffmpeg command not found for audio merge.")
        if os.path.exists(temp_video_path):
            try: os.remove(temp_video_path)
            except OSError as remove_e: print(f"Warning: Could not remove temp file {temp_video_path} after FileNotFoundError: {remove_e}")
        raise
    except Exception as e:
        print(f"ERROR: Unexpected error during audio merge: {e}")
        if os.path.exists(temp_video_path):
            try: os.remove(temp_video_path)
            except OSError as remove_e: print(f"Warning: Could not remove temp file {temp_video_path} after error: {remove_e}")
        raise

    # --- Cleanup ---
    print("Cleaning up temporary video file...")
    if os.path.exists(temp_video_path):
        try:
            os.remove(temp_video_path)
            print(f"Removed temp file: {temp_video_path}")
        except OSError as e:
            print(f"Warning: Could not remove temp file {temp_video_path}: {e}")
    if progress_callback:
        progress_callback(100)
    print(f"Visualization saved to: {output_file}")

# --- END OF FILE visualizer.py ---
