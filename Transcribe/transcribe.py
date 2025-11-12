# /// script
# requires-python = ">=3.12"
# dependencies = ["mlx-whisper"]
# ///

#!/usr/bin/env python3
"""
Audio Transcription Script using MLX-Whisper (GPU-accelerated for M1/M2/M3)
Transcribes all audio files in the current directory
"""

import os
from pathlib import Path
import mlx_whisper

# Configuration
MODEL_SIZE = "mlx-community/whisper-medium-mlx"  # Options: whisper-{tiny,base,small,medium,large-v3}-mlx
# MLX automatically uses GPU on Apple Silicon

# Supported audio formats
AUDIO_EXTENSIONS = {'.aac', '.mp3', '.wav', '.m4a', '.flac', '.ogg', '.vorbis'}

def transcribe_file(audio_file):
    """Transcribe a single audio file"""
    print(f"\n{'='*60}")
    print(f"Transcribing: {audio_file.name}")
    print(f"{'='*60}")

    # Transcribe using MLX-Whisper (GPU-accelerated)
    result = mlx_whisper.transcribe(
        str(audio_file),
        path_or_hf_repo=MODEL_SIZE,
        language="en",  # Change if needed, or set to None for auto-detection
    )

    print(f"Detected language: {result.get('language', 'en')}")

    # Collect all segments
    transcription = []
    for segment in result["segments"]:
        start = segment["start"]
        end = segment["end"]
        text = segment["text"]
        print(f"[{start:.2f}s -> {end:.2f}s] {text}")
        transcription.append(f"[{start:.2f}s -> {end:.2f}s] {text}")

    return "\n".join(transcription)

def main():
    # Get current directory
    current_dir = Path.cwd()

    # Find all audio files
    audio_files = [
        f for f in current_dir.iterdir()
        if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS
    ]

    if not audio_files: 
        print("No audio files found in current directory")
        return

    print(f"Found {len(audio_files)} audio file(s)")
    print(f"\nUsing MLX-Whisper model: {MODEL_SIZE}")
    print("(First run will download the model, this may take a few minutes)")
    print("GPU acceleration enabled for Apple Silicon")

    # Create output directory for transcriptions
    output_dir = current_dir / "transcriptions"
    output_dir.mkdir(exist_ok=True)

    # Transcribe each file
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n\n[{i}/{len(audio_files)}] Processing: {audio_file.name}")

        try:
            transcription = transcribe_file(audio_file)

            # Save transcription
            output_file = output_dir / f"{audio_file.stem}.txt"
            output_file.write_text(transcription, encoding='utf-8')

            print(f"\n✓ Saved transcription to: {output_file}")

        except Exception as e:
            print(f"\n✗ Error transcribing {audio_file.name}: {e}")
            continue

    print(f"\n\n{'='*60}")
    print(f"Transcription complete!")
    print(f"All transcriptions saved to: {output_dir}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

