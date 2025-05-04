# Audio Visualizer Suite

Audio Visualizer Suite is a powerful web application that transforms audio files into stunning visual experiences. Create professional-quality music visualizations with customizable parameters, background images or videos, and artist information overlays.

## Features

### Multiple Visualizer Types
* **Spectrum Analyzer**: Classic frequency bars with customizable appearance and peak indicators
* **Dual Bar Visualizer**: Symmetrical bars that grow both up and down from a center line

### Comprehensive Customization
* **Appearance**: Control bar count, width, gap, colors, transparency, and more
* **Text Overlay**: Display artist name and track title with customizable colors and sizes
* **Dynamics**: Adjust sensitivity, attack/decay speeds, and frequency response
* **Output**: Configure video resolution, frame rate, and duration

### Advanced Options
* **Background Media**: Use static images or videos as backgrounds
* **Glow Effects**: Add subtle glow behind bars and text
* **Frequency Filtering**: Customize frequency range and response curves
* **Silence Handling**: Special behavior during quiet passages

### User Experience
* **Tabbed Interface**: Organized settings for easy configuration
* **Real-time Validation**: Form validation with helpful error messages
* **Progress Tracking**: Monitor processing with status updates and progress bar
* **Preview & Download**: Watch your visualization and download the final MP4

## Prerequisites

Before you begin, ensure you have the following installed:

1. **Python**: Version 3.8 or newer ([Download Python](https://www.python.org/downloads/))
2. **pip**: The Python package installer (included with Python)
3. **FFmpeg**: **Essential** for video processing ([FFmpeg Download](https://ffmpeg.org/download.html))
   * Verify installation by running `ffmpeg -version` in your terminal

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/AudioVisualizerSuite.git
   cd AudioVisualizerSuite
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the Virtual Environment**:
   * **Windows**:
     ```bash
     venv\Scripts\activate
     ```
   * **macOS/Linux**:
     ```bash
     source venv/bin/activate
     ```

4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. **Start the Server**:
   ```bash
   python app.py
   ```

2. **Access the Web Interface**:
   Open your browser and navigate to:
   [http://localhost:8080](http://localhost:8080)

## Creating Visualizations

1. **Select a Visualizer**: Choose from the available visualizer types on the home page
2. **Upload Audio**: Select your audio file (MP3, WAV, FLAC, etc.)
3. **Add Background** (Optional): Upload an image or video to use as background
4. **Configure Settings**: Navigate through the tabs to customize your visualization:
   * **Input Files & Info**: Upload files and set artist/title information
   * **Appearance**: Adjust visual elements like bars, colors, and transparency
   * **Reactivity**: Fine-tune how the visualizer responds to audio
   * **Advanced & Output**: Set video parameters and specialized options
5. **Generate**: Click "Generate Visualization" and monitor the progress
6. **Preview & Download**: When processing completes, preview your visualization and download the MP4 file

## Extending the Application

Audio Visualizer Suite is designed with modularity in mind. You can create new visualizer types by:

1. Creating a new directory under `visualizers/` with your visualizer name
2. Implementing the required files:
   * `__init__.py`: Package initialization
   * `visualizer.py`: Main visualizer class inheriting from `BaseVisualizer`
   * `config.py`: Configuration processing
   * `renderer.py`: Rendering implementation
3. Creating a form template in `templates/[visualizer_name]_form.html`
4. Adding JavaScript in `static/js/[visualizer_name]_form.js`

See `docs/module_structure.md` for detailed guidance on the architecture.
