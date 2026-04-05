# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Single-script CLI tool that transcribes audio files using MLX-Whisper, optimized for Apple Silicon GPU acceleration. Place audio files in the project directory, run the tool, and transcriptions are saved to `transcriptions/`.

## Commands

```bash
# Install dependencies (uses uv)
uv sync

# Transcribe all audio files in the current directory (auto-detect language)
uv run transcribe

# Transcribe with a specific language
uv run transcribe --lang fr
```

## Key Details

- **Model**: `mlx-community/whisper-medium-mlx` (configurable via `MODEL_SIZE` constant in `transcribe.py`)
- **Supported formats**: `.aac`, `.mp3`, `.wav`, `.m4a`, `.flac`, `.ogg`, `.vorbis`
- **Output**: Timestamped text files in `transcriptions/` directory, one per audio file
- **Platform**: macOS only (requires Apple Silicon for MLX GPU acceleration)
- **Entry point**: `transcribe:main` registered as a console script
