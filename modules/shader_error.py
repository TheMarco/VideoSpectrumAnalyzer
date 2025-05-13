"""
Custom exceptions for shader-related errors.
"""

class ShaderError(Exception):
    """Base exception for shader-related errors."""
    
    def __init__(self, message, shader_path=None, details=None):
        self.message = message
        self.shader_path = shader_path
        self.details = details
        
        # Format the error message
        full_message = f"SHADER ERROR: {message}"
        if shader_path:
            full_message += f" (in {shader_path})"
        if details:
            full_message += f"\n\nDetails:\n{details}"
            
        super().__init__(full_message)
        
    def get_shader_name(self):
        """Get the shader name from the path."""
        if not self.shader_path:
            return "Unknown Shader"
        
        import os
        return os.path.basename(self.shader_path)
