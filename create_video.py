#!/usr/bin/env python3
"""
Script to create a video from a sequence of frames using ffmpeg.
"""

import os
import argparse
import subprocess
import glob
from tqdm import tqdm

def parse_args():
    parser = argparse.ArgumentParser(description='Create video from frames')
    parser.add_argument('--frames_dir', type=str, required=True, help='Directory containing frames')
    parser.add_argument('--output', type=str, default='output.mp4', help='Output video file')
    parser.add_argument('--fps', type=int, default=30, help='Frames per second')
    parser.add_argument('--audio', type=str, default=None, help='Audio file to add to the video')
    parser.add_argument('--crf', type=int, default=18, help='CRF value for ffmpeg (0-51, lower is better quality)')
    parser.add_argument('--preset', type=str, default='medium', help='Encoding preset (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow)')
    return parser.parse_args()

def create_video(frames_dir, output_file, fps, crf, preset):
    """
    Create a video from frames using ffmpeg.
    
    Args:
        frames_dir (str): Directory containing frames
        output_file (str): Output video file
        fps (int): Frames per second
        crf (int): CRF value for ffmpeg
        preset (str): Encoding preset
    """
    # Get list of frames
    frames = sorted(glob.glob(os.path.join(frames_dir, 'frame_*.png')))
    if not frames:
        print(f"No frames found in {frames_dir}")
        return False
    
    print(f"Found {len(frames)} frames in {frames_dir}")
    
    # Create temporary file with frame paths
    frames_list_file = os.path.join(frames_dir, 'frames_list.txt')
    with open(frames_list_file, 'w') as f:
        for frame in frames:
            f.write(f"file '{os.path.abspath(frame)}'\n")
            f.write(f"duration {1/fps}\n")
    
    # Create video using ffmpeg
    cmd = [
        'ffmpeg',
        '-y',  # Overwrite output file if it exists
        '-f', 'concat',
        '-safe', '0',
        '-i', frames_list_file,
        '-c:v', 'libx264',
        '-crf', str(crf),
        '-preset', preset,
        '-pix_fmt', 'yuv420p',
        '-r', str(fps),
        output_file
    ]
    
    print(f"Creating video: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        print(f"Video created: {output_file}")
        
        # Clean up
        os.remove(frames_list_file)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating video: {e}")
        return False

def add_audio(video_file, audio_file, output_file):
    """
    Add audio to a video using ffmpeg.
    
    Args:
        video_file (str): Input video file
        audio_file (str): Input audio file
        output_file (str): Output video file with audio
    """
    cmd = [
        'ffmpeg',
        '-y',  # Overwrite output file if it exists
        '-i', video_file,
        '-i', audio_file,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-shortest',
        output_file
    ]
    
    print(f"Adding audio: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        print(f"Video with audio created: {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error adding audio: {e}")
        return False

def main():
    args = parse_args()
    
    # Create video from frames
    temp_video = args.output
    if args.audio:
        # If adding audio, create a temporary video first
        temp_video = os.path.splitext(args.output)[0] + '_temp.mp4'
    
    success = create_video(args.frames_dir, temp_video, args.fps, args.crf, args.preset)
    if not success:
        return
    
    # Add audio if specified
    if args.audio:
        success = add_audio(temp_video, args.audio, args.output)
        if success:
            # Clean up temporary video
            os.remove(temp_video)

if __name__ == "__main__":
    main()
