# Audio Visualizer Suite

This web application generates a spectrum analyzer video visualization for an audio file. You can upload an audio file, optionally provide a background image, configure various visualizer parameters through a web interface, and download the resulting MP4 video.

## Features

*   Web-based interface for easy configuration.
*   Generates MP4 video with audio synced to visuals.
*   Customizable spectrum analyzer:
    *   Number of bars, width, gap
    *   Colors for bars, artist/title text
    *   Amplitude scaling and sensitivity
    *   Segment appearance (height, gap, corner radius)
    *   Frequency range filtering
    *   Attack/decay smoothing
    *   Peak holding
    *   Optional static bottom segment
    *   Optional color gradient for bars
    *   Noise gating and silence handling
*   Optional custom background image.
*   Background processing with job status updates.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

1.  **Python:** Version 3.8 or newer recommended. ([Download Python](https://www.python.org/downloads/))
2.  **pip:** The Python package installer (usually comes with Python).
3.  **ffmpeg:** This is **essential** for video encoding and adding audio back to the generated video. The application **will not work** without it.
    *   **Website:** [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
    *   **Installation Guides:** Follow the instructions for your operating system (Windows, macOS, Linux).
    *   **Verification:** Make sure the `ffmpeg` command is accessible from your terminal/command prompt (i.e., it's in your system's PATH). You can test by opening a terminal and typing `ffmpeg -version`.

## Installation

1.  **Clone or Download:**
    Get the project files. If you have Git installed:
    ```bash
    git clone <repository-url> # Replace with your repo URL if applicable
    cd <repository-directory>
    ```
    Alternatively, download the `app.py`, `visualizer.py`, `requirements.txt`, and the `templates/index.html` and `static` folders and place them in a project directory.

2.  **Create a Virtual Environment (Recommended):**
    It's best practice to create a virtual environment to isolate project dependencies.
    ```bash
    # Navigate to your project directory in the terminal
    python -m venv venv
    ```

3.  **Activate the Virtual Environment:**
    *   **Windows (cmd.exe):**
        ```bash
        venv\Scripts\activate.bat
        ```
    *   **Windows (PowerShell):**
        ```bash
        venv\Scripts\Activate.ps1
        ```
        (If you encounter execution policy issues, you might need to run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` first).
    *   **macOS / Linux (bash/zsh):**
        ```bash
        source venv/bin/activate
        ```
    Your terminal prompt should now indicate that you are in the `(venv)`.

4.  **Install Python Dependencies:**
    Install all the required Python libraries listed in `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

1.  **Ensure Prerequisites:** Double-check that Python, pip, and especially **ffmpeg** are installed correctly.
2.  **Activate Virtual Environment:** If you created one, make sure it's activated (see Installation Step 3).
3.  **Start the Flask Server:**
    Run the `app.py` script from your project's root directory in the terminal:
    ```bash
    python app.py
    ```
4.  **Access the Web UI:**
    Open your web browser and navigate to:
    [http://127.0.0.1:8080/](http://127.0.0.1:8080/) or [http://localhost:8080/](http://localhost:8080/)
    (The server might also listen on `0.0.0.0`, check the terminal output).

## Usage

1.  **Upload Audio:** Click the "Choose File" button under "Audio File" to select your desired audio file (e.g., MP3, WAV, FLAC).
2.  **Upload Background (Optional):** Click "Choose File" under "Background Image" to select an image (PNG, JPG, WEBP). If omitted, a solid black background is used.
3.  **Configure Text:** Enter Artist Name and Track Title, and select their colors if desired.
4.  **Configure Visualizer:** Adjust the various sliders, number inputs, checkboxes, and color pickers to customize the look and behavior of the spectrum analyzer. Hover over labels or check `visualizer.py` for details on each parameter.
5.  **Submit:** Click the "Create Visualization" button.
6.  **Monitor Progress:** The page will show the job status ("queued", "processing", "completed", "failed") and a progress bar while the video is generated. This can take time depending on the audio length and your computer's speed.
7.  **Download:** Once the status shows "completed", a download button will appear. Click it to save your generated MP4 video file.
8.  **Errors:** If the status becomes "failed", check the terminal window where you ran `python app.py` for error messages (common causes include missing `ffmpeg` or issues with the input files).

## Notes

*   Ensure input audio files are not corrupted.
*   Very long audio files will require significant processing time and disk space.
*   The default Flask development server is not recommended for production. For deployment, consider using a production-ready WSGI server like Gunicorn or Waitress.
