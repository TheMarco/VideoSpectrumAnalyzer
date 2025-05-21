"""
Progress tracking utility for the Audio Visualizer Suite.
This module provides a unified way to track progress across different stages of the rendering process.
"""

class ProgressTracker:
    """
    A utility class for tracking progress across multiple stages of processing.
    
    This class manages progress tracking with weighted stages, ensuring that
    progress moves smoothly from 0% to 100% across the entire process.
    """
    
    def __init__(self, stages=None, callback=None):
        """
        Initialize the progress tracker.
        
        Args:
            stages (dict, optional): Dictionary of stage names and their weights.
                                    If not provided, default stages will be used.
            callback (callable, optional): Callback function for progress updates.
                                          Should accept progress (int) and message (str) parameters.
        """
        # Default stages and their weights (must sum to 100)
        self.default_stages = {
            "audio_loading": 5,
            "audio_analysis": 15,
            "background_preparation": 10,
            "frame_generation": 60,
            "video_finalization": 10
        }
        
        self.stages = stages if stages is not None else self.default_stages
        self.callback = callback
        
        # Validate that weights sum to 100
        total_weight = sum(self.stages.values())
        if total_weight != 100:
            print(f"Warning: Stage weights sum to {total_weight}, not 100. Normalizing...")
            factor = 100 / total_weight
            self.stages = {stage: weight * factor for stage, weight in self.stages.items()}
        
        # Initialize tracking variables
        self.current_stage = None
        self.stage_progress = 0
        self.completed_weight = 0
        
        # Debug info
        print(f"Progress tracker initialized with stages: {self.stages}")
    
    def start_stage(self, stage_name, message=None):
        """
        Start a new processing stage.
        
        Args:
            stage_name (str): Name of the stage to start.
            message (str, optional): Message to display for this stage.
        
        Returns:
            bool: True if stage exists, False otherwise.
        """
        if stage_name not in self.stages:
            print(f"Warning: Unknown stage '{stage_name}'")
            return False
        
        self.current_stage = stage_name
        self.stage_progress = 0
        
        if message is None:
            message = f"Starting {stage_name.replace('_', ' ')}..."
        
        self._update_progress(message)
        return True
    
    def update_stage_progress(self, progress_percent, message=None):
        """
        Update progress within the current stage.
        
        Args:
            progress_percent (float): Progress percentage within the current stage (0-100).
            message (str, optional): Message to display for this progress update.
        """
        if self.current_stage is None:
            print("Warning: No active stage for progress update")
            return
        
        self.stage_progress = min(100, max(0, progress_percent))
        
        if message is None:
            message = f"{self.current_stage.replace('_', ' ')}: {self.stage_progress:.0f}%"
        
        self._update_progress(message)
    
    def complete_stage(self, message=None):
        """
        Mark the current stage as complete and move to the next stage.
        
        Args:
            message (str, optional): Message to display for stage completion.
        """
        if self.current_stage is None:
            print("Warning: No active stage to complete")
            return
        
        # Add this stage's weight to completed weight
        self.completed_weight += self.stages.get(self.current_stage, 0)
        
        if message is None:
            message = f"Completed {self.current_stage.replace('_', ' ')}"
        
        # Set stage progress to 100% and update
        self.stage_progress = 100
        self._update_progress(message)
        
        # Clear current stage
        self.current_stage = None
    
    def _update_progress(self, message):
        """
        Calculate overall progress and call the callback function.
        
        Args:
            message (str): Message to display for this progress update.
        """
        # Calculate overall progress
        if self.current_stage is None:
            overall_progress = self.completed_weight
        else:
            # Calculate the weighted progress of the current stage
            stage_weight = self.stages.get(self.current_stage, 0)
            weighted_stage_progress = (self.stage_progress / 100) * stage_weight
            overall_progress = self.completed_weight + weighted_stage_progress
        
        # Ensure progress is within bounds
        overall_progress = min(100, max(0, overall_progress))
        
        # Call the callback if provided
        if self.callback:
            try:
                self.callback(int(overall_progress), message)
            except Exception as e:
                print(f"Error in progress callback: {e}")
        
        # Debug output
        print(f"Progress: {overall_progress:.1f}% - {message}")
