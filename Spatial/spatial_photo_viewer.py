#!/usr/bin/env python3
"""
Spatial Photo Viewer - Extract and view stereoscopic images from iPhone spatial photos
Supports HEIC format with MV-HEVC encoding
"""

import os
import sys
from pathlib import Path

try:
    from PIL import Image
    import pillow_heif
except ImportError:
    print("Required libraries not found. Installing with uv...")
    import subprocess
    import shutil

    # Check if uv is available
    if shutil.which("uv"):
        subprocess.check_call(["uv", "pip", "install", "pillow", "pillow-heif"])
    else:
        print("uv not found, falling back to pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow", "pillow-heif"])

    from PIL import Image
    import pillow_heif

# Register HEIF opener with Pillow
pillow_heif.register_heif_opener()

import io
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
import socket


class SpatialPhotoExtractor:
    """Extract left and right eye images from spatial photos"""

    def __init__(self, heic_path):
        self.heic_path = Path(heic_path)
        self.left_image = None
        self.right_image = None

    def extract_images(self):
        """Extract stereoscopic images from HEIC file"""
        try:
            # Open the HEIC file
            heif_file = pillow_heif.open_heif(str(self.heic_path), convert_hdr_to_8bit=False)

            print(f"Found {len(heif_file)} image(s) in the HEIC file")

            if len(heif_file) >= 2:
                # Spatial photo with multiple images
                self.left_image = Image.frombytes(
                    heif_file[0].mode,
                    heif_file[0].size,
                    heif_file[0].data,
                    "raw",
                )

                self.right_image = Image.frombytes(
                    heif_file[1].mode,
                    heif_file[1].size,
                    heif_file[1].data,
                    "raw",
                )

                print(f"✓ Extracted left image: {self.left_image.size}")
                print(f"✓ Extracted right image: {self.right_image.size}")
                return True

            elif len(heif_file) == 1:
                # Single image - not a spatial photo
                print("⚠ Warning: This appears to be a regular photo, not a spatial photo")
                self.left_image = Image.frombytes(
                    heif_file[0].mode,
                    heif_file[0].size,
                    heif_file[0].data,
                    "raw",
                )
                self.right_image = self.left_image.copy()
                return True
            else:
                print("✗ No images found in HEIC file")
                return False

        except Exception as e:
            print(f"✗ Error extracting images: {e}")
            return False

    def save_images(self, output_dir="."):
        """Save extracted images as PNG files"""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        base_name = self.heic_path.stem

        if self.left_image:
            left_path = output_dir / f"{base_name}_left.png"
            self.left_image.save(left_path, "PNG")
            print(f"✓ Saved left image: {left_path}")

        if self.right_image:
            right_path = output_dir / f"{base_name}_right.png"
            self.right_image.save(right_path, "PNG")
            print(f"✓ Saved right image: {right_path}")

    def create_side_by_side(self, output_path=None):
        """Create side-by-side stereoscopic image"""
        if not self.left_image or not self.right_image:
            return None

        left = self.left_image.convert('RGB')
        right = self.right_image.convert('RGB')

        # Resize right image to match left if sizes differ
        if left.size != right.size:
            print(f"⚠ Resizing right image from {right.size} to {left.size}")
            right = right.resize(left.size, Image.Resampling.LANCZOS)

        # Create new image with combined width
        width = left.width + right.width
        height = left.height

        combined = Image.new('RGB', (width, height))
        combined.paste(left, (0, 0))
        combined.paste(right, (left.width, 0))

        if output_path:
            combined.save(output_path, "PNG")
            print(f"✓ Saved side-by-side: {output_path}")

        return combined

    def create_anaglyph(self, output_path=None):
        """Create red-cyan anaglyph 3D image"""
        if not self.left_image or not self.right_image:
            return None

        # Convert to RGB if needed
        left_rgb = self.left_image.convert('RGB')
        right_rgb = self.right_image.convert('RGB')

        # Resize right image to match left if sizes differ
        if left_rgb.size != right_rgb.size:
            print(f"⚠ Resizing right image from {right_rgb.size} to {left_rgb.size}")
            right_rgb = right_rgb.resize(left_rgb.size, Image.Resampling.LANCZOS)

        # Split channels
        left_r, _, _ = left_rgb.split()
        _, right_g, right_b = right_rgb.split()

        # Combine: red from left, green and blue from right
        anaglyph = Image.merge('RGB', (left_r, right_g, right_b))

        if output_path:
            anaglyph.save(output_path, "PNG")
            print(f"✓ Saved anaglyph: {output_path}")

        return anaglyph

    def to_base64(self, image):
        """Convert PIL Image to base64 string"""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode()


