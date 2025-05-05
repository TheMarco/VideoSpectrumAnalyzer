#!/usr/bin/env python3
"""
Create a high-quality noise texture for shaders
"""
import os
import numpy as np
from PIL import Image
import argparse

def create_noise_texture(width, height, output_path):
    """
    Create a high-quality noise texture.
    
    Args:
        width (int): Width of the texture
        height (int): Height of the texture
        output_path (str): Path to save the texture
    """
    print(f"Creating noise texture of size {width}x{height}...")
    
    # Create a high-quality noise texture with multiple octaves
    noise = np.zeros((height, width, 4), dtype=np.uint8)
    
    # Base noise
    base_noise = np.random.randint(0, 256, (height, width), dtype=np.uint8)
    
    # Create multiple octaves of noise
    octaves = 4
    persistence = 0.5
    amplitude = 1.0
    total_amplitude = 0.0
    
    # Initialize with random noise
    result = np.zeros((height, width), dtype=np.float32)
    
    # Add multiple octaves
    for i in range(octaves):
        # Create noise at this octave
        octave_width = max(1, width >> i)
        octave_height = max(1, height >> i)
        octave = np.random.rand(octave_height, octave_width).astype(np.float32)
        
        # Resize to full size
        if octave_width != width or octave_height != height:
            octave_img = Image.fromarray((octave * 255).astype(np.uint8), 'L')
            octave_img = octave_img.resize((width, height), Image.BICUBIC)
            octave = np.array(octave_img).astype(np.float32) / 255.0
        
        # Add to result
        result += octave * amplitude
        total_amplitude += amplitude
        amplitude *= persistence
    
    # Normalize
    result /= total_amplitude
    
    # Convert to 8-bit
    result = (result * 255).astype(np.uint8)
    
    # Create RGBA channels
    noise[..., 0] = result  # R
    noise[..., 1] = np.random.randint(0, 256, (height, width), dtype=np.uint8)  # G
    noise[..., 2] = np.random.randint(0, 256, (height, width), dtype=np.uint8)  # B
    noise[..., 3] = 255  # A (fully opaque)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save the texture
    img = Image.fromarray(noise, 'RGBA')
    img.save(output_path)
    print(f"Noise texture saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Create a high-quality noise texture for shaders")
    parser.add_argument("--width", type=int, default=1024, help="Width of the texture")
    parser.add_argument("--height", type=int, default=1024, help="Height of the texture")
    parser.add_argument("--output", default="glsl/textures/noise_hq.png", help="Output path")
    
    args = parser.parse_args()
    create_noise_texture(args.width, args.height, args.output)

if __name__ == "__main__":
    main()
