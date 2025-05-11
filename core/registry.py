"""
Registry for visualizers.
This module provides a registry for discovering and managing visualizers.
"""
import os
import importlib
import inspect
import logging
logger = logging.getLogger('audio_visualizer.registry')
from core.base_visualizer import BaseVisualizer

class VisualizerRegistry:
    """
    Registry for visualizers.
    """

    def __init__(self):
        """Initialize the registry."""
        self.visualizers = {}

    def register(self, visualizer_class):
        """
        Register a visualizer class.

        Args:
            visualizer_class: Visualizer class to register

        Returns:
            bool: True if registration was successful, False otherwise
        """
        logger.debug(f"Attempting to register visualizer class: {visualizer_class.__name__}")
        
        if not inspect.isclass(visualizer_class):
            logger.error(f"Error: {visualizer_class} is not a class")
            return False

        if not issubclass(visualizer_class, BaseVisualizer):
            logger.error(f"Error: {visualizer_class.__name__} does not inherit from BaseVisualizer")
            return False

        # Create an instance to get metadata
        try:
            instance = visualizer_class()
            name = instance.name
            display_name = getattr(instance, 'display_name', name)
            self.visualizers[name] = {
                "class": visualizer_class,
                "instance": instance,
                "name": name,
                "display_name": display_name,
                "description": instance.description,
                "thumbnail": instance.thumbnail
            }
            logger.info(f"Registered visualizer: {display_name} (internal name: {name})")
            return True
        except Exception as e:
            logger.error(f"Error registering visualizer {visualizer_class.__name__}: {e}", exc_info=True)
            return False

    def discover_visualizers(self, package_name="visualizers"):
        """
        Discover and register visualizers from a package.

        Args:
            package_name (str): Name of the package to search

        Returns:
            int: Number of visualizers registered
        """
        count = 0
        try:
            package = importlib.import_module(package_name)
            package_path = os.path.dirname(package.__file__)

            # Find all subdirectories that might contain visualizers
            for item in os.listdir(package_path):
                item_path = os.path.join(package_path, item)
                if os.path.isdir(item_path) and not item.startswith('__'):
                    # Check if this directory contains a visualizer module
                    visualizer_module_path = f"{package_name}.{item}.visualizer"
                    try:
                        module = importlib.import_module(visualizer_module_path)

                        # Find all classes in the module that inherit from BaseVisualizer
                        for name, obj in inspect.getmembers(module, inspect.isclass):
                            if issubclass(obj, BaseVisualizer) and obj is not BaseVisualizer:
                                if self.register(obj):
                                    count += 1
                    except ImportError as e:
                        print(f"Could not import {visualizer_module_path}: {e}")
                    except Exception as e:
                        print(f"Error discovering visualizers in {visualizer_module_path}: {e}")
        except Exception as e:
            print(f"Error discovering visualizers: {e}")

        return count

    def get_visualizer(self, name):
        """
        Get a visualizer by name.

        Args:
            name (str): Name of the visualizer

        Returns:
            object: Visualizer instance or None if not found
        """
        if name in self.visualizers:
            return self.visualizers[name]["instance"]
        return None

    def get_all_visualizers(self):
        """
        Get all registered visualizers.

        Returns:
            list: List of visualizer metadata dictionaries
        """
        return [info for _, info in self.visualizers.items()]

    def get_visualizer_names(self):
        """
        Get names of all registered visualizers.

        Returns:
            list: List of visualizer names
        """
        return list(self.visualizers.keys())

# Create a singleton instance
registry = VisualizerRegistry()