class SpatialPhotoHandler(BaseHTTPRequestHandler):
    """HTTP handler for web viewer"""

    extractor = None

    def do_GET(self):
        """Serve the web interface"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.get_html().encode())
        elif self.path == '/images':
            if self.extractor and self.extractor.left_image:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()

                data = {
                    'left': self.extractor.to_base64(self.extractor.left_image),
                    'right': self.extractor.to_base64(self.extractor.right_image),
                    'sideBySide': self.extractor.to_base64(self.extractor.create_side_by_side()),
                    'anaglyph': self.extractor.to_base64(self.extractor.create_anaglyph())
                }
                self.wfile.write(json.dumps(data).encode())
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        """Handle file upload"""
        if self.path == '/upload':
            try:
                content_length = int(self.headers['Content-Length'])
                print(f"\n📤 Receiving upload: {content_length} bytes")
                post_data = self.rfile.read(content_length)

                # Save uploaded file temporarily
                temp_path = Path('/tmp/spatial_photo_temp.heic')
                temp_path.write_bytes(post_data)
                print(f"✓ Saved to {temp_path}")

                # Extract images
                print("🔄 Extracting images...")
                extractor = SpatialPhotoExtractor(temp_path)
                success = extractor.extract_images()

                if success:
                    self.__class__.extractor = extractor
                else:
                    print("⚠ Keeping previous extractor due to extraction failure")

                if success:
                    print("✓ Extraction successful!")
                else:
                    print("✗ Extraction failed!")

                self.send_response(200 if success else 500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': success}).encode())

            except Exception as e:
                print(f"✗ Error in upload handler: {e}")
                import traceback
                traceback.print_exc()
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())

    def get_html(self):
        """Return the HTML viewer interface"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Spatial Photo Viewer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #000;
            min-height: 100vh;
            overflow-x: hidden;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 1400px;
            width: 90%;
            margin: 20px auto;
            padding: 30px;
        }
        .container.minimal {
            background: transparent;
            box-shadow: none;
            padding: 0;
            width: 100%;
            max-width: 100%;
            margin: 0;
        }
        h1 { text-align: center; color: #333; margin-bottom: 10px; }
        .subtitle { text-align: center; color: #666; margin-bottom: 30px; font-size: 14px; }
        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 15px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 20px;
        }
        .upload-area:hover { border-color: #764ba2; background: #f8f9ff; }
        .upload-area:active { background: #e0e5ff; transform: scale(0.98); }
        input[type="file"] { display: none !important; }
        label.upload-area { display: block; }
        .controls {
            display: none;
            margin-bottom: 20px;
            padding: 20px;
            background: #f5f5f5;
            border-radius: 10px;
        }
        .controls.active { display: block; }
        .button-group { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px; }
        button {
            padding: 10px 20px;
            border: 2px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            font-size: 14px;
        }
        button:hover, button.active { background: #667eea; color: white; }
        button.motion-btn {
            border-color: #ff6b6b;
            color: #ff6b6b;
            font-size: 16px;
            padding: 15px 25px;
        }
        button.motion-btn:hover, button.motion-btn.active {
            background: #ff6b6b;
            color: white;
        }
        .viewer {
            display: none;
            border-radius: 10px;
            overflow: hidden;
            background: #000;
            position: relative;
        }
        .viewer.active { display: block; }
        .viewer.fullscreen {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            border-radius: 0;
            z-index: 9999;
        }
        .viewer img { max-width: 100%; height: auto; display: block; margin: 0 auto; }
        #motionCanvas {
            width: 100%;
            height: auto;
            display: block;
            touch-action: none;
        }
        .viewer.fullscreen #motionCanvas {
            height: 100vh;
            width: 100vw;
            object-fit: contain;
        }
        .loading { text-align: center; padding: 40px; color: #666; display: none; }
        .loading.active { display: block; }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .image-container { display: flex; gap: 2px; justify-content: center; }
        .image-container img { width: 49%; }
        .motion-info {
            position: fixed;
            top: 10px;
            left: 10px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
            z-index: 10000;
            display: none;
        }
        .motion-info.active { display: block; }
        .permission-prompt {
            background: #fff3cd;
            border: 2px solid #ffc107;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            display: none;
        }
        .permission-prompt.active { display: block; }
    </style>
</head>
<body>
    <div class="container" id="container">
        <h1>📱 Spatial Photo Viewer</h1>
        <p class="subtitle">View iPhone spatial photos with motion - Use Safari on iOS for best experience!</p>

        <label for="fileInput" class="upload-area" id="uploadArea">
            <div style="font-size: 48px;">📸</div>
            <h3>Tap here to select your spatial photo</h3>
            <p style="margin-top: 10px; color: #666;">Supports HEIC format from iPhone</p>
            <input type="file" id="fileInput" accept="image/heic,image/heif,.heic,.HEIC,image/*" style="display: none;">
        </label>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Processing spatial photo...</p>
        </div>

        <div class="permission-prompt" id="permissionPrompt">
            <h3 style="margin-bottom: 10px;">📱 Motion Permission Required</h3>
            <p style="margin-bottom: 15px;">To experience spatial photos like on iPhone, we need access to your device motion sensors.</p>
            <p style="margin-bottom: 15px; font-size: 12px; color: #666;">
                <strong>Safari iOS users:</strong> You'll see a popup asking for "Motion & Orientation" access. Tap "Allow" to continue.
            </p>
            <button onclick="requestMotionPermission()" style="width: 100%; font-size: 18px; padding: 15px;">
                ✓ Allow Motion & Orientation
            </button>
        </div>

        <div class="controls" id="controls">
            <div style="margin-bottom: 15px;">
                <button class="motion-btn" id="motionBtn" data-mode="motion">
                    📱 Motion View (Tilt Phone)
                </button>
            </div>
            <label style="font-weight: 600; display: block; margin-bottom: 10px;">Other Viewing Modes:</label>
            <div class="button-group">
                <button class="mode-btn" data-mode="sideBySide">Side by Side</button>
                <button class="mode-btn" data-mode="anaglyph">Anaglyph 3D</button>
                <button class="mode-btn" data-mode="wiggle">Wigglegram</button>
                <button class="mode-btn" data-mode="leftOnly">Left Eye</button>
                <button class="mode-btn" data-mode="rightOnly">Right Eye</button>
            </div>
        </div>

        <div class="viewer" id="viewer"></div>
    </div>

    <div class="motion-info" id="motionInfo">
        Tilt: <span id="tiltValue">0</span>° |
        Blend: <span id="blendValue">50</span>%
    </div>

    <script>
        let images = null;
        let wiggleInterval = null;
        let motionCanvas = null;
        let motionCtx = null;
        let leftImg = null;
        let rightImg = null;
        let currentMode = null;
        let motionEnabled = false;
        let permissionGranted = false;

        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const loading = document.getElementById('loading');
        const controls = document.getElementById('controls');
        const viewer = document.getElementById('viewer');
        const motionInfo = document.getElementById('motionInfo');
        const permissionPrompt = document.getElementById('permissionPrompt');
        const container = document.getElementById('container');
        const motionBtn = document.getElementById('motionBtn');

        // Upload area click is handled by the <label> element natively
        uploadArea.addEventListener('click', () => {
            console.log('Upload area clicked');
        });

        fileInput.addEventListener('change', async (e) => {
            console.log('File input changed', e.target.files);
            const file = e.target.files[0];
            if (!file) {
                console.log('No file selected');
                return;
            }
            console.log('Selected file:', file.name, file.type, file.size);

            // Hide upload area and show loading
            uploadArea.style.display = 'none';
            loading.classList.add('active');
            viewer.classList.remove('active');
            controls.classList.remove('active');

            try {
                console.log('Uploading file...');
                const uploadResponse = await fetch('/upload', {
                    method: 'POST',
                    body: await file.arrayBuffer(),
                    headers: {
                        'Content-Type': 'application/octet-stream'
                    }
                });

                console.log('Upload response status:', uploadResponse.status);

                if (!uploadResponse.ok) {
                    throw new Error('Upload failed with status: ' + uploadResponse.status);
                }

                const uploadResult = await uploadResponse.json();
                console.log('Upload result:', uploadResult);

                if (!uploadResult.success) {
                    throw new Error('Server failed to process the image');
                }

                console.log('Fetching processed images...');
                const response = await fetch('/images');

                if (!response.ok) {
                    throw new Error('Failed to fetch images');
                }

                images = await response.json();
                console.log('Images loaded:', images ? 'yes' : 'no');

                // Preload images
                console.log('Preloading images...');
                await loadImageElements();
                console.log('Images preloaded');

                loading.classList.remove('active');
                controls.classList.add('active');
                viewer.classList.add('active');

                // Check if motion is available
                if (typeof DeviceOrientationEvent !== 'undefined') {
                    if (typeof DeviceOrientationEvent.requestPermission === 'function') {
                        // iOS 13+ requires permission
                        permissionPrompt.classList.add('active');
                    } else {
                        // Android or older iOS
                        permissionGranted = true;
                        setupMotionListeners();
                    }
                }

                console.log('Rendering motion view...');
                renderView('motion');
                console.log('Done!');
            } catch (error) {
                console.error('Error:', error);
                alert('Error processing file: ' + error.message + '\n\nCheck the browser console for more details.');
                loading.classList.remove('active');
                uploadArea.style.display = 'block';
            }
        });

        async function requestMotionPermission() {
            if (typeof DeviceOrientationEvent.requestPermission === 'function') {
                try {
                    // Request both DeviceOrientation and DeviceMotion for Safari iOS 13+
                    const orientationPermission = await DeviceOrientationEvent.requestPermission();

                    let motionPermission = 'granted';
                    if (typeof DeviceMotionEvent.requestPermission === 'function') {
                        motionPermission = await DeviceMotionEvent.requestPermission();
                    }

                    if (orientationPermission === 'granted' && motionPermission === 'granted') {
                        permissionGranted = true;
                        permissionPrompt.classList.remove('active');
                        setupMotionListeners();
                        if (currentMode === 'motion') {
                            renderView('motion');
                        }
                        console.log('✓ Motion permissions granted');
                    } else {
                        alert('Motion permission denied. You can still use other viewing modes.');
                    }
                } catch (error) {
                    console.error('Permission error:', error);
                    alert('Could not request permission: ' + error.message + '\n\nMake sure you\'re using Safari on iOS.');
                }
            } else {
                // No permission needed (Android or older iOS)
                permissionGranted = true;
                permissionPrompt.classList.remove('active');
                setupMotionListeners();
                if (currentMode === 'motion') {
                    renderView('motion');
                }
                console.log('✓ Motion permissions not required on this device');
            }
        }

        function loadImageElements() {
            return new Promise((resolve, reject) => {
                let loaded = 0;
                leftImg = new Image();
                rightImg = new Image();

                const checkComplete = () => {
                    loaded++;
                    if (loaded === 2) resolve();
                };

                leftImg.onload = checkComplete;
                rightImg.onload = checkComplete;
                leftImg.onerror = reject;
                rightImg.onerror = reject;

                leftImg.src = 'data:image/png;base64,' + images.left;
                rightImg.src = 'data:image/png;base64,' + images.right;
            });
        }

        function setupMotionListeners() {
            console.log('Setting up motion listeners...');

            // Add both deviceorientation and devicemotion for better compatibility
            window.addEventListener('deviceorientation', handleMotion, true);

            // Test if motion events are actually firing
            let testTimeout = setTimeout(() => {
                console.warn('No motion events received after 3 seconds. Make sure device motion is enabled in Safari settings.');
            }, 3000);

            // Clear timeout once we receive first event
            const testHandler = () => {
                clearTimeout(testTimeout);
                console.log('✓ Motion events are working!');
                window.removeEventListener('deviceorientation', testHandler);
            };
            window.addEventListener('deviceorientation', testHandler, { once: true });
        }

        function handleMotion(event) {
            if (!motionEnabled || !motionCanvas || !motionCtx) return;

            // Get gamma (left-right tilt) and beta (front-back tilt)
            let gamma = event.gamma || 0; // -90 to 90
            let beta = event.beta || 0;   // -180 to 180

            // Normalize gamma to 0-1 range
            // When phone is tilted left (-45 to 0), show more of left image
            // When phone is tilted right (0 to 45), show more of right image
            const tiltRange = 30; // degrees of tilt to use
            let normalizedTilt = (gamma / tiltRange) + 0.5;
            normalizedTilt = Math.max(0, Math.min(1, normalizedTilt));

            // Update info display
            document.getElementById('tiltValue').textContent = gamma.toFixed(1);
            document.getElementById('blendValue').textContent = (normalizedTilt * 100).toFixed(0);

            // Blend between left and right images
            blendImages(normalizedTilt);
        }

        function blendImages(blend) {
            if (!leftImg || !rightImg || !motionCtx) return;

            const canvas = motionCanvas;
            const ctx = motionCtx;

            // Clear canvas
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Draw left image with opacity based on blend
            ctx.globalAlpha = 1 - blend;
            ctx.drawImage(leftImg, 0, 0, canvas.width, canvas.height);

            // Draw right image with opposite opacity
            ctx.globalAlpha = blend;
            ctx.drawImage(rightImg, 0, 0, canvas.width, canvas.height);

            ctx.globalAlpha = 1;
        }

        motionBtn.addEventListener('click', () => {
            if (!permissionGranted && typeof DeviceOrientationEvent.requestPermission === 'function') {
                permissionPrompt.classList.add('active');
            } else {
                document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.motion-btn').forEach(b => b.classList.remove('active'));
                motionBtn.classList.add('active');
                renderView('motion');
            }
        });

        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.motion-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                renderView(btn.dataset.mode);
            });
        });

        // Tap viewer to toggle fullscreen (for motion mode)
        viewer.addEventListener('click', () => {
            if (currentMode === 'motion') {
                viewer.classList.toggle('fullscreen');
                container.classList.toggle('minimal');
                if (viewer.classList.contains('fullscreen')) {
                    // Resize canvas for fullscreen
                    setTimeout(() => {
                        if (motionCanvas && leftImg) {
                            const aspect = leftImg.width / leftImg.height;
                            motionCanvas.width = window.innerWidth;
                            motionCanvas.height = window.innerWidth / aspect;
                            blendImages(0.5);
                        }
                    }, 100);
                }
            }
        });

        function renderView(mode) {
            if (!images) return;
            currentMode = mode;
            viewer.innerHTML = '';
            motionEnabled = false;
            motionInfo.classList.remove('active');
            if (wiggleInterval) {
                clearInterval(wiggleInterval);
                wiggleInterval = null;
            }

            switch (mode) {
                case 'motion':
                    if (!leftImg || !rightImg) {
                        alert('Images not loaded yet');
                        return;
                    }

                    // Create canvas for blending
                    motionCanvas = document.createElement('canvas');
                    motionCanvas.id = 'motionCanvas';
                    motionCanvas.width = leftImg.width;
                    motionCanvas.height = leftImg.height;
                    motionCtx = motionCanvas.getContext('2d');

                    viewer.appendChild(motionCanvas);

                    // Initial blend (center position)
                    blendImages(0.5);

                    motionEnabled = true;
                    motionInfo.classList.add('active');

                    if (!permissionGranted) {
                        // Show fallback message
                        const msg = document.createElement('div');
                        msg.style.cssText = 'position:absolute;top:10px;left:10px;right:10px;background:rgba(255,255,255,0.95);padding:20px;border-radius:10px;text-align:center;box-shadow:0 4px 12px rgba(0,0,0,0.2);';
                        msg.innerHTML = `
                            <strong style="display:block;margin-bottom:10px;font-size:16px;">📱 Motion Sensors Required</strong>
                            <p style="font-size:14px;margin-bottom:10px;">Click the "Motion View" button above to enable motion tracking.</p>
                            <p style="font-size:12px;color:#666;">
                                <strong>Safari iOS:</strong> Settings → Safari → Motion & Orientation Access → Enable for this site
                            </p>
                        `;
                        viewer.appendChild(msg);
                    } else {
                        // Show helpful tip for using motion
                        const tip = document.createElement('div');
                        tip.style.cssText = 'position:absolute;bottom:20px;left:20px;right:20px;background:rgba(0,0,0,0.7);color:white;padding:15px;border-radius:10px;text-align:center;font-size:14px;';
                        tip.innerHTML = '💡 Tilt your phone left and right to see the spatial effect!';
                        viewer.appendChild(tip);
                        setTimeout(() => tip.remove(), 5000);
                    }
                    break;

                case 'sideBySide':
                    viewer.innerHTML = `
                        <div class="image-container">
                            <img src="data:image/png;base64,${images.left}">
                            <img src="data:image/png;base64,${images.right}">
                        </div>`;
                    break;

                case 'anaglyph':
                    viewer.innerHTML = `<img src="data:image/png;base64,${images.anaglyph}">`;
                    break;

                case 'wiggle':
                    const img = document.createElement('img');
                    img.src = `data:image/png;base64,${images.left}`;
                    viewer.appendChild(img);
                    let showLeft = true;
                    wiggleInterval = setInterval(() => {
                        img.src = `data:image/png;base64,${showLeft ? images.left : images.right}`;
                        showLeft = !showLeft;
                    }, 500);
                    break;

                case 'leftOnly':
                    viewer.innerHTML = `<img src="data:image/png;base64,${images.left}">`;
                    break;

                case 'rightOnly':
                    viewer.innerHTML = `<img src="data:image/png;base64,${images.right}">`;
                    break;
            }
        }
    </script>
