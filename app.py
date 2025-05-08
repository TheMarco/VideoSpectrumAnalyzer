import os
import uuid
import json
from flask import Flask, request, render_template, jsonify, send_from_directory, url_for
import subprocess
import threading
from werkzeug.utils import secure_filename
import traceback
import glob
import re

# Import core components
from core.registry import registry
from core.utils import is_image_file, is_video_file
from visualizers.oscilloscope_waveform.visualizer import OscilloscopeWaveformVisualizer # Import the specific visualizer class

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

def get_available_shaders():
    """Get a list of all available GLSL shaders in the glsl directory."""
    shader_files = glob.glob("glsl/*.glsl")
    # Filter out optical_deconstruction shader as per user preference
    # Also filter out audioreactive shaders (those starting with "ar_")
    shader_files = [f for f in shader_files if "optical_deconstruction" not in f and not os.path.basename(f).startswith("ar_")]
    shaders = []

    for shader_path in shader_files:
        # Get just the filename without extension
        shader_name = os.path.basename(shader_path).replace(".glsl", "")
        # Convert to title case for display (e.g., "biomine" -> "Biomine")
        display_name = shader_name.replace("_", " ").title()

        # Check if a preview video exists for this shader
        preview_path = f"glsl/previews/{shader_name}.mp4"
        has_preview = os.path.exists(preview_path)

        shaders.append({
            "path": shader_path,
            "name": display_name,
            "preview_path": preview_path if has_preview else None
        })

    return sorted(shaders, key=lambda x: x["name"])

@app.route("/")
def index():
    """Render the home page with all available visualizers."""
    visualizers = registry.get_all_visualizers()

    # Hide the audioreactive visualizer unless dev=true is in the URL
    dev_mode = request.args.get('dev', '').lower() == 'true'
    if not dev_mode:
        # Filter out the AudioreactiveShaderVisualizer
        visualizers = [v for v in visualizers if v['name'] != 'AudioreactiveShaderVisualizer']

    shaders = get_available_shaders()
    return render_template("index.html", visualizers=visualizers, shaders=shaders, dev_mode=dev_mode)

