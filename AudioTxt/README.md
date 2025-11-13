# AudioTxt - Real-time Microphone Transcription

Real-time microphone transcription using MLX Parakeet optimized for Apple Silicon GPU.

## Features

 **16kHz Mono Audio** - Optimized format for best transcription results
 **Overlapping Chunks** - 1-second overlap prevents word cutoff at boundaries
 **Timestamped Transcripts** - Each transcription includes time markers for meeting minutes
 **Speaker Diarization** - Optional speaker identification (requires HuggingFace token)
 **GPU Accelerated** - Uses MLX for fast transcription on Apple Silicon
 **Auto-save** - Transcriptions saved to timestamped files in real-time

## Installation

```bash
cd AudioTxt
uv sync
```

## Basic Usage

```bash
uv run audiotxt.py
```

This will:
- Load the Parakeet model
- Start recording from your default microphone
- Display transcriptions in the console with timestamps
- Save transcriptions to `transcriptions/transcription_YYYY-MM-DD_HH-MM-SS.txt`

Press **Ctrl+C** to stop recording.

## Output Format

**Console:**
```
[17:30:50]: This is the first sentence being transcribed
------------------------------------------------------------
[17:30:55]: This is the second sentence
------------------------------------------------------------
```

**File (transcriptions/transcription_2025-11-12_17-30-45.txt):**
```
Transcription Session - 2025-11-12 17:30:45
============================================================

[17:30:50] This is the first sentence being transcribed

[17:30:55] This is the second sentence

[17:31:00] And so on...
```

## AI Summarization

After recording a transcript, you can generate an AI-powered summary and analysis:

```bash
# Summarize the latest transcript
uv run summarize.py

# Summarize a specific transcript file
uv run summarize.py transcriptions/transcription_2025-11-12_17-30-45.txt

# Customize output
uv run summarize.py --max-tokens 2048 --temperature 0.8 --output-dir my_summaries
```

**What the AI analyzes:**
1. **Summary** - Brief overview (2-3 sentences)
2. **Key Points** - Main discussion points
3. **Action Items** - Tasks, decisions, next steps
4. **Important Details** - Dates, numbers, names mentioned
5. **Overall Sentiment** - General tone of conversation

**Example Output:**
```
1. Summary
The conversation covers a project planning meeting where the team discussed
the new website redesign timeline and budget allocation. Key stakeholders
agreed on a phased rollout approach starting in Q2.

2. Key Points
• Website redesign will follow a three-phase approach
• Budget approved for $50,000 with quarterly reviews
• Launch target set for June 15th
• Mobile-first design approach confirmed

3. Action Items
• John to prepare mockups by next Friday
• Sarah to coordinate with development team
• Schedule follow-up meeting for April 10th

...
```

The summary is saved to `summaries/summary_<original_name>_<timestamp>.txt`

## Configuration

Edit these constants in audiotxt.py:

```python
SAMPLE_RATE = 16000        # Audio sample rate (16kHz recommended)
CHUNK_DURATION = 5         # Seconds of audio per transcription
OVERLAP_DURATION = 1       # Seconds of overlap between chunks
ENABLE_DIARIZATION = False # Enable speaker identification
```

## Speaker Diarization (Optional)

To enable speaker identification in transcripts:

1. **Get a HuggingFace Token:**
   - Go to https://huggingface.co/settings/tokens
   - Create a new token
   - Accept the terms for pyannote/speaker-diarization-3.1

2. **Set Environment Variable:**
   ```bash
   export HF_TOKEN=your_token_here
   ```

3. **Enable in Script:**
   ```python
   ENABLE_DIARIZATION = True  # Line 25 in audiotxt.py
   ```

4. **Run:**
   ```bash
   uv run audiotxt.py
   ```

**Output with Diarization:**
```
[17:30:50] [SPEAKER_00] Hello, how are you today?

[17:30:55] [SPEAKER_01] I'm doing great, thank you for asking!

[17:31:00] [SPEAKER_00] That's wonderful to hear!
```

## Performance Tips

- **Chunk Duration**: 5 seconds balances latency and accuracy. Longer chunks are more accurate but slower.
- **Overlap**: 1 second overlap prevents word cutoff. Increase for better continuity.
- **Long Sessions**: For recordings >30 minutes, the system automatically handles segmentation.
- **GPU Memory**: The script uses minimal GPU memory (~500MB) and can run alongside other tasks.

## Troubleshooting

**No audio recorded:**
- Check microphone permissions in System Settings � Privacy & Security � Microphone
- Verify default input device: System Settings � Sound � Input

**Slow transcription:**
- Reduce `CHUNK_DURATION` for faster response (trade-off: less accuracy)
- Ensure no other heavy processes are using the GPU

**Diarization not working:**
- Verify HF_TOKEN is set: `echo $HF_TOKEN`
- Check you accepted the model terms on HuggingFace
- Ensure pyannote-audio is installed: `uv run python -c "import pyannote.audio"`

## Models Used

- **Transcription**: mlx-community/parakeet-tdt-0.6b-v3
- **Diarization**: pyannote/speaker-diarization-3.1
- **Summarization**: mlx-community/Llama-3.2-3B-Instruct-4bit

## Files

- `audiotxt.py` - Main transcription script
- `summarize.py` - AI summarization script
- `transcriptions/` - Output directory for transcripts (auto-created)
- `summaries/` - Output directory for AI summaries (auto-created)
- `pyproject.toml` - Python dependencies
- `.venv/` - Virtual environment (created by uv)

## License

This script uses:
- MLX Parakeet - MIT License
- Pyannote Audio - MIT License
- Llama-3.2-3B-Instruct - Llama 3.2 Community License
