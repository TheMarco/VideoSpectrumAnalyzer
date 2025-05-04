import os
import uuid
import json
from flask import Flask, request, render_template, jsonify, send_from_directory, url_for
import subprocess
import threading
from werkzeug.utils import secure_filename
import traceback

# Import core components
from core.registry import registry
from core.utils import is_image_file, is_video_file

app = Flask(__name__, static_folder="static")
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["OUTPUT_FOLDER"] = "outputs"
app.config["MAX_CONTENT_LENGTH"] = 1600 * 1024 * 1024 # 1.6 GB total request size limit

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)
os.makedirs(os.path.join("static", "images", "thumbnails"), exist_ok=True)

# Discover available visualizers
registry.discover_visualizers()
print(f"Discovered visualizers: {registry.get_visualizer_names()}")

jobs = {}

# Allowed extensions (adjust as needed)
ALLOWED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp'}
ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.webm', '.mkv'}
MAX_IMAGE_SIZE = 50 * 1024 * 1024 # 50 MB
MAX_VIDEO_SIZE = 1000 * 1024 * 1024 # 1 GB (1000 MB)


@app.route("/")
def index():
    visualizers = registry.get_all_visualizers()
    return render_template("index.html", visualizers=visualizers)

@app.route("/visualizer/<name>")
def visualizer_form(name):
    visualizer = registry.get_visualizer(name)
    if not visualizer:
        return render_template("error.html", message=f"Visualizer '{name}' not found"), 404
    # Choose per-visualizer form template
    if visualizer.name == "Dual Bar Visualizer":
        template = "dual_bar_visualizer_form.html"
    elif visualizer.name == "Spectrum Analyzer":
        template = "spectrum_analyzer_form.html"
    else:
        template = "visualizer_form.html"
    return render_template(template, visualizer=visualizer)


