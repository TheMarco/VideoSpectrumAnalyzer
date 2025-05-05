"""
Process-based shader renderer for the Audio Visualizer Suite.
This module provides a shader renderer that uses a separate process to render frames.
"""
import os
import sys
import time
import json
import tempfile
import subprocess
from PIL import Image
import numpy as np

class ProcessShaderRenderer:
    """
    A shader renderer that uses a separate process to render frames.
    This avoids OpenGL context issues in the main application.
    """
    def __init__(self, shader_path, width, height):
        """
        Initialize the process-based shader renderer.
        
        Args:
            shader_path (str): Path to the shader file
            width (int): Width of the output
            height (int): Height of the output
        """
        self.shader_path = shader_path
        self.width = width
        self.height = height
        self.start_time = time.time()
        
        # Verify that the shader file exists
        if not os.path.exists(shader_path):
            raise FileNotFoundError(f"Shader file not found: {shader_path}")
        
        # Verify that the shader_render_service.py script exists
        service_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "shader_render_service.py")
        if not os.path.exists(service_path):
            raise FileNotFoundError(f"Shader render service not found: {service_path}")
        
        self.service_path = service_path
        
        # Create a temporary directory for rendered frames
        self.temp_dir = tempfile.mkdtemp(prefix="shader_frames_")
        print(f"Created temporary directory for shader frames: {self.temp_dir}")
        
        # Test the renderer by rendering a frame
        test_frame = self.render_frame(0.0)
        if test_frame is None:
            raise RuntimeError("Failed to render test frame")
        
        print(f"Process-based shader renderer initialized for {shader_path} at {width}x{height}")
    
    def render_frame(self, time_value):
        """
        Render a frame at the specified time.
        
        Args:
            time_value (float): Time value for the shader
            
        Returns:
            PIL.Image: The rendered frame
        """
        # Create a unique output path for this frame
        output_path = os.path.join(self.temp_dir, f"frame_{time_value:.6f}.png")
        
        # Build the command to render the frame
        cmd = [
            sys.executable,
            self.service_path,
            "--shader", self.shader_path,
            "--output", output_path,
            "--width", str(self.width),
            "--height", str(self.height),
            "--time", str(time_value)
        ]
        
        # Run the command
        try:
            print(f"Rendering frame at time {time_value:.2f} using separate process")
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            
            # Check if the output file exists
            if not os.path.exists(output_path):
                print(f"Error: Output file not found: {output_path}")
                print(f"Command output: {result.stdout}")
                print(f"Command error: {result.stderr}")
                return None
            
            # Load the rendered frame
            image = Image.open(output_path)
            
            # Clean up the temporary file
            try:
                os.remove(output_path)
            except Exception as e:
                print(f"Warning: Failed to remove temporary file {output_path}: {e}")
            
            return image
        
        except subprocess.CalledProcessError as e:
            print(f"Error rendering frame: {e}")
            print(f"Command output: {e.stdout}")
            print(f"Command error: {e.stderr}")
            return None
        
        except Exception as e:
            print(f"Error rendering frame: {e}")
            return None
    
    def cleanup(self):
        """Clean up resources."""
        # Remove the temporary directory
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                print(f"Removed temporary directory: {self.temp_dir}")
        except Exception as e:
            print(f"Error cleaning up temporary directory: {e}")
    
    def __del__(self):
        """Ensure cleanup when the object is garbage collected."""
        self.cleanup()
