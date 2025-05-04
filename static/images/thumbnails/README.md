# Visualizer Thumbnail Images

This directory contains thumbnail images for the visualizers displayed on the home page.

## Adding a Thumbnail for the Spectrum Analyzer

1. Create an image of your spectrum analyzer visualization with the following specifications:
   - **Filename**: `spectrum_analyzer.jpg`
   - **Dimensions**: 800px × 450px (16:9 aspect ratio)
   - **Format**: JPG (preferred) or PNG
   - **Content**: The image should show what the spectrum analyzer looks like when processing audio - with colorful bars and peaks

2. Place the image in this directory (`static/images/thumbnails/`)

3. Restart the application to see your thumbnail on the home page

## Tips for Creating a Good Thumbnail

- Use a dark background that matches the app's dark theme
- Show the spectrum analyzer with colorful bars at different heights
- Include peak indicators if your visualizer has them
- You can take a screenshot of your actual visualizer output for the most accurate representation
- Make sure the image is clear and visually appealing

## Example

```
static/images/thumbnails/
├── spectrum_analyzer.jpg  <- Your thumbnail goes here
└── .gitkeep
```

Once you add the image, the "No Preview Available" message will be replaced with your thumbnail.