@app.route("/upload", methods=["POST"])
def upload_file():
    # Get the visualizer name from the form
    visualizer_name = request.form.get("visualizer_name")
    if not visualizer_name:
        return jsonify({"error": "No visualizer specified"}), 400

    # Get the visualizer instance
    visualizer = registry.get_visualizer(visualizer_name)
    if not visualizer:
        return jsonify({"error": f"Visualizer '{visualizer_name}' not found"}), 404

    # --- Basic File Handling (Audio) ---
    if "file" not in request.files:
        return jsonify({"error": "No audio file part"}), 400
    audio_file = request.files["file"]
    if audio_file.filename == "":
        return jsonify({"error": "No selected audio file"}), 400

    job_id = str(uuid.uuid4())
    audio_filename = secure_filename(audio_file.filename)
    audio_file_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{job_id}_{audio_filename}")
    try:
        audio_file.save(audio_file_path)
    except Exception as e:
         print(f"Error saving audio file: {e}")
         return jsonify({"error": f"Failed to save audio file: {e}"}), 500

    # --- Unified Background Media Handling ---
    background_media_file = request.files.get("background_media")
    background_image_path = None
    background_video_path = None

    if background_media_file and background_media_file.filename != "":
        filename = secure_filename(background_media_file.filename)
        ext = os.path.splitext(filename)[1].lower()
        temp_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{job_id}_temp_background{ext}") # Save temporarily first

        try:
            background_media_file.save(temp_path)
            file_size = os.path.getsize(temp_path)

            if ext in ALLOWED_VIDEO_EXTENSIONS:
                if file_size > MAX_VIDEO_SIZE:
                    os.remove(temp_path) # Clean up oversized file
                    return jsonify({"error": f"Background video file is too large (max {MAX_VIDEO_SIZE // (1024*1024)}MB)"}), 400
                # Rename to final video path
                background_video_filename = f"{job_id}_background{ext}"
                background_video_path = os.path.join(app.config["UPLOAD_FOLDER"], background_video_filename)
                os.rename(temp_path, background_video_path)
                print(f"Saved background video: {background_video_path}")
                background_image_path = None # Ensure image path is None

            elif ext in ALLOWED_IMAGE_EXTENSIONS:
                if file_size > MAX_IMAGE_SIZE:
                     os.remove(temp_path) # Clean up oversized file
                     return jsonify({"error": f"Background image file is too large (max {MAX_IMAGE_SIZE // (1024*1024)}MB)"}), 400
                # Rename to final image path
                background_image_filename = f"{job_id}_background{ext}"
                background_image_path = os.path.join(app.config["UPLOAD_FOLDER"], background_image_filename)
                os.rename(temp_path, background_image_path)
                print(f"Saved background image: {background_image_path}")
                background_video_path = None # Ensure video path is None

            else:
                os.remove(temp_path) # Clean up invalid file
                return jsonify({"error": "Invalid background file format. Use common image or video types."}), 400

        except Exception as e:
            print(f"Error saving/processing background media: {e}")
            # Clean up temp file if it exists on error
            if os.path.exists(temp_path):
                try: os.remove(temp_path)
                except OSError: pass
            return jsonify({"error": f"Failed to save or process background media: {e}"}), 500
    # --- End Background Media Handling ---

    # --- Get Configuration from form ---
    # Convert form data to a dictionary
    config = {}
    for key, value in request.form.items():
        if key != "visualizer_name":  # Skip the visualizer name
            config[key] = value

    # Process specific types
    for key in config:
        # Convert numeric values
        if key in ["n_bars", "bar_width", "bar_gap", "segment_height", "segment_gap",
                  "corner_radius", "peak_hold_frames", "min_freq", "max_freq",
                  "fps", "width", "height", "max_segments", "max_amplitude"]:
            try:
                config[key] = int(config[key])
            except (ValueError, TypeError):
                pass

        # Convert float values
        elif key in ["amplitude_scale", "sensitivity", "analyzer_alpha", "threshold_factor",
                    "attack_speed", "decay_speed", "peak_decay_speed", "bass_threshold_adjust",
                    "mid_threshold_adjust", "high_threshold_adjust", "silence_threshold",
                    "silence_decay_factor", "noise_gate", "duration"]:
            try:
                config[key] = float(config[key])
            except (ValueError, TypeError):
                pass

        # Convert boolean values
        elif key in ["always_on_bottom", "use_gradient"]:
            if isinstance(config[key], str):
                config[key] = config[key].lower() in ("true", "on", "yes", "1")
            else:
                config[key] = bool(config[key])

    # Handle special case for duration
    if "duration" in config and (config["duration"] == 0 or config["duration"] == "0"):
        config["duration"] = None

    # Add default background color
    config["background_color"] = (0, 0, 0)  # Fallback solid color

    # Debug print
    print(f"Processed configuration: {config}")

    # Add important default values if not present
    if "n_bars" not in config:
        config["n_bars"] = 40
    if "amplitude_scale" not in config:
        config["amplitude_scale"] = 0.6
    if "sensitivity" not in config:
        config["sensitivity"] = 1.0

    # Save configuration
    config_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{job_id}_config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, default=lambda x: list(x) if isinstance(x, tuple) else str(x))
    print(f"Saved config to: {config_path}")

    # Set initial job status
    output_filename = f"{job_id}_output.mp4"
    output_path = os.path.join(app.config["OUTPUT_FOLDER"], output_filename)
    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "visualizer": visualizer_name,
        "input_file": audio_file_path,
        "background_image_file": background_image_path,
        "background_video_file": background_video_path,
        "output_file": output_path,
        "config": config,
    }

    # Start processing in a background thread
    thread = threading.Thread(
        target=process_video,
        args=(
            job_id,
            visualizer,
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


def process_video(
    job_id,
    visualizer,
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

        # Use the visualizer to create the visualization
        visualizer.create_visualization(
            audio_file=input_file,
            background_image_path=background_image_file,
            background_video_path=background_video_file,
            output_file=output_file,
            artist_name=config.get("artist_name", ""),
            track_title=config.get("track_title", ""),
            duration=config.get("duration"),
            fps=config.get("fps", 30),
            height=config.get("height", 720),
            width=config.get("width", 1280),
            config=config,
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
    # Ensure sensitive paths aren't sent to client if needed, but okay for now
    return jsonify(job_data)


@app.route("/download/<job_id>", methods=["GET"])
def download_file(job_id):
    if job_id not in jobs or jobs[job_id]["status"] != "completed":
        return jsonify({"error": "File not ready or job not found"}), 404
    directory = os.path.abspath(app.config["OUTPUT_FOLDER"])
    filename = os.path.basename(jobs[job_id]["output_file"])
    return send_from_directory(directory, filename, as_attachment=True)


if __name__ == "__main__":
    # Use host='0.0.0.0' for accessibility on network, debug=False for production
    app.run(debug=True, host="0.0.0.0", port=8080)
