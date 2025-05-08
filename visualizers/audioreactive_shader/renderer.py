"""
Renderer for the Audioreactive Shader visualizer.
"""
import os
import time
import numpy as np
from PIL import Image

# Import the ShaderRenderer from the glsl module
from glsl.shader import ShaderRenderer

class AudioreactiveShaderRenderer:
    """
    Renderer for the Audioreactive Shader visualizer.
    This renderer passes audio data to a GLSL shader for visualization.
    """

    def __init__(self, width, height, config, shader_path):
        """
        Initialize the renderer.

        Args:
            width (int): Frame width
            height (int): Frame height
            config (dict): Configuration dictionary
            shader_path (str): Path to the GLSL shader file
        """
        self.width = width
        self.height = height
        self.config = config
        self.shader_path = shader_path
        self.start_time = time.time()
        self.frame_count = 0

        print(f"Initializing AudioreactiveShaderRenderer with shader: {shader_path}")
        print(f"Width: {width}, Height: {height}")

        try:
            # Initialize the shader renderer
            self.renderer = ShaderRenderer(shader_path, width, height)
            print("Shader renderer initialized successfully")

            # Create audio texture
            self.create_audio_texture()
            print("Audio texture created")

        except Exception as e:
            print(f"Error during renderer initialization: {e}")
            # Clean up resources if initialization fails
            self.cleanup()
            raise

    def create_audio_texture(self):
        """Create a texture for audio data."""
        # Create a blank texture for audio data
        texture_width = 512  # Width of the texture
        texture_data = np.zeros((texture_width, 1, 4), dtype=np.uint8)

        # Save the texture to a temporary file
        audio_texture_path = os.path.join(os.path.dirname(self.shader_path), "textures")
        os.makedirs(audio_texture_path, exist_ok=True)

        self.audio_texture_path = os.path.join(audio_texture_path, "audio_data.png")
        Image.fromarray(texture_data.reshape(1, texture_width, 4)).save(self.audio_texture_path)

        print(f"Created audio texture at {self.audio_texture_path}")

    def update_audio_texture(self, audio_data):
        """
        Update the audio texture with new audio data.

        Args:
            audio_data (numpy.ndarray): Audio data array (1D)
        """
        # Normalize audio data to 0-1 range
        normalized_data = np.clip((audio_data + 1.0) / 2.0, 0, 1)

        # Create a 2D texture with audio data
        # Format: R channel contains audio amplitude
        texture_width = 512  # Width of the texture
        texture_data = np.zeros((1, texture_width, 4), dtype=np.uint8)

        # Fill the texture with audio data
        for i in range(min(texture_width, len(normalized_data))):
            value = int(normalized_data[i] * 255)
            texture_data[0, i, 0] = value  # R channel
            texture_data[0, i, 1] = value  # G channel
            texture_data[0, i, 2] = value  # B channel
            texture_data[0, i, 3] = 255    # A channel

        # Save the texture to the file
        Image.fromarray(texture_data.reshape(1, texture_width, 4)).save(self.audio_texture_path)

    def render_frame(self, audio_data, time_value):
        """
        Render a frame with the current audio data.

        Args:
            audio_data (numpy.ndarray): Audio data for the current frame
            time_value (float): Current time value

        Returns:
            PIL.Image: Rendered frame
        """
        # Update audio texture
        self.update_audio_texture(audio_data)

        # Render the frame using the shader renderer
        frame = self.renderer.render_frame(time_value)

        # Increment frame counter
        self.frame_count += 1

        return frame

    def cleanup(self):
        """Clean up resources."""
        print("Cleaning up renderer resources...")
        try:
            if hasattr(self, 'renderer'):
                print("Cleaning up shader renderer...")
                self.renderer.cleanup()

            # Remove temporary audio texture file
            if hasattr(self, 'audio_texture_path') and os.path.exists(self.audio_texture_path):
                try:
                    os.remove(self.audio_texture_path)
                    print(f"Removed temporary audio texture: {self.audio_texture_path}")
                except:
                    print(f"Failed to remove temporary audio texture: {self.audio_texture_path}")

            print("Cleanup complete")
        except Exception as e:
            print(f"Error during cleanup: {e}")
