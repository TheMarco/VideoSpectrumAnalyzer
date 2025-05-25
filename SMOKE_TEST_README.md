# Audio Visualizer Suite - Smoke Test

This directory contains comprehensive smoke tests for the Audio Visualizer Suite. The smoke tests verify that all visualizers work correctly with different background configurations and settings.

## What the Smoke Test Does

The smoke test runs each available visualizer with the following configurations:

1. **Plain** - No background, basic visualization
2. **With Background Image** - Static image background
3. **With Background Video** - Video background
4. **With Artist/Track Info** - Text overlay enabled
5. **With Background Image + Text** - Combined image background and text
6. **With Background Shaders** - GLSL shader backgrounds (first 3 available shaders)

For each test, a 1-second (or 3-second for full mode) video is generated and saved to the `smoketest/results/` directory.

## Files

- `run_smoke_test.py` - Main script to run all smoke tests
- `comprehensive_smoke_test.py` - Core smoke test implementation
- `prepare_test_media.py` - Script to prepare test media files
- `SMOKE_TEST_README.md` - This documentation

## Quick Start

### Basic Usage

```bash
# Run quick smoke tests (1 second per test) [default]
python3 run_smoke_test.py

# Run longer smoke tests (3 seconds per test)
python3 run_smoke_test.py --full

# Clean previous results and run fresh tests
python3 run_smoke_test.py --clean
```

### Prepare Test Media Only

```bash
# Just prepare test media without running tests
python3 run_smoke_test.py --prepare-only
```

## Requirements

- Python 3.7+
- All dependencies for the Audio Visualizer Suite
- FFmpeg (for generating test media)
- PIL/Pillow (for generating test images)

## Test Media

The smoke test uses the following media files:

### Audio Files
- Existing audio files from `uploads/` directory (preferred)
- Generated test audio (30-second sine wave) if no uploads exist

### Background Images
- `test_gradient.png` - Radial gradient image
- `test_pattern.png` - Geometric pattern image

### Background Videos
- Existing video files from `uploads/` directory (preferred)
- Generated test video (30-second test pattern) if no uploads exist

### Background Shaders
- First 3 non-audio-reactive shaders from `glsl/` directory
- Excludes shaders starting with `ar_` and known problematic shaders

## Output Structure

```
smoketest/
├── media/                          # Test media files
│   ├── test_gradient.png
│   ├── test_pattern.png
│   ├── test_background_video.mp4
│   └── generated_test_audio.wav
├── results/                        # Test results
│   ├── spectrum_analyzer/          # Results for Spectrum Analyzer
│   │   ├── plain.mp4
│   │   ├── with_image.mp4
│   │   ├── with_video.mp4
│   │   ├── with_artist_track.mp4
│   │   ├── with_image_and_text.mp4
│   │   └── with_shader_*.mp4
│   ├── dual_bar_visualizer/        # Results for Dual Bar Visualizer
│   │   └── ...
│   └── ...
└── smoke_test_report.txt           # Summary report
```

## Understanding Results

### Success Indicators
- ✓ Test completed successfully
- Output video file exists
- File size > 0 bytes
- No exceptions during rendering

### Failure Indicators
- ✗ Test failed
- No output file generated
- Exception during rendering
- Zero-byte output file

### Report File
The `smoke_test_report.txt` contains:
- Test date and time
- Total/passed/failed test counts
- Success rate percentage
- Detailed results for each visualizer and configuration

## Troubleshooting

### Common Issues

1. **No visualizers found**
   - Check that visualizer modules are properly installed
   - Some visualizers require `moderngl` - install with `pip install moderngl`

2. **FFmpeg not found**
   - Install FFmpeg: `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Ubuntu)
   - Ensure FFmpeg is in your PATH

3. **PIL/Pillow not available**
   - Install Pillow: `pip install Pillow`

4. **Test media creation fails**
   - Check that you have write permissions in the project directory
   - Ensure sufficient disk space

5. **Shader tests fail**
   - Some shaders may have dependencies or require specific OpenGL features
   - Check the main application logs for shader compilation errors

### Debugging

To debug specific issues:

1. Check the console output for detailed error messages
2. Look at the generated report file for failure patterns
3. Try running individual visualizers through the web interface
4. Check that all dependencies are properly installed

## Customization

### Changing Test Duration
Use command line options (`--quick` for 1 second, `--full` for 3 seconds) or edit the `test_duration` parameter in `SmokeTestRunner.__init__()`.

### Adding More Test Configurations
Modify the `test_configs` list in `SmokeTestRunner.run_all_tests()`.

### Using Different Media Files
Place your own test files in the `smoketest/media/` directory or modify the media preparation logic.

### Testing Specific Visualizers
Modify the visualizer discovery logic to filter specific visualizers.

## Integration with CI/CD

The smoke test can be integrated into continuous integration pipelines:

```bash
# Exit code 0 = all tests passed
# Exit code 1 = some tests failed
python3 run_smoke_test.py
echo $?  # Check exit code
```

## Performance Notes

- Quick smoke tests take 2-5 minutes depending on the number of visualizers
- Full tests take 5-10 minutes
- Each test generates a small video file (typically 1-10 MB for 1-3 second videos)
- Ensure sufficient disk space for all test outputs

## Maintenance

- Run smoke tests after major changes to visualizers
- Update test media periodically
- Review and update test configurations as new features are added
- Clean old test results regularly to save disk space
