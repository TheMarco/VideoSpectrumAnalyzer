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

            # Use a timeout to prevent hanging
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                timeout=10  # 10 second timeout
            )

            # Check if the output file exists
            if not os.path.exists(output_path):
                print(f"Error: Output file not found: {output_path}")
                print(f"Command output: {result.stdout}")
                print(f"Command error: {result.stderr}")

                # Create a detailed error message
                error_message = f"""
SHADER ERROR: Failed to render shader '{os.path.basename(self.shader_path)}'

The shader '{self.shader_path}' could not be rendered using the GPU-based renderer.
No output file was produced by the shader rendering process.

Error details:
- Shader path: {self.shader_path}
- Dimensions: {self.width}x{self.height}
- Time value: {time_value}
- Command output: {result.stdout}
- Command error: {result.stderr}

Possible solutions:
1. Check if the shader has syntax errors
"""
                # Log the error
                print(error_message)

                # Create an error image for the UI
                from PIL import Image, ImageDraw, ImageFont
                error_image = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 255))
                draw = ImageDraw.Draw(error_image)

                # Add error text
                try:
                    # Try to load a font
                    font = ImageFont.truetype("Arial.ttf", 24)
                except:
                    # Fall back to default font
                    font = ImageFont.load_default()

                # Draw the error message
                shader_name = os.path.basename(self.shader_path)
                draw.text((self.width//2, self.height//2 - 50), f"SHADER ERROR: {shader_name}",
                         fill=(255, 0, 0), anchor="mm", font=font)
                draw.text((self.width//2, self.height//2), "Shader could not be rendered",
                         fill=(255, 0, 0), anchor="mm", font=font)
                draw.text((self.width//2, self.height//2 + 50), "See logs for details",
                         fill=(255, 0, 0), anchor="mm", font=font)

                # Save the error image for reference
                error_image_path = f"shader_error_{os.path.basename(self.shader_path)}.png"
                error_image.save(error_image_path)
                print(f"Saved error image to {error_image_path}")

                # Raise the error
                raise RuntimeError(f"Shader '{os.path.basename(self.shader_path)}' failed to render. See logs for details.")

            # Load the rendered frame
            try:
                image = Image.open(output_path)

                # Check if the image is valid
                image.verify()  # Verify that it's a valid image
                # Need to reopen after verify
                image = Image.open(output_path)

                # Check if the image is all black (potential shader failure)
                if image.mode == "RGBA":
                    # Convert to numpy array for faster processing
                    import numpy as np
                    img_array = np.array(image)
                    # Check if all pixels are black (RGB = 0,0,0)
                    if np.all(img_array[:,:,:3] == 0):
                        print("Warning: Rendered image is completely black, likely a shader error")

                        # Create a detailed error message
                        error_message = f"""
SHADER ERROR: Shader '{os.path.basename(self.shader_path)}' rendered a completely black image

The shader '{self.shader_path}' was compiled successfully but produced a completely black image.
This usually indicates a problem with the shader code.

Error details:
- Shader path: {self.shader_path}
- Dimensions: {self.width}x{self.height}
- Time value: {time_value}

Possible solutions:
1. Check if the shader has logic errors
"""
                        # Log the error
                        print(error_message)

                        # Create an error image for the UI
                        from PIL import ImageDraw, ImageFont
                        error_image = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 255))
                        draw = ImageDraw.Draw(error_image)

                        # Add error text
                        try:
                            # Try to load a font
                            font = ImageFont.truetype("Arial.ttf", 24)
                        except:
                            # Fall back to default font
                            font = ImageFont.load_default()

                        # Draw the error message
                        shader_name = os.path.basename(self.shader_path)
                        draw.text((self.width//2, self.height//2 - 50), f"SHADER ERROR: {shader_name}",
                                 fill=(255, 0, 0), anchor="mm", font=font)
                        draw.text((self.width//2, self.height//2), "Shader produced a black image",
                                 fill=(255, 0, 0), anchor="mm", font=font)
                        draw.text((self.width//2, self.height//2 + 50), "See logs for details",
                                 fill=(255, 0, 0), anchor="mm", font=font)

                        # Save the error image for reference
                        error_image_path = f"shader_error_black_{os.path.basename(self.shader_path)}.png"
                        error_image.save(error_image_path)
                        print(f"Saved error image to {error_image_path}")

                        # Raise the error
                        raise RuntimeError(f"Shader '{os.path.basename(self.shader_path)}' produced a black image. See logs for details.")

                # Clean up the temporary file
                try:
                    os.remove(output_path)
                except Exception as e:
                    print(f"Warning: Failed to remove temporary file {output_path}: {e}")

                return image
            except Exception as img_error:
                print(f"Error loading image: {img_error}")

                # Create a detailed error message
                error_message = f"""
SHADER ERROR: Failed to load image for shader '{os.path.basename(self.shader_path)}'

The shader '{self.shader_path}' produced an output file, but it could not be loaded as a valid image.

Error details:
- Shader path: {self.shader_path}
- Dimensions: {self.width}x{self.height}
- Time value: {time_value}
- Error: {img_error}

Possible solutions:
1. Check if the shader has rendering errors
"""
                # Log the error
                print(error_message)

                # Create an error image for the UI
                from PIL import ImageDraw, ImageFont
                error_image = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 255))
                draw = ImageDraw.Draw(error_image)

                # Add error text
                try:
                    # Try to load a font
                    font = ImageFont.truetype("Arial.ttf", 24)
                except:
                    # Fall back to default font
                    font = ImageFont.load_default()

                # Draw the error message
                shader_name = os.path.basename(self.shader_path)
                draw.text((self.width//2, self.height//2 - 50), f"SHADER ERROR: {shader_name}",
                         fill=(255, 0, 0), anchor="mm", font=font)
                draw.text((self.width//2, self.height//2), "Invalid image produced",
                         fill=(255, 0, 0), anchor="mm", font=font)
                draw.text((self.width//2, self.height//2 + 50), "See logs for details",
                         fill=(255, 0, 0), anchor="mm", font=font)

                # Save the error image for reference
                error_image_path = f"shader_error_invalid_{os.path.basename(self.shader_path)}.png"
                error_image.save(error_image_path)
                print(f"Saved error image to {error_image_path}")

                # Raise the error
                raise RuntimeError(f"Shader '{os.path.basename(self.shader_path)}' produced an invalid image. See logs for details.")

        except subprocess.CalledProcessError as e:
            print(f"Error rendering frame: {e}")
            print(f"Command output: {e.stdout}")
            print(f"Command error: {e.stderr}")

            # Create a detailed error message
            error_message = f"""
SHADER ERROR: Process error while rendering shader '{os.path.basename(self.shader_path)}'

The shader rendering process failed with an error.

Error details:
- Shader path: {self.shader_path}
- Dimensions: {self.width}x{self.height}
- Time value: {time_value}
- Error: {e}
- Command output: {e.stdout}
- Command error: {e.stderr}

Possible solutions:
1. Check if the shader has syntax errors
"""
            # Log the error
            print(error_message)

            # Create an error image for the UI
            from PIL import Image, ImageDraw, ImageFont
            error_image = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 255))
            draw = ImageDraw.Draw(error_image)

            # Add error text
            try:
                # Try to load a font
                font = ImageFont.truetype("Arial.ttf", 24)
            except:
                # Fall back to default font
                font = ImageFont.load_default()

            # Draw the error message
            shader_name = os.path.basename(self.shader_path)
            draw.text((self.width//2, self.height//2 - 50), f"SHADER ERROR: {shader_name}",
                     fill=(255, 0, 0), anchor="mm", font=font)
            draw.text((self.width//2, self.height//2), "Process error during rendering",
                     fill=(255, 0, 0), anchor="mm", font=font)
            draw.text((self.width//2, self.height//2 + 50), "See logs for details",
                     fill=(255, 0, 0), anchor="mm", font=font)

            # Save the error image for reference
            error_image_path = f"shader_error_process_{os.path.basename(self.shader_path)}.png"
            error_image.save(error_image_path)
            print(f"Saved error image to {error_image_path}")

            # Raise the error
            raise RuntimeError(f"Process error while rendering shader '{os.path.basename(self.shader_path)}'. See logs for details.")

        except Exception as e:
            print(f"Error rendering frame: {e}")

            # Create a detailed error message
            error_message = f"""
SHADER ERROR: Unexpected error while rendering shader '{os.path.basename(self.shader_path)}'

An unexpected error occurred while rendering the shader.

Error details:
- Shader path: {self.shader_path}
- Dimensions: {self.width}x{self.height}
- Time value: {time_value}
- Error: {e}

Possible solutions:
1. Check if the shader has syntax errors
"""
            # Log the error
            print(error_message)

            # Create an error image for the UI
            from PIL import Image, ImageDraw, ImageFont
            error_image = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 255))
            draw = ImageDraw.Draw(error_image)

            # Add error text
            try:
                # Try to load a font
                font = ImageFont.truetype("Arial.ttf", 24)
            except:
                # Fall back to default font
                font = ImageFont.load_default()

            # Draw the error message
            shader_name = os.path.basename(self.shader_path)
            draw.text((self.width//2, self.height//2 - 50), f"SHADER ERROR: {shader_name}",
                     fill=(255, 0, 0), anchor="mm", font=font)
            draw.text((self.width//2, self.height//2), "Unexpected error during rendering",
                     fill=(255, 0, 0), anchor="mm", font=font)
            draw.text((self.width//2, self.height//2 + 50), "See logs for details",
                     fill=(255, 0, 0), anchor="mm", font=font)

            # Save the error image for reference
            error_image_path = f"shader_error_unexpected_{os.path.basename(self.shader_path)}.png"
            error_image.save(error_image_path)
            print(f"Saved error image to {error_image_path}")

            # Raise the error
            raise RuntimeError(f"Unexpected error while rendering shader '{os.path.basename(self.shader_path)}'. See logs for details.")

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
