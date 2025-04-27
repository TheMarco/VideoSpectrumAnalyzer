import os
import uuid
import json
from flask import Flask, request, render_template, jsonify, send_from_directory, url_for
import subprocess
import threading
from werkzeug.utils import secure_filename
import traceback

from visualizer import create_spectrum_analyzer

app = Flask(__name__, static_folder="static")
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["OUTPUT_FOLDER"] = "outputs"
app.config["MAX_CONTENT_LENGTH"] = 1600 * 1024 * 1024

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)

jobs = {}


# (parse_hex_color helper remains unchanged)
def parse_hex_color(hex_color, default=(255, 255, 255)):
    # ... (implementation unchanged) ...
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 6:
        try:
            return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            return default
    return default


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    # --- File Handling (Audio, Background Image/Video) ---
    # ... (This part remains unchanged from the previous version) ...
    if "file" not in request.files:
        return jsonify({"error": "No audio file part"}), 400
    audio_file = request.files["file"]
    if audio_file.filename == "":
        return jsonify({"error": "No selected audio file"}), 400
    background_image_file = request.files.get("background_image")
    background_video_file = request.files.get("background_video")
    background_image_path = None
    background_video_path = None
    job_id = str(uuid.uuid4())
    audio_filename = secure_filename(audio_file.filename)
    audio_file_path = os.path.join(
        app.config["UPLOAD_FOLDER"], f"{job_id}_{audio_filename}"
    )
    audio_file.save(audio_file_path)
    if background_video_file and background_video_file.filename != "":
        if background_video_file.content_length > 1000 * 1024 * 1024:
            return (
                jsonify({"error": "Background video file is too large (max 1GB)"}),
                400,
            )
        ext = os.path.splitext(background_video_file.filename)[1].lower()
        if ext not in [".mp4", ".mov", ".avi", ".webm", ".mkv"]:
            return jsonify({"error": "Invalid background video format"}), 400
        background_video_filename = f"{job_id}_background{ext}"
        background_video_path = os.path.join(
            app.config["UPLOAD_FOLDER"], background_video_filename
        )
        try:
            background_video_file.save(background_video_path)
            print(f"Saved background video: {background_video_path}")
        except Exception as e:
            print(f"Error saving background video: {e}")
            return jsonify({"error": f"Failed to save background video: {e}"}), 500
        background_image_path = None
    elif background_image_file and background_image_file.filename != "":
        if background_image_file.content_length > 50 * 1024 * 1024:
            return jsonify({"error": "Background image file too large (max 50MB)"}), 400
        ext = os.path.splitext(background_image_file.filename)[1].lower()
        if ext not in [".png", ".jpg", ".jpeg", ".webp"]:
            return jsonify({"error": "Invalid background image format"}), 400
        background_image_filename = f"{job_id}_background{ext}"
        background_image_path = os.path.join(
            app.config["UPLOAD_FOLDER"], background_image_filename
        )
        background_image_file.save(background_image_path)
        print(f"Saved background image: {background_image_path}")
        background_video_path = None
    # --- End File Handling ---

    # --- Get Configuration ---
    config = {
        # Basic Info
        "artist_name": request.form.get("artist_name", ""),
        "track_title": request.form.get("track_title", ""),
        "artist_color": request.form.get("artist_color", "#FFFFFF"),
        "title_color": request.form.get("title_color", "#FFFFFF"),
        # Visualizer Appearance
        "n_bars": int(request.form.get("n_bars", 20)),
        "bar_width": int(request.form.get("bar_width", 40)),
        "bar_gap": int(request.form.get("bar_gap", 2)),
        "segment_height": int(request.form.get("segment_height", 6)),
        "segment_gap": int(request.form.get("segment_gap", 6)),
        "corner_radius": int(request.form.get("corner_radius", 4)),
        "analyzer_alpha": float(request.form.get("analyzer_alpha", 1.0)),
        # ****** ADDED BAR COLOR FETCH ******
        "bar_color": request.form.get(
            "bar_color", "#FFFFFF"
        ),  # Fetch the new bar color
        # ****** END ADD ******
        "use_gradient": request.form.get("use_gradient") == "on",
        "always_on_bottom": str(request.form.get("always_on_bottom")).lower()
        in ("on", "true"),
        # Advanced: Reactivity
        "amplitude_scale": float(request.form.get("amplitude_scale", 0.6)),
        "sensitivity": float(request.form.get("sensitivity", 1.0)),
        "threshold_factor": float(request.form.get("threshold_factor", 0.3)),
        "attack_speed": float(request.form.get("attack_speed", 0.95)),
        "decay_speed": float(request.form.get("decay_speed", 0.25)),
        "noise_gate": float(request.form.get("noise_gate", 0.08)),
        # Advanced: Peaks
        "peak_hold_frames": int(request.form.get("peak_hold_frames", 5)),
        "peak_decay_speed": float(request.form.get("peak_decay_speed", 0.15)),
        # Advanced: Frequency & Thresholds
        "min_freq": int(request.form.get("min_freq", 30)),
        "max_freq": int(request.form.get("max_freq", 16000)),
        "bass_threshold_adjust": float(request.form.get("bass_threshold_adjust", 1.2)),
        "mid_threshold_adjust": float(request.form.get("mid_threshold_adjust", 1.0)),
        "high_threshold_adjust": float(request.form.get("high_threshold_adjust", 0.9)),
        # Advanced: Silence
        "silence_threshold": float(request.form.get("silence_threshold", 0.04)),
        "silence_decay_factor": float(request.form.get("silence_decay_factor", 0.5)),
        # Advanced: Gradient
        "gradient_top_color": (
            200,
            200,
            255,
        ),  # Could make these configurable too eventually
        "gradient_bottom_color": (255, 255, 255),
        "gradient_exponent": float(request.form.get("gradient_exponent", 0.7)),
        # Video Output
        "duration": float(request.form.get("duration", 0)) or None,
        "fps": int(request.form.get("fps", 30)),
        "width": int(request.form.get("width", 1280)),
        "height": int(request.form.get("height", 720)),
        # Other
        "background_color": (0, 0, 0),  # Fallback solid color
    }
    # --- End Configuration ---

    # Save configuration
    config_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{job_id}_config.json")
    with open(config_path, "w") as f:
        json.dump(
            config, f, default=lambda x: list(x) if isinstance(x, tuple) else str(x)
        )
    print(f"Saved config to: {config_path}")

    # Set initial job status
    output_filename = f"{job_id}_output.mp4"
    output_path = os.path.join(app.config["OUTPUT_FOLDER"], output_filename)
    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "input_file": audio_file_path,
        "background_image_file": background_image_path,
        "background_video_file": background_video_path,
        "output_file": output_path,
        "config": config,  # Config dict is stored here
    }

    # Start processing in a background thread
    thread = threading.Thread(
        target=process_video,
        args=(
            job_id,
            audio_file_path,
            background_image_path,
            background_video_path,
            output_path,
            config,
        ),
    )
    thread.daemon = True
    thread.start()

    return jsonify(
        {
            "job_id": job_id,
            "status": "queued",
            "message": "File uploaded and processing started",
        }
    )


