# /// script
# requires-python = ">=3.12"
# dependencies = ["mlx-whisper"]
# ///

#!/usr/bin/env python3
"""
Audio Transcription Script using MLX-Whisper (GPU-accelerated for M1/M2/M3)
Transcribes all audio files in the current directory, or downloads from a URL first.
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
import mlx_whisper

# Configuration
MODEL_SIZE = "mlx-community/whisper-medium-mlx"  # Options: whisper-{tiny,base,small,medium,large-v3}-mlx
# MLX automatically uses GPU on Apple Silicon

OBSIDIAN_CLIPPINGS = Path("/Users/olivier/Obsidian/Main/Clippings")

# Supported audio formats
AUDIO_EXTENSIONS = {'.aac', '.mp3', '.wav', '.m4a', '.flac', '.ogg', '.vorbis'}

def transcribe_file(audio_file, language=None):
    """Transcribe a single audio file"""
    print(f"\n{'='*60}")
    print(f"Transcribing: {audio_file.name}")
    print(f"{'='*60}")

    # Transcribe using MLX-Whisper (GPU-accelerated)
    result = mlx_whisper.transcribe(
        str(audio_file),
        path_or_hf_repo=MODEL_SIZE,
        language=language,  # None for auto-detection, or specify language code
    )
    # Collect all segments
    transcription = []
    for segment in result["segments"]:
        start = segment["start"]
        end = segment["end"]
        text = segment["text"]
        print(f"[{start:.2f}s -> {end:.2f}s] {text}")
        transcription.append(f"[{start:.2f}s -> {end:.2f}s] {text}")

    return "\n".join(transcription)

def fetch_video_metadata(url):
    """Fetch video metadata from a URL using yt-dlp --dump-json."""
    print(f"\nFetching metadata for: {url}")
    cmd = ["yt-dlp", "--dump-json", "--no-playlist", url]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        return json.loads(result.stdout.strip().splitlines()[0])
    except json.JSONDecodeError:
        return None


def save_obsidian_clipping(title, url, channel, upload_date, description, transcription_clean):
    """Save a markdown clipping to the Obsidian Clippings folder."""
    OBSIDIAN_CLIPPINGS.mkdir(parents=True, exist_ok=True)

    # Format upload_date from YYYYMMDD to YYYY-MM-DD
    published = ""
    if upload_date and len(upload_date) == 8:
        published = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"

    today = date.today().isoformat()

    # Escape double quotes in strings for YAML
    def yaml_str(s):
        return (s or "").replace('"', '\\"')

    frontmatter = f"""---
title: "{yaml_str(title)}"
source: "{yaml_str(url)}"
author:
  - "{yaml_str(channel)}"
published: {published}
created: {today}
description: "{yaml_str(description)}"
tags:
  - "clippings"
---

"""
    content = frontmatter + transcription_clean

    # Sanitize filename
    safe_title = re.sub(r'[<>:"/\\|?*]', '', title)[:100].strip()
    output_file = OBSIDIAN_CLIPPINGS / f"{safe_title}.md"
    output_file.write_text(content, encoding='utf-8')
    print(f"✓ Saved Obsidian clipping to: {output_file}")


def strip_timestamps(text):
    """Remove [start -> end] timestamp markers from transcription text."""
    return re.sub(r'\[\d+\.\d+s -> \d+\.\d+s\] ?', '', text).strip()


def download_audio(url, output_dir):
    """Download audio from a URL (or playlist) using yt-dlp, returns list of downloaded files."""
    print(f"\nDownloading audio from: {url}")
    cmd = [
        "yt-dlp",
        "-x",
        "--audio-format", "mp3",
        "--cookies-from-browser", "firefox",
        "-o", str(output_dir / "%(title)s.%(ext)s"),
        url,
    ]
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"yt-dlp exited with code {result.returncode}")
        sys.exit(result.returncode)


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Transcribe audio files using MLX-Whisper (GPU-accelerated)"
    )
    parser.add_argument(
        "--lang",
        type=str,
        default=None,
        help="Language code (e.g., 'fr', 'en', 'es', 'de'). If not specified, language will be auto-detected."
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="YouTube URL or playlist to download and transcribe."
    )
    parser.add_argument(
        "--convert",
        action="store_true",
        help="Convert existing .txt transcriptions in transcriptions/ to Obsidian clippings without re-transcribing."
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Target a specific .txt file in transcriptions/ when using --convert (e.g. 'My Video.txt')."
    )
    args = parser.parse_args()

    # Get current directory
    current_dir = Path.cwd()

    # --convert: process existing .txt files without re-transcribing
    if args.convert:
        transcriptions_dir = current_dir / "transcriptions"
        if args.file:
            target = transcriptions_dir / args.file
            if not target.exists():
                print(f"File not found: {target}")
                return
            txt_files = [target]
        else:
            txt_files = sorted(transcriptions_dir.glob("*.txt"))
        if not txt_files:
            print("No .txt files found in transcriptions/")
            return
        video_meta = fetch_video_metadata(args.url) if args.url else None
        print(f"Converting {len(txt_files)} file(s) to Obsidian clippings...")
        for txt_file in txt_files:
            raw = txt_file.read_text(encoding='utf-8')
            clean_text = strip_timestamps(raw)
            if video_meta:
                title = video_meta.get("title", txt_file.stem)
                url = video_meta.get("webpage_url", args.url or "")
                channel = video_meta.get("uploader", video_meta.get("channel", ""))
                upload_date = video_meta.get("upload_date", "")
                description = (video_meta.get("description") or "").split("\n")[0][:300]
            else:
                title = txt_file.stem
                url = args.url or ""
                channel = ""
                upload_date = ""
                description = ""
            save_obsidian_clipping(title, url, channel, upload_date, description, clean_text)
        return

    # Fetch metadata before downloading (so we have it for all files from this URL)
    video_meta = None
    if args.url:
        video_meta = fetch_video_metadata(args.url)
        download_audio(args.url, current_dir)

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
    if args.lang:
        print(f"Language: {args.lang}")
    else:
        print("Language: auto-detect")
    print("(First run will download the model, this may take a few minutes)")
    print("GPU acceleration enabled for Apple Silicon")

    # Create output directory for transcriptions
    output_dir = current_dir / "transcriptions"
    output_dir.mkdir(exist_ok=True)

    # Transcribe each file
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n\n[{i}/{len(audio_files)}] Processing: {audio_file.name}")

        try:
            transcription = transcribe_file(audio_file, language=args.lang)

            # Save raw transcription with timestamps
            output_file = output_dir / f"{audio_file.stem}.txt"
            output_file.write_text(transcription, encoding='utf-8')
            print(f"\n✓ Saved transcription to: {output_file}")

            # Save Obsidian clipping (clean text, with frontmatter)
            clean_text = strip_timestamps(transcription)
            if video_meta:
                title = video_meta.get("title", audio_file.stem)
                url = video_meta.get("webpage_url", args.url or "")
                channel = video_meta.get("uploader", video_meta.get("channel", ""))
                upload_date = video_meta.get("upload_date", "")
                description = (video_meta.get("description") or "").split("\n")[0][:300]
            else:
                title = audio_file.stem
                url = args.url or ""
                channel = ""
                upload_date = ""
                description = ""
            save_obsidian_clipping(title, url, channel, upload_date, description, clean_text)

        except Exception as e:
            print(f"\n✗ Error transcribing {audio_file.name}: {e}")
            continue

    print(f"\n\n{'='*60}")
    print(f"Transcription complete!")
    print(f"All transcriptions saved to: {output_dir}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

