# Spatial Photo Viewer

View and extract stereoscopic images from iPhone spatial photos (HEIC format with MV-HEVC encoding).

## Quick Start (with uv - easiest!)

No installation needed! Just run:
```bash
# Start web viewer
uv run spatial_photo_viewer.py --server

# Or extract images from command line
uv run spatial_photo_viewer.py your_photo.heic
```

## Installation (optional)

If you prefer to install dependencies first:
```bash
# Install with uv
uv pip install -r requirements.txt

# Or with pip
pip install -r requirements.txt
```

The script will auto-install dependencies on first run using uv (or pip as fallback).

## Usage

### Option 1: Web Interface with Motion (Recommended)

Start the web server:
```bash
# With uv (auto-installs dependencies)
uv run spatial_photo_viewer.py --server

# Or directly
python spatial_photo_viewer.py --server
```

Then open your browser to: **http://localhost:8000**

The server will display your local IP address. Use that address on your phone to access from another device on the same network (e.g., **http://192.168.1.XXX:8000**)

**On your iPhone (Safari):**

1. Make sure you're using **Safari browser** (Chrome/Firefox don't support motion on iOS)
2. Upload your spatial photo
3. Click "📱 Motion View (Tilt Phone)"
4. When prompted, tap **"Allow"** for Motion & Orientation access
5. Tilt your phone left/right to see the spatial effect!
6. Tap the image to go fullscreen

**Troubleshooting Safari iOS:**
If motion isn't working, check:
- Settings → Safari → Motion & Orientation Access → Enable
- Make sure you're in Safari (not Chrome or Firefox)
- Try reloading the page and granting permission again

**Other Viewing Modes:**

- **Motion View**: 📱 Tilt your phone to shift perspective (like iPhone Photos app!)
- **Side by Side**: For VR headsets or parallel viewing
- **Anaglyph 3D**: Use red-cyan 3D glasses
- **Wigglegram**: Automated animated depth effect
- **Left/Right Eye**: View individual images

### Option 2: Command Line Extraction

Extract images from a spatial photo:
```bash
# With uv (recommended)
uv run spatial_photo_viewer.py your_photo.heic

# Or directly
python spatial_photo_viewer.py your_photo.heic
```

This will create:
- `your_photo_left.png` - Left eye view
- `your_photo_right.png` - Right eye view
- `your_photo_side_by_side.png` - Combined stereoscopic image
- `your_photo_anaglyph.png` - Red-cyan 3D image

**Specify output directory:**
```bash
uv run spatial_photo_viewer.py your_photo.heic --output-dir ./output
```

**Custom server port:**
```bash
uv run spatial_photo_viewer.py --server --port 3000
```

## Features

✅ Supports iPhone spatial photos (HEIC with MV-HEVC)
✅ Multiple viewing modes
✅ Extract stereoscopic images
✅ Create anaglyph 3D images
✅ Web interface with live preview
✅ Command-line batch processing

## Requirements

- Python 3.7+
- Pillow (PIL)
- pillow-heif

## How It Works

iPhone spatial photos use the HEIC container format with MV-HEVC encoding to store two slightly offset images (left and right eye views). This viewer extracts both images and displays them in various stereoscopic formats to create the 3D depth effect.

## Viewing Tips

- **Side by Side**: Relax your eyes and look "through" the screen to merge the images
- **Anaglyph 3D**: Requires red-cyan 3D glasses for best effect
- **Wigglegram**: Creates an animated 3D effect without special equipment
- **Cross-Eye**: Swap the images and cross your eyes to see 3D

## Troubleshooting

If you get import errors, make sure to install the dependencies:
```bash
uv pip install pillow pillow-heif
# or without uv:
# pip install pillow pillow-heif
```

On macOS, you might need to install libheif:
```bash
brew install libheif
```
