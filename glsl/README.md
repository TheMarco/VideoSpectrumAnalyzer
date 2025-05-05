# GLSL Shaders Collection

## Attribution and Licensing

The GLSL shaders in this directory are primarily sourced from [Shadertoy.com](https://www.shadertoy.com), a fantastic community platform for creating and sharing shader art.

I've made an effort to only include shaders with Creative Commons and comparable licenses, avoiding those with more restrictive terms. Each shader file should contain its original attribution and license information in the comments at the top of the file.

## Notice to Original Authors

If you are an original author of any shader included in this collection and have concerns about its inclusion in this tool, please contact me at info@ai-created.com, and I will promptly remove it.

## Usage in Audio Visualizer Suite

These shaders are used as visual effects in the Audio Visualizer Suite. The application includes a shader testing tool that allows you to preview and test shaders before using them in your visualizations. See `SHADER_TESTING.md` in the root directory for more information on how to use the shader testing tool.

## Modifications

Some shaders have been modified to work with our rendering system. These modifications typically include:

1. Compatibility fixes for our GLSL implementation
2. Performance optimizations
3. Integration with our audio reactive system

Modified versions can be found in the `fixed` subdirectory.

## Creating New Shaders

Feel free to create and add your own shaders to this collection. Please follow these guidelines:

1. Include proper attribution and licensing information
2. Follow the format of existing shaders
3. Test your shader with the shader testing tool before using it in the main application

## Shader Resources

If you're interested in learning more about GLSL and creating your own shaders, here are some helpful resources:

- [The Book of Shaders](https://thebookofshaders.com/)
- [Shadertoy](https://www.shadertoy.com)
- [GLSL Sandbox](http://glslsandbox.com/)
- [Inigo Quilez's Articles](https://iquilezles.org/articles/)