# --- process_video, job_status, download_file (remain unchanged) ---
def process_video(
    job_id,
    input_file,
    background_image_file,
    background_video_file,
    output_file,
    config,
):
    try:
        jobs[job_id]["status"] = "processing"

        def update_progress(progress):
            jobs[job_id]["progress"] = progress

        create_spectrum_analyzer(
            audio_file=input_file,
            background_image_path=background_image_file,
            background_video_path=background_video_file,
            output_file=output_file,
            artist_name=config["artist_name"],
            track_title=config["track_title"],
            duration=config["duration"],
            fps=config["fps"],
            height=config["height"],
            width=config["width"],
            config=config,  # Pass the whole config dict
            progress_callback=update_progress,
        )
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 100
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Error processing job {job_id}: {e}")
        traceback.print_exc()


@app.route("/job_status/<job_id>", methods=["GET"])
def job_status(job_id):
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    job_data = jobs[job_id].copy()
    return jsonify(job_data)


@app.route("/download/<job_id>", methods=["GET"])
def download_file(job_id):
    if job_id not in jobs or jobs[job_id]["status"] != "completed":
        return jsonify({"error": "File not ready or job not found"}), 404
    directory = os.path.abspath(app.config["OUTPUT_FOLDER"])
    filename = os.path.basename(jobs[job_id]["output_file"])
    return send_from_directory(directory, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
