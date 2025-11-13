#!/usr/bin/env python3
"""
Real-time microphone transcription using MLX Parakeet on Apple Silicon GPU.
With overlapping chunks, timestamps, and optional speaker diarization.
"""

import sounddevice as sd
import numpy as np
from parakeet_mlx import from_pretrained
import queue
import sys
import tempfile
import soundfile as sf
import os
from datetime import datetime, timedelta

# Configuration
SAMPLE_RATE = 16000  # Parakeet expects 16kHz audio
CHUNK_DURATION = 5  # seconds of audio to accumulate before transcription
OVERLAP_DURATION = 1  # seconds of overlap between chunks to avoid word cutoff
CHANNELS = 1  # Mono audio

# Optional: Enable speaker diarization (requires HuggingFace token)
# Set to True and configure HF_TOKEN environment variable to enable
ENABLE_DIARIZATION = False  # Set to True to enable speaker diarization

# Audio buffer
audio_queue = queue.Queue()

# Global model instances
model = None
diarization_pipeline = None


def audio_callback(indata, _frames, _time, status):
    """Callback function for audio stream - adds audio data to queue."""
    if status:
        print(f"Audio status: {status}", file=sys.stderr)
    audio_queue.put(indata.copy())


def load_diarization_model():
    """Load speaker diarization model (optional)."""
    try:
        from pyannote.audio import Pipeline

        # Check for HuggingFace token
        hf_token = os.environ.get("HF_TOKEN")
        if not hf_token:
            print("\nWarning: HF_TOKEN environment variable not set.")
            print("Speaker diarization requires authentication with HuggingFace.")
            print("To enable: export HF_TOKEN=your_token_here")
            return None

        print("Loading speaker diarization model...")
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=hf_token
        )
        print("Diarization model loaded!")
        return pipeline
    except Exception as e:
        print(f"Could not load diarization model: {e}")
        print("Continuing without speaker diarization...")
        return None


def diarize_audio(audio_data, audio_path):
    """Perform speaker diarization on audio."""
    global diarization_pipeline

    if diarization_pipeline is None:
        return None

    try:
        # Run diarization
        diarization = diarization_pipeline(audio_path)

        # Extract speaker segments
        speakers = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            speakers.append({
                "start": turn.start,
                "end": turn.end,
                "speaker": speaker
            })

        return speakers
    except Exception as e:
        print(f"Diarization error: {e}", file=sys.stderr)
        return None


def transcribe_audio(audio_data, start_time):
    """Transcribe audio data using Parakeet MLX."""
    global model, diarization_pipeline
    try:
        # Flatten audio to 1D array and convert to float32
        audio = audio_data.flatten().astype(np.float32)

        # Parakeet needs audio file, so create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            sf.write(tmp_path, audio, SAMPLE_RATE)

            try:
                # Transcribe using Parakeet MLX
                result = model.transcribe(tmp_path)
                text = result.text.strip()

                # Optionally perform speaker diarization
                speakers = None
                if ENABLE_DIARIZATION and diarization_pipeline:
                    speakers = diarize_audio(audio, tmp_path)

                return text, speakers
            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

    except Exception as e:
        print(f"Transcription error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return "", None


def format_transcript_with_speakers(text, speakers, start_time):
    """Format transcript with speaker labels if available."""
    if not speakers or not text:
        return text

    # Simple approach: assign the most dominant speaker in the chunk
    if speakers:
        # Count speaker time
        speaker_times = {}
        for seg in speakers:
            speaker = seg["speaker"]
            duration = seg["end"] - seg["start"]
            speaker_times[speaker] = speaker_times.get(speaker, 0) + duration

        # Get dominant speaker
        dominant_speaker = max(speaker_times, key=speaker_times.get)
        return f"[{dominant_speaker}] {text}"

    return text


def main():
    """Main function to run continuous microphone transcription."""
    global model, diarization_pipeline

    print("=" * 60)
    print("MLX Parakeet Real-time Transcription")
    print("=" * 60)
    print(f"Sample Rate: {SAMPLE_RATE} Hz")
    print(f"Chunk Duration: {CHUNK_DURATION} seconds")
    print(f"Overlap Duration: {OVERLAP_DURATION} seconds")
    print(f"Speaker Diarization: {'Enabled' if ENABLE_DIARIZATION else 'Disabled'}")
    print("\nLoading model (this may take a moment)...")

    # Load the Parakeet model
    model = from_pretrained("mlx-community/parakeet-tdt-0.6b-v3")

    # Optionally load diarization model
    if ENABLE_DIARIZATION:
        diarization_pipeline = load_diarization_model()

    # Create transcriptions directory if it doesn't exist
    transcriptions_dir = "transcriptions"
    os.makedirs(transcriptions_dir, exist_ok=True)

    # Create output file with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = os.path.join(transcriptions_dir, f"transcription_{timestamp}.txt")

    print(f"\nModel loaded! Transcriptions will be saved to: {output_file}")
    print("Speak into your microphone. Press Ctrl+C to stop.")
    print("-" * 60)

    try:
        # Open file for writing transcriptions
        with open(output_file, "w", encoding="utf-8") as f:
            # Write header
            f.write(f"Transcription Session - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            f.flush()

            # Start audio stream
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                callback=audio_callback,
                blocksize=int(SAMPLE_RATE * 0.5),  # 0.5 second blocks
            ):
                chunk_size = int(SAMPLE_RATE * CHUNK_DURATION)
                overlap_size = int(SAMPLE_RATE * OVERLAP_DURATION)
                audio_buffer = []
                overlap_buffer = None  # Store overlap from previous chunk
                session_start = datetime.now()

                while True:
                    # Collect audio chunks
                    chunk = audio_queue.get()
                    audio_buffer.append(chunk)

                    # Calculate total samples collected
                    total_samples = sum(len(c) for c in audio_buffer)

                    # When we have enough audio, transcribe it
                    if total_samples >= chunk_size:
                        # Concatenate all chunks
                        audio_data = np.concatenate(audio_buffer, axis=0)

                        # If we have overlap from previous chunk, prepend it
                        if overlap_buffer is not None:
                            audio_data = np.concatenate([overlap_buffer, audio_data], axis=0)

                        # Calculate chunk start time
                        chunk_start_time = datetime.now()

                        # Transcribe
                        text, speakers = transcribe_audio(audio_data, chunk_start_time)

                        if text:
                            # Get current timestamp for this chunk
                            chunk_time = chunk_start_time.strftime("%H:%M:%S")

                            # Format with speaker labels if available
                            formatted_text = format_transcript_with_speakers(text, speakers, chunk_start_time)

                            # Print to console with timestamp
                            print(f"\n[{chunk_time}]: {formatted_text}")
                            print("-" * 60)

                            # Write to file with timestamp
                            f.write(f"[{chunk_time}] {formatted_text}\n\n")
                            f.flush()  # Ensure it's written immediately

                        # Save overlap for next chunk (last OVERLAP_DURATION seconds)
                        if len(audio_data) > overlap_size:
                            overlap_buffer = audio_data[-overlap_size:]
                        else:
                            overlap_buffer = audio_data

                        # Clear buffer (keep only the new data beyond the chunk)
                        excess_samples = total_samples - chunk_size
                        if excess_samples > 0:
                            # Keep the excess in buffer for next iteration
                            audio_buffer = [audio_data[-excess_samples:]]
                        else:
                            audio_buffer = []

    except KeyboardInterrupt:
        print("\n\nStopping transcription...")
        print(f"Transcription saved to: {output_file}")
        print("Goodbye!")
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