</body>
</html>'''

    def log_message(self, format, *args):
        """Log HTTP requests"""
        # Only log non-favicon requests to reduce noise
        if 'favicon' not in format % args:
            print(f"[HTTP] {format % args}")


def get_local_ip():
    """Get the local IP address of the machine"""
    try:
        # Create a socket to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Connect to an external server (doesn't actually send data)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "unknown"


def main():
    if len(sys.argv) < 2:
        print("Spatial Photo Viewer")
        print("=" * 50)
        print("\nUsage:")
        print("  1. Extract images: python spatial_photo_viewer.py <photo.heic>")
        print("  2. Web viewer:     python spatial_photo_viewer.py --server")
        print("\nOptions:")
        print("  --output-dir DIR   Specify output directory for extracted images")
        print("  --server          Start web server on http://0.0.0.0:8000")
        print("  --port PORT       Specify server port (default: 8000)")
        return

    if '--server' in sys.argv:
        port = 8000
        if '--port' in sys.argv:
            port_idx = sys.argv.index('--port') + 1
            port = int(sys.argv[port_idx])

        local_ip = get_local_ip()

        print(f"Starting Spatial Photo Viewer server...")
        print(f"\n📱 On this device:")
        print(f"   http://localhost:{port}")
        print(f"\n📱 On your phone (same network):")
        print(f"   http://{local_ip}:{port}")
        print(f"\nPress Ctrl+C to stop\n")

        server = HTTPServer(('0.0.0.0', port), SpatialPhotoHandler)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped")
    else:
        # Command line mode
        heic_path = sys.argv[1]

        if not Path(heic_path).exists():
            print(f"✗ File not found: {heic_path}")
            return

        output_dir = "."
        if '--output-dir' in sys.argv:
            output_dir = sys.argv[sys.argv.index('--output-dir') + 1]

        print(f"Processing: {heic_path}")
        print("=" * 50)

        extractor = SpatialPhotoExtractor(heic_path)

        if extractor.extract_images():
            extractor.save_images(output_dir)

            # Create additional formats
            base_name = Path(heic_path).stem
            extractor.create_side_by_side(f"{output_dir}/{base_name}_side_by_side.png")
            extractor.create_anaglyph(f"{output_dir}/{base_name}_anaglyph.png")

            print("\n✓ All images saved successfully!")
        else:
            print("\n✗ Failed to process spatial photo")


if __name__ == "__main__":
    main()
