#!/usr/bin/env python3
"""
Extract frames from a video file at a specified rate.
"""

import os
import sys
import ffmpeg
from pathlib import Path


def extract_frames(video_path, output_dir="frames", fps=2):
    """
    Extract frames from a video file.

    Args:
        video_path: Path to the input video file
        output_dir: Directory to save extracted frames
        fps: Number of frames per second to extract (default: 2)
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Get video info
    try:
        probe = ffmpeg.probe(video_path)
        video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        duration = float(probe['format']['duration'])
        print(f"Video duration: {duration:.2f} seconds")
        print(f"Video resolution: {video_info['width']}x{video_info['height']}")
        print(f"Extracting {fps} frames per second...")
    except ffmpeg.Error as e:
        print(f"Error probing video: {e.stderr.decode()}")
        return

    # Extract frames
    output_pattern = str(output_path / "frame_%06d.jpg")

    try:
        (
            ffmpeg
            .input(video_path)
            .filter('fps', fps=fps)
            .output(output_pattern, **{
                'q:v': 2,  # Quality (1-31, lower is better)
                'start_number': 0
            })
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )

        # Count extracted frames
        frame_count = len(list(output_path.glob("frame_*.jpg")))
        print(f"Successfully extracted {frame_count} frames to {output_dir}/")

    except ffmpeg.Error as e:
        print(f"Error extracting frames: {e.stderr.decode()}")
        return


def main():
    # Default video file
    video_file = "The Ranch- Tales from the Trail.mkv"

    # Check if video file exists
    if not os.path.exists(video_file):
        print(f"Error: Video file '{video_file}' not found")
        sys.exit(1)

    # Extract frames (you can change fps value here)
    # fps=2 means 2 frames per second
    # fps=3 means 3 frames per second, etc.
    extract_frames(video_file, output_dir="frames", fps=2)


if __name__ == "__main__":
    main()
