#!/usr/bin/env python3
"""
Process images using Sharp Apple 3D Gaussian Splatting model.
Downloads the model from Hugging Face and processes all images in ./input directory.
"""

import os
import subprocess
import sys
from pathlib import Path
from huggingface_hub import hf_hub_download


def download_model():
    """Download the Sharp model from Hugging Face if not already present."""
    model_file = "sharp_2572gikvuh.pt"

    # Check if model already exists
    if os.path.exists(model_file):
        print(f"Model {model_file} already exists, skipping download.")
        return model_file

    print("Downloading model from Hugging Face...")
    try:
        downloaded_path = hf_hub_download(
            repo_id="apple/Sharp",
            filename="sharp_2572gikvuh.pt",
            local_dir=".",
            local_dir_use_symlinks=False
        )
        print(f"Model downloaded successfully: {downloaded_path}")
        return model_file
    except Exception as e:
        print(f"Error downloading model: {e}")
        sys.exit(1)


def find_images(input_dir):
    """Find all image files in the input directory."""
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"Input directory {input_dir} does not exist.")
        return []

    # Common image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp',
                        '.tiff', '.tif', '.webp', '.heic', '.heif'}

    images = []
    for ext in image_extensions:
        images.extend(input_path.glob(f"*{ext}"))
        images.extend(input_path.glob(f"*{ext.upper()}"))

    return sorted(images)


def get_sharp_command():
    """Get the command to run sharp, using the current Python interpreter."""
    # Use the current Python interpreter (from venv if active)
    python_exe = sys.executable

    # Method 1: Try to find sharp in the venv's bin directory (most common)
    venv_bin = Path(sys.prefix) / "bin" / "sharp"
    if venv_bin.exists():
        return [str(venv_bin)]

    # Method 2: Try running as Python module
    # First check if sharp module exists
    try:
        import importlib.util
        spec = importlib.util.find_spec("sharp")
        if spec is not None:
            return [python_exe, "-m", "sharp"]
    except ImportError:
        pass

    # Method 3: Fallback to just "sharp" (if in PATH)
    return ["sharp"]


def process_image(image_path, output_dir, model_file):
    """Process a single image using sharp predict command."""
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Get image name without extension for output
    image_name = image_path.stem
    output_file = output_path / f"{image_name}.ply"

    print(f"Processing: {image_path.name} -> {output_file}")

    try:
        # Get the sharp command (using venv's Python if available)
        sharp_cmd = get_sharp_command()

        # Run sharp predict command
        cmd = sharp_cmd + [
            "predict",
            "-i", str(image_path),
            "-o", str(output_file),
            "-c", model_file
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        print(f"✓ Successfully processed {image_path.name}")
        if result.stdout:
            print(f"  Output: {result.stdout.strip()}")

        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error processing {image_path.name}: {e.stderr}")
        return False
    except FileNotFoundError:
        print("✗ Error: 'sharp' command not found.")
        print("  Make sure you have activated your virtual environment and installed dependencies:")
        print("  source venv/bin/activate  # or .venv/bin/activate")
        print("  pip install -r requirements.txt")
        return False


def check_sharp_available():
    """Check if sharp is available in the current environment."""
    sharp_cmd = get_sharp_command()
    try:
        # Try to run sharp --version or just check if command exists
        result = subprocess.run(
            sharp_cmd + ["--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        # If we get here, sharp exists (even if --version fails, the command was found)
        return True
    except FileNotFoundError:
        # Command not found at all
        return False
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        # Command exists but --version failed (that's okay, it means sharp is installed)
        return True
    except Exception:
        # Any other error - assume it's not available
        return False


def main():
    """Main function to orchestrate the processing."""
    input_dir = "./input"
    output_dir = "./output"

    print("=" * 60)
    print("Sharp Apple 3D Gaussian Splatting - Image Processor")
    print("=" * 60)

    # Check if sharp is available
    if not check_sharp_available():
        print("\n✗ Error: 'sharp' command not found or not working.")
        print("\n  Please make sure:")
        print("  1. Your virtual environment is activated")
        print("  2. You have installed all dependencies:")
        print("     pip install -r requirements.txt")
        print("     (or: uv pip install -r requirements.txt)")
        print("\n  Current Python: ", sys.executable)
        print("  Current prefix:  ", sys.prefix)
        sys.exit(1)

    # Download model
    model_file = download_model()
    print()

    # Find all images
    images = find_images(input_dir)

    if not images:
        print(f"No images found in {input_dir}")
        print("Supported formats: jpg, jpeg, png, bmp, tiff, tif, webp, heic, heif")
        sys.exit(1)

    print(f"Found {len(images)} image(s) to process:")
    for img in images:
        print(f"  - {img.name}")
    print()

    # Process each image
    successful = 0
    failed = 0

    for image_path in images:
        if process_image(image_path, output_dir, model_file):
            successful += 1
        else:
            failed += 1
        print()

    # Summary
    print("=" * 60)
    print(f"Processing complete: {successful} successful, {failed} failed")
    print("=" * 60)


if __name__ == "__main__":
    main()