@app.route("/visualizer/<name>")
def visualizer_form(name):
    """Render the form for a specific visualizer."""
    visualizer = registry.get_visualizer(name)
    if not visualizer:
        return render_template("error.html", message=f"Visualizer '{name}' not found")

    # Get available shaders - for audioreactive shader, use its own method
    if hasattr(visualizer, 'get_available_shaders'):
        shaders = visualizer.get_available_shaders()
    else:
        shaders = get_available_shaders()

    template = visualizer.get_config_template()
    return render_template(template, visualizer=visualizer, shaders=shaders)


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
            config.get("background_shader_path"),  # Add shader path
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
    background_shader_file,  # Parameter for shader path
    output_file,
    config,
):
    try:
        jobs[job_id]["status"] = "processing"

        def update_progress(progress, message=None):
            print(f"DEBUG: Progress callback called with progress={progress}, message={message}")
            jobs[job_id]["progress"] = progress
            if message:
                jobs[job_id]["message"] = message
                print(f"DEBUG: Setting job message to: {message}")

            # Debug: Print current job state
            print(f"DEBUG: Current job state: {jobs[job_id]}")

        # Use the visualizer to create the visualization
        try:
            visualizer.create_visualization(
                audio_file=input_file,
                background_image_path=background_image_file,
                background_video_path=background_video_file,
                background_shader_path=background_shader_file,  # Pass shader path
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
    # Debug: Print job data being sent to client
    print(f"DEBUG: Sending job data to client: {job_data}")
    # Ensure sensitive paths aren't sent to client if needed, but okay for now
    return jsonify(job_data)

@app.route("/debug_job_status/<job_id>", methods=["GET"])
def debug_job_status(job_id):
    """Debug route to display the current job status as HTML."""
    if job_id == "latest" and jobs:
        # Get the most recent job
        job_id = list(jobs.keys())[-1]
        print(f"Using latest job ID: {job_id}")

    if job_id not in jobs:
        # List all available jobs
        job_list = "<ul>"
        for jid in jobs:
            job_list += f'<li><a href="/debug_job_status/{jid}">{jid}</a> - {jobs[jid].get("status", "unknown")}</li>'
        job_list += "</ul>"

        return f"""
        <h1>Job not found: {job_id}</h1>
        <h2>Available jobs:</h2>
        {job_list}
        """

    job_data = jobs[job_id]

    html = f"""
    <html>
    <head>
        <title>Job Status Debug</title>
        <meta http-equiv="refresh" content="2">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .job-info {{ margin-bottom: 20px; }}
            .progress {{ background-color: #f0f0f0; height: 20px; border-radius: 5px; margin-bottom: 10px; }}
            .progress-bar {{ background-color: #4CAF50; height: 100%; border-radius: 5px; text-align: center; color: white; }}
            .message {{ padding: 10px; background-color: #e0e0e0; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <h1>Job Status Debug</h1>
        <div class="job-info">
            <p><strong>Job ID:</strong> {job_id}</p>
            <p><strong>Status:</strong> {job_data.get('status', 'unknown')}</p>
            <p><strong>Visualizer:</strong> {job_data.get('visualizer', 'unknown')}</p>
        </div>

        <h2>Progress</h2>
        <div class="progress">
            <div class="progress-bar" style="width: {job_data.get('progress', 0)}%">
                {job_data.get('progress', 0)}%
            </div>
        </div>

        <h2>Message</h2>
        <div class="message">
            {job_data.get('message', 'No message')}
        </div>

        <h2>Full Job Data</h2>
        <pre>{json.dumps(job_data, indent=2)}</pre>
    </body>
    </html>
    """

    return html


@app.route("/download/<job_id>", methods=["GET"])
def download_file(job_id):
    if job_id not in jobs or jobs[job_id]["status"] != "completed":
        return jsonify({"error": "File not ready or job not found"}), 404
    directory = os.path.abspath(app.config["OUTPUT_FOLDER"])
    filename = os.path.basename(jobs[job_id]["output_file"])
    return send_from_directory(directory, filename, as_attachment=True)


@app.route("/stream/<job_id>", methods=["GET"])
def stream_file(job_id):
    if job_id not in jobs or jobs[job_id]["status"] != "completed":
        return jsonify({"error": "File not ready or job not found"}), 404
    directory = os.path.abspath(app.config["OUTPUT_FOLDER"])
    filename = os.path.basename(jobs[job_id]["output_file"])
    # Return the file for streaming (not as attachment)
    return send_from_directory(directory, filename, as_attachment=False)


@app.route("/shader-explorer")
def shader_explorer():
    """Render the shader explorer page with previews of all shaders."""
    # Get the referring page to allow returning to it
    referrer = request.referrer
    visualizer_name = None

    # Try to extract visualizer name from referrer URL if it exists
    if referrer and '/visualizer/' in referrer:
        try:
            visualizer_name = referrer.split('/visualizer/')[1].split('?')[0]
        except:
            pass

    # Get available shaders
    shaders = get_available_shaders()

    # Extract credits for each shader
    for shader in shaders:
        shader_path = shader['path']
        try:
            with open(shader_path, 'r') as f:
                content = f.read()

                # Look for credits between [C] and [/C] markers
                credit_match = re.search(r'\[C\](.*?)\[/C\]', content, re.DOTALL)
                if credit_match:
                    credit_line = credit_match.group(1).strip()
                    shader['credits'] = credit_line

                    # Check for URL in the credit line
                    url_match = re.search(r'https?://[^\s"\']+', credit_line)
                    if url_match:
                        shader['credit_url'] = url_match.group(0)
                        # Remove the URL from the displayed credit text
                        shader['credits'] = re.sub(r'\s*https?://[^\s"\']+\s*', '', credit_line).strip()
                    else:
                        shader['credit_url'] = None
                else:
                    shader['credits'] = None
                    shader['credit_url'] = None

        except Exception as e:
            print(f"Error extracting credits for {shader_path}: {e}")
            shader['credits'] = None
            shader['credit_url'] = None

    return render_template(
        "shader_explorer.html",
        shaders=shaders,
        visualizer_name=visualizer_name,
        referrer=referrer
    )


@app.route("/shader-preview/<path:shader_name>")
def shader_preview(shader_name):
    """Stream a shader preview video."""
    # The shader_name parameter will be something like "biomine"
    preview_path = f"glsl/previews/{shader_name}.mp4"

    if not os.path.exists(preview_path):
        return jsonify({"error": "Shader preview not found"}), 404

    directory = os.path.dirname(os.path.abspath(preview_path))
    filename = os.path.basename(preview_path)

    return send_from_directory(directory, filename, as_attachment=False)


if __name__ == "__main__":
    # Use host='0.0.0.0' for accessibility on network, debug=False for production
    app.run(debug=True, host="0.0.0.0", port=8080)
