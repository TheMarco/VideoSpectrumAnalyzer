#!/usr/bin/env python3
"""
Test script for all the fixed shaders.
"""

import os
import sys
import subprocess
import glob

def test_shader(shader_path, output_path=None, width=800, height=600, time_value=0.0):
    """
    Test a shader by rendering a single frame.

    Args:
        shader_path (str): Path to the shader file
        output_path (str): Path to save the output image
        width (int): Width of the output image
        height (int): Height of the output image
        time_value (float): Time value for the shader

    Returns:
        bool: True if the shader rendered successfully, False otherwise
    """
    if output_path is None:
        shader_name = os.path.basename(shader_path).replace('.glsl', '')
        output_path = f"test_output_{shader_name}.png"

    print(f"Testing shader: {shader_path}")
    print(f"Output path: {output_path}")

    # Build the command to render the frame
    cmd = [
        sys.executable,
        "shader_render_service.py",
        "--shader", shader_path,
        "--output", output_path,
        "--width", str(width),
        "--height", str(height),
        "--time", str(time_value)
    ]

    # Run the command
    try:
        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=30  # 30 second timeout
        )

        # Check if the command was successful
        if result.returncode == 0:
            print(f"Shader rendered successfully!")
            print(f"Output saved to: {output_path}")
            return True
        else:
            print(f"Shader rendering failed with return code: {result.returncode}")
            print(f"Command output: {result.stdout}")
            print(f"Command error: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print(f"Shader rendering timed out after 30 seconds")
        return False
    except Exception as e:
        print(f"Error running shader: {e}")
        return False

if __name__ == "__main__":
    # List of shaders to test
    shaders_to_test = [
        "glsl/basewarp.glsl",
        "glsl/biomine.glsl",
        "glsl/chromaticresonance.glsl",
        "glsl/combustible.glsl",
        "glsl/digitalbrain.glsl",
        "glsl/earthtunnel.glsl",
        "glsl/fire.glsl",
        "glsl/gears.glsl",
        "glsl/hyperspace.glsl",
        "glsl/ionize.glsl",
        "glsl/portal.glsl",
        "glsl/protean.glsl",
        "glsl/singularity.glsl",
        "glsl/spectrum.glsl",
        "glsl/sunset.glsl",
        "glsl/torusfog.glsl"
    ]

    # Test each shader
    results = {}
    for shader in shaders_to_test:
        print("\n" + "=" * 50)
        print(f"Testing shader: {shader}")
        print("=" * 50)

        result = test_shader(shader)
        results[shader] = result

    # Print summary
    print("\n\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)

    success_count = 0
    failure_count = 0

    for shader, result in results.items():
        status = "SUCCESS" if result else "FAILED"
        if result:
            success_count += 1
        else:
            failure_count += 1
        print(f"{shader}: {status}")

    print("\nTotal: {0} shaders".format(len(results)))
    print(f"Successful: {success_count}")
    print(f"Failed: {failure_count}")

    if failure_count == 0:
        print("\nAll shaders rendered successfully!")
    else:
        print("\nSome shaders failed to render. Please check the logs for details.")
