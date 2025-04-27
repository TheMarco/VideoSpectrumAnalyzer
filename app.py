import os
import uuid
import json
from flask import (
    Flask,
    request,
    render_template,
    jsonify,
    send_from_directory,
    url_for,
)  # Added url_for
import subprocess
import threading
from werkzeug.utils import secure_filename
import traceback  # Keep for debugging

# Import your visualizer script - make sure this file is in the same directory
from visualizer import create_spectrum_analyzer

app = Flask(__name__, static_folder="static")  # Explicitly define static folder
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["OUTPUT_FOLDER"] = "outputs"
app.config["MAX_CONTENT_LENGTH"] = (
    1600 * 1024 * 1024
)  # Increased significantly for video

# Create necessary directories
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)

# Store job status
jobs = {}


# Helper to parse hex color (Unchanged)
def parse_hex_color(hex_color, default=(255, 255, 255)):
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
    if "file" not in request.files:
        return jsonify({"error": "No audio file part"}), 400

    audio_file = request.files["file"]
    if audio_file.filename == "":
        return jsonify({"error": "No selected audio file"}), 400

    # Determine background type and handle upload
    background_image_file = request.files.get("background_image")
    background_video_file = request.files.get(
        "background_video"
    )  # <-- New video file input
    background_image_path = None
    background_image_filename = None
    background_video_path = None
    background_video_filename = None

    # Generate unique ID for this job
    job_id = str(uuid.uuid4())

    # Save the uploaded audio file
    audio_filename = secure_filename(audio_file.filename)
    audio_file_path = os.path.join(
        app.config["UPLOAD_FOLDER"], f"{job_id}_{audio_filename}"
    )
    audio_file.save(audio_file_path)

    # Prioritize video if both are somehow sent, otherwise save the provided background
    if background_video_file and background_video_file.filename != "":
        # Add size validation for video (e.g., 1GB limit)
        # Note: Flask/Werkzeug might struggle streaming very large files directly.
        # Consider chunked uploads or external storage for production with huge files.
        # A basic check here:
        if (
            background_video_file.content_length > 1000 * 1024 * 1024
        ):  # 1GB Limit example
            return (
                jsonify({"error": "Background video file is too large (max 1GB)"}),
                400,
            )

        ext = os.path.splitext(background_video_file.filename)[1].lower()
        # Add common video extensions
        if ext not in [".mp4", ".mov", ".avi", ".webm", ".mkv"]:
            return (
                jsonify(
                    {
                        "error": "Invalid background video format (use MP4, MOV, AVI, WEBM, MKV)"
                    }
                ),
                400,
            )

        background_video_filename = f"{job_id}_background{ext}"
        background_video_path = os.path.join(
            app.config["UPLOAD_FOLDER"], background_video_filename
        )
        try:
            background_video_file.save(background_video_path)
            print(f"Saved background video to: {background_video_path}")
        except Exception as e:
            print(f"Error saving background video: {e}")
            return jsonify({"error": f"Failed to save background video: {e}"}), 500
        background_image_path = None  # Ensure only video path is used if video provided

    elif background_image_file and background_image_file.filename != "":
        # Keep existing image validation
        if (
            background_image_file.content_length > 50 * 1024 * 1024
        ):  # 50MB limit for background image
            return (
                jsonify({"error": "Background image file is too large (max 50MB)"}),
                400,
            )
        ext = os.path.splitext(background_image_file.filename)[1].lower()
        if ext not in [".png", ".jpg", ".jpeg", ".webp"]:
            return (
                jsonify(
                    {
                        "error": "Invalid background image format (use PNG, JPG, JPEG, WEBP)"
                    }
                ),
                400,
            )

        background_image_filename = f"{job_id}_background{ext}"
        background_image_path = os.path.join(
            app.config["UPLOAD_FOLDER"], background_image_filename
        )
        background_image_file.save(background_image_path)
        print(f"Saved background image to: {background_image_path}")
        background_video_path = None  # Ensure only image path is used

    # --- Rest of the config parsing is mostly the same ---
    # (Removed debug prints for brevity)

    # Get configuration from form
    config = {
        "artist_name": request.form.get("artist_name", ""),
        "track_title": request.form.get("track_title", ""),
        "artist_color": request.form.get("artist_color", "#FFFFFF"),
        "title_color": request.form.get("title_color", "#FFFFFF"),
        "n_bars": int(request.form.get("n_bars", 20)),
        "bar_width": int(request.form.get("bar_width", 40)),
        "bar_gap": int(request.form.get("bar_gap", 2)),
        "amplitude_scale": float(request.form.get("amplitude_scale", 0.6)),
        "sensitivity": float(request.form.get("sensitivity", 1.0)),
        "analyzer_alpha": float(request.form.get("analyzer_alpha", 1.0)),
        "segment_height": int(request.form.get("segment_height", 6)),
        "segment_gap": int(request.form.get("segment_gap", 6)),
        "corner_radius": int(request.form.get("corner_radius", 4)),
        "min_freq": int(request.form.get("min_freq", 30)),
        "max_freq": int(request.form.get("max_freq", 16000)),
        "threshold_factor": float(request.form.get("threshold_factor", 0.3)),
        "attack_speed": float(request.form.get("attack_speed", 0.95)),
        "decay_speed": float(request.form.get("decay_speed", 0.25)),
        "peak_hold_frames": int(request.form.get("peak_hold_frames", 5)),
        "peak_decay_speed": float(request.form.get("peak_decay_speed", 0.15)),
        "bass_threshold_adjust": float(request.form.get("bass_threshold_adjust", 1.2)),
        "mid_threshold_adjust": float(request.form.get("mid_threshold_adjust", 1.0)),
        "high_threshold_adjust": float(request.form.get("high_threshold_adjust", 0.9)),
        "silence_threshold": float(request.form.get("silence_threshold", 0.04)),
        "silence_decay_factor": float(request.form.get("silence_decay_factor", 0.5)),
        "noise_gate": float(request.form.get("noise_gate", 0.08)),
        "duration": float(request.form.get("duration", 0)) or None,
        "fps": int(request.form.get("fps", 30)),
        "width": int(request.form.get("width", 1280)),
        "height": int(request.form.get("height", 720)),
        "always_on_bottom": str(request.form.get("always_on_bottom")).lower()
        in ("on", "true"),
        "use_gradient": request.form.get("use_gradient") == "on",
        "gradient_top_color": (200, 200, 255),
        "gradient_bottom_color": (255, 255, 255),
        "gradient_exponent": float(request.form.get("gradient_exponent", 0.7)),
        "background_color": (0, 0, 0),
    }

    # Save configuration
    with open(
        os.path.join(app.config["UPLOAD_FOLDER"], f"{job_id}_config.json"), "w"
    ) as f:
        json.dump(
            config, f, default=lambda x: list(x) if isinstance(x, tuple) else str(x)
        )

    # Set initial job status, now including both background paths potentially
    output_filename = f"{job_id}_output.mp4"
    output_path = os.path.join(app.config["OUTPUT_FOLDER"], output_filename)
    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "input_file": audio_file_path,
        "background_image_file": background_image_path,  # Store image path
        "background_video_file": background_video_path,  # Store video path
        "output_file": output_path,
        "config": config,
    }

    # Start processing in a background thread
    # Pass both background paths to the processing function
    thread = threading.Thread(
        target=process_video,
        args=(
            job_id,
            audio_file_path,
            background_image_path,
            background_video_path,  # <-- Pass video path
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


# Updated function signature to accept video path
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

        # Create a progress callback function
        def update_progress(progress):
            jobs[job_id]["progress"] = progress

        # Call visualizer function, passing both background paths
        create_spectrum_analyzer(
            audio_file=input_file,
            background_image_path=background_image_file,  # Pass image path
            background_video_path=background_video_file,  # Pass video path
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
    # Avoid sending full file paths back to the client if desired
    # job_data.pop('input_file', None)
    # job_data.pop('background_image_file', None)
    # job_data.pop('background_video_file', None)
    # job_data.pop('output_file', None)
    return jsonify(job_data)


@app.route("/download/<job_id>", methods=["GET"])
def download_file(job_id):
    if job_id not in jobs or jobs[job_id]["status"] != "completed":
        return jsonify({"error": "File not ready or job not found"}), 404

    directory = os.path.abspath(app.config["OUTPUT_FOLDER"])
    filename = os.path.basename(jobs[job_id]["output_file"])

    # Optional cleanup could go here
    # Be careful cleaning inputs if multiple jobs might share them (though UUIDs make this unlikely)

    return send_from_directory(directory, filename, as_attachment=True)


if __name__ == "__main__":
    # Use waitress or gunicorn for production instead of Flask's debug server
    # For development:
    app.run(debug=True, host="0.0.0.0", port=8080)
