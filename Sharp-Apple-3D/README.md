# Sharp Apple 3D Gaussian Splatting

Process images into 3D Gaussian Splatting models using Apple's Sharp model.

## Setup

1. Create a virtual environment (choose one method):

**Option A: Using Python's venv (standard):**
```bash
python3.13 -m venv venv
source venv/bin/activate
```

**Option B: Using uv (recommended - automatically uses Python 3.13):**
```bash
uv venv --python 3.13
source .venv/bin/activate
```

Or if Python 3.13 is your default:
```bash
uv venv
source .venv/bin/activate
```

2. Install dependencies:

**Using pip (standard venv):**
```bash
pip install -r requirements.txt
```

**Or using uv (recommended for git dependencies):**
```bash
uv pip install -r requirements.txt
```

**Or install directly from pyproject.toml:**
```bash
uv pip install -e .
```

This will install all dependencies including `sharp` (from Apple's GitHub repository), which is a Python package that provides the `sharp` command-line tool.

**Note:** If you encounter issues installing `sharp` from requirements.txt, you can install it directly:
```bash
pip install git+https://github.com/apple/ml-sharp.git
```

**Note:** This project requires Python 3.13 or higher.

## Usage

1. Place your input images in the `./input` directory.

2. Make sure your virtual environment is activated, then run:
```bash
python process_images.py
```

Or:
```bash
./process_images.py
```

**Important:** The script will automatically use the `sharp` command from your activated virtual environment. Make sure you've activated the venv before running the script.

The script will:
- Download the Sharp model (`sharp_2572gikvuh.pt`) from Hugging Face (only once)
- Find all images in `./input`
- Process each image using `sharp predict`
- Save the output Gaussian Splatting files (`.ply`) to `./output`

## Supported Image Formats

- JPG/JPEG
- PNG
- BMP
- TIFF/TIF
- WebP
- HEIC/HEIF

## Output

Processed 3D Gaussian Splatting files will be saved as `.ply` files in the `./output` directory, with the same base name as the input image.


