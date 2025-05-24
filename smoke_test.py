#!/usr/bin/env python3
"""
Smoke test script to render all GLSL shaders and the Dual Bar Visualizer.

Usage:
    python3 smoke_test.py

This script renders each GLSL shader for 5 seconds at 30fps and saves outputs to tests/shaders/.
It also renders a dummy audio visualization for 5 seconds at 30fps using Dual Bar Visualizer
and saves the output to tests/dual_bar_visualizer/.
"""
import os
import sys
import glob
import subprocess

import numpy as np

def render_shaders(duration=5.0, fps=30, width=1280, height=720, output_dir="tests/shaders"):
    print("=== Rendering GLSL shaders ===")
    os.makedirs(output_dir, exist_ok=True)
    shader_paths = glob.glob(os.path.join("glsl", "*.glsl"))
    if not shader_paths:
        print("No GLSL shaders found under glsl/")
        return
    for shader_path in shader_paths:
        name = os.path.splitext(os.path.basename(shader_path))[0]
        output_path = os.path.join(output_dir, f"{name}.mp4")
        cmd = [
            sys.executable, "test_shader.py", shader_path,
            "--output", output_path,
            "--duration", str(duration),
            "--fps", str(fps),
            "--width", str(width),
            "--height", str(height),
        ]
        print(f"Rendering shader '{name}' -> {output_path}")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"Error rendering shader '{name}' (return code {result.returncode})")

def render_dual_bar(duration=5.0, fps=30, width=1280, height=720, output_dir="tests/dual_bar_visualizer"):
    print("=== Rendering Dual Bar Visualizer Smoke Test ===")
    try:
        from visualizers.dual_bar_visualizer.visualizer import DualBarVisualizer
    except ImportError as e:
        print(f"Error: could not import DualBarVisualizer: {e}")
        return

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "dual_bar_visualizer.mp4")

    total_frames = int(duration * fps)

    viz = DualBarVisualizer()
    conf = viz.process_config(None)
    renderer = viz.create_renderer(width, height, conf)

    n_bars = conf.get("n_bars", 0)
    # Synthetic mel spectrogram: shape (n_bars, total_frames)
    t = np.linspace(0, 2 * np.pi, total_frames)
    freqs = np.linspace(1, 3, n_bars)[:, None]
    mel_spec_norm = np.abs(np.sin(freqs * t))
    normalized_frame_energy = mel_spec_norm.mean(axis=0)
    dynamic_thresholds = np.zeros(n_bars)
    smoothed_spectrum = np.zeros(n_bars)
    peak_values = np.zeros(n_bars)
    peak_hold_counters = np.zeros(n_bars, dtype=int)

    frame_data = {
        "mel_spec_norm": mel_spec_norm,
        "normalized_frame_energy": normalized_frame_energy,
        "dynamic_thresholds": dynamic_thresholds,
        "smoothed_spectrum": smoothed_spectrum,
        "peak_values": peak_values,
        "peak_hold_counters": peak_hold_counters,
    }

    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{width}x{height}",
        "-pix_fmt", "rgba",
        "-r", str(fps),
        "-i", "-", "-c:v", "libx264", "-preset", "fast",
        "-crf", "23", "-pix_fmt", "yuv420p", output_path
    ]
    print(f"Starting FFmpeg for Dual Bar Visualizer -> {output_path}")
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for frame_idx in range(total_frames):
        viz.update_frame_data(frame_data, frame_idx, conf)
        img = renderer.render_frame(
            frame_data["smoothed_spectrum"],
            frame_data["peak_values"],
            None, "", ""
        )
        proc.stdin.write(img.tobytes())
    proc.stdin.close()
    proc.wait()
    print(f"Dual Bar Visualizer test video saved to {output_path}")

def main():
    render_shaders()
    render_dual_bar()

if __name__ == "__main__":
    main()