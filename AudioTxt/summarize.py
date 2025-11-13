#!/usr/bin/env python3
"""
Summarize and analyze transcripts using Llama-3.2-3B-Instruct (MLX-optimized).
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from mlx_lm import load, generate


# Configuration
MODEL_NAME = "mlx-community/Llama-3.2-3B-Instruct-4bit"
MAX_TOKENS = 1024  # Maximum tokens for summary
TEMPERATURE = 0.7  # Temperature for generation (0.0-1.0)


def load_model():
    """Load the Llama model."""
    print(f"Loading model: {MODEL_NAME}")
    print("(First run will download the model, this may take a few minutes)")

    model, tokenizer = load(MODEL_NAME)

    print("Model loaded successfully!\n")
    return model, tokenizer


def read_transcript(file_path):
    """Read transcript from file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)


def create_summary_prompt(transcript):
    """Create a comprehensive analysis prompt for the transcript."""
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a helpful AI assistant that analyzes meeting transcripts and conversations. Your task is to provide clear, concise summaries and extract meaningful insights.<|eot_id|><|start_header_id|>user<|end_header_id|>

Please analyze the following transcript and provide:

1. **Summary** (2-3 sentences): A brief overview of the main topic and discussion
2. **Key Points**: List the main points discussed (bullet points)
3. **Action Items**: Any tasks, decisions, or next steps mentioned
4. **Important Details**: Dates, numbers, names, or specific information mentioned
5. **Overall Sentiment**: The general tone of the conversation

Here is the transcript:

{transcript}

Please provide your analysis:<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
    return prompt


def summarize_transcript(model, tokenizer, transcript):
    """Generate summary using Llama model."""
    prompt = create_summary_prompt(transcript)

    print("Generating analysis...")
    print("-" * 60)

    response = generate(
        model,
        tokenizer,
        prompt=prompt,
        max_tokens=MAX_TOKENS,
        temp=TEMPERATURE,
        verbose=False
    )

    return response


def save_summary(summary, original_file, output_dir):
    """Save summary to file."""
    # Create summaries directory
    output_dir.mkdir(exist_ok=True)

    # Create output filename
    original_stem = Path(original_file).stem
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = output_dir / f"summary_{original_stem}_{timestamp}.txt"

    # Write summary with header
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Summary Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Original Transcript: {original_file}\n")
        f.write(f"Model: {MODEL_NAME}\n")
        f.write("=" * 60 + "\n\n")
        f.write(summary)
        f.write("\n")

    return output_file


def main():
    parser = argparse.ArgumentParser(
        description="Summarize and analyze transcripts using Llama-3.2-3B-Instruct"
    )
    parser.add_argument(
        "transcript",
        type=str,
        nargs="?",
        help="Path to transcript file (or latest if not specified)"
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=str,
        default="summaries",
        help="Output directory for summaries (default: summaries)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=MAX_TOKENS,
        help=f"Maximum tokens for summary (default: {MAX_TOKENS})"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=TEMPERATURE,
        help=f"Temperature for generation (default: {TEMPERATURE})"
    )

    args = parser.parse_args()

    # Determine transcript file
    if args.transcript:
        transcript_file = Path(args.transcript)
    else:
        # Find the latest transcript in transcriptions directory
        transcriptions_dir = Path("transcriptions")
        if not transcriptions_dir.exists():
            print("Error: No transcript file specified and transcriptions/ directory not found")
            print("\nUsage:")
            print("  python summarize.py <transcript_file>")
            print("  python summarize.py  # Uses latest transcript from transcriptions/")
            sys.exit(1)

        transcript_files = sorted(
            transcriptions_dir.glob("transcription_*.txt"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        if not transcript_files:
            print("Error: No transcript files found in transcriptions/")
            sys.exit(1)

        transcript_file = transcript_files[0]
        print(f"Using latest transcript: {transcript_file}\n")

    if not transcript_file.exists():
        print(f"Error: File not found: {transcript_file}")
        sys.exit(1)

    # Update global config if specified
    global MAX_TOKENS, TEMPERATURE
    MAX_TOKENS = args.max_tokens
    TEMPERATURE = args.temperature

    output_dir = Path(args.output_dir)

    print("=" * 60)
    print("Transcript Summarization with Llama-3.2-3B-Instruct")
    print("=" * 60)
    print(f"Transcript: {transcript_file}")
    print(f"Output directory: {output_dir}")
    print()

    # Load model
    model, tokenizer = load_model()

    # Read transcript
    print(f"Reading transcript: {transcript_file}")
    transcript = read_transcript(transcript_file)

    # Check if transcript is too short
    if len(transcript.strip()) < 50:
        print("Warning: Transcript appears to be very short or empty")
        print(f"Content preview: {transcript[:200]}")

    print(f"Transcript length: {len(transcript)} characters\n")

    # Generate summary
    summary = summarize_transcript(model, tokenizer, transcript)

    # Display summary
    print("\n" + "=" * 60)
    print("ANALYSIS RESULTS")
    print("=" * 60)
    print(summary)
    print("=" * 60)

    # Save summary
    output_file = save_summary(summary, transcript_file, output_dir)
    print(f"\n✓ Summary saved to: {output_file}")


if __name__ == "__main__":
    main()
