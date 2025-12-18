#!/usr/bin/env python3
"""
Generate individual viewer HTML pages for each .ply file in the output directory.
"""

import os
from pathlib import Path


VIEWER_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - 3D Gaussian Splatting Viewer</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #1a1a1a;
            color: #ffffff;
            overflow: hidden;
        }}

        #canvas-container {{
            width: 100vw;
            height: 100vh;
            position: relative;
        }}

        #controls {{
            position: absolute;
            top: 20px;
            left: 20px;
            z-index: 100;
            background: rgba(0, 0, 0, 0.7);
            padding: 20px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
            min-width: 250px;
        }}

        .control-group {{
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }}

        .control-group label {{
            display: block;
            margin-bottom: 5px;
            font-size: 12px;
            color: #ccc;
        }}

        .control-group input[type="range"] {{
            width: 100%;
            margin-bottom: 10px;
        }}

        #back-button {{
            display: inline-block;
            padding: 8px 16px;
            background: #4a9eff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-size: 12px;
            margin-bottom: 15px;
            transition: background 0.3s;
        }}

        #back-button:hover {{
            background: #3a8eef;
        }}

        #status {{
            margin-top: 15px;
            padding: 10px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 5px;
            font-size: 12px;
            min-height: 40px;
        }}

        #info {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: rgba(0, 0, 0, 0.7);
            padding: 10px 15px;
            border-radius: 5px;
            font-size: 11px;
            color: #aaa;
            backdrop-filter: blur(10px);
        }}
    </style>
</head>
<body>
    <div id="canvas-container"></div>
    
    <div id="controls">
        <a href="index.html" id="back-button">← Back to Gallery</a>
        <h3 style="margin: 10px 0; font-size: 14px;">{title}</h3>
        
        <div id="status">Loading {filename}...</div>
        
        <div class="control-group">
            <label for="scale">Scale: <span id="scale-value">1.0</span></label>
            <input type="range" id="scale" min="0.1" max="5" step="0.1" value="1.0">
        </div>
        
        <div class="control-group">
            <label for="rotation-speed">Rotation Speed: <span id="rotation-value">0</span></label>
            <input type="range" id="rotation-speed" min="0" max="2" step="0.1" value="0">
        </div>
    </div>
    
    <div id="info">
        Left click + drag: Rotate | Right click + drag: Pan | Scroll: Zoom
    </div>

    <!-- Load Three.js and Spark (Gaussian Splatting renderer) from CDN -->
    <script type="importmap">
    {{
        "imports": {{
            "three": "https://cdn.jsdelivr.net/npm/three@0.178.0/build/three.module.js",
            "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.178.0/examples/jsm/",
            "@sparkjsdev/spark": "https://sparkjs.dev/releases/spark/0.1.10/spark.module.js"
        }}
    }}
    </script>

    <script type="module">
        import * as THREE from 'three';
        import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
        import {{ SplatMesh }} from '@sparkjsdev/spark';

        // Make THREE available globally for Spark.js compatibility
        window.THREE = THREE;

        const PLY_FILE = '{ply_path}';

        let scene, camera, renderer, controls;
        let splatMesh = null;
        let rotationSpeed = 0;

        // Initialize scene
        function init() {{
            // Scene
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x1a1a1a);

            // Camera
            camera = new THREE.PerspectiveCamera(
                75,
                window.innerWidth / window.innerHeight,
                0.1,
                1000
            );
            camera.position.set(0, 0, 5);

            // Renderer
            renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.setPixelRatio(window.devicePixelRatio);
            document.getElementById('canvas-container').appendChild(renderer.domElement);

            // Controls
            controls = new OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;

            // Grid helper
            const gridHelper = new THREE.GridHelper(10, 10, 0x444444, 0x222222);
            scene.add(gridHelper);

            // Axes helper
            const axesHelper = new THREE.AxesHelper(2);
            scene.add(axesHelper);

            // Controls
            document.getElementById('scale').addEventListener('input', (e) => {{
                const scale = parseFloat(e.target.value);
                document.getElementById('scale-value').textContent = scale.toFixed(1);
                if (splatMesh) {{
                    splatMesh.scale.set(scale, scale, scale);
                }}
            }});

            document.getElementById('rotation-speed').addEventListener('input', (e) => {{
                rotationSpeed = parseFloat(e.target.value);
                document.getElementById('rotation-value').textContent = rotationSpeed.toFixed(1);
            }});

            // Window resize
            window.addEventListener('resize', () => {{
                camera.aspect = window.innerWidth / window.innerHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, window.innerHeight);
            }});

            // Load the PLY file
            loadPLYFile();

            // Animation loop
            animate();
        }}

        async function loadPLYFile() {{
            const status = document.getElementById('status');
            status.textContent = `Loading ${{PLY_FILE}}...`;

            try {{
                // Remove previous splat if exists
                if (splatMesh) {{
                    scene.remove(splatMesh);
                    if (splatMesh.dispose) {{
                        splatMesh.dispose();
                    }}
                    splatMesh = null;
                }}

                // Use Spark's SplatMesh for proper Gaussian Splatting rendering
                status.textContent = `Loading 3D Gaussian Splatting model...`;
                
                const splat = new SplatMesh({{ url: PLY_FILE }});
                
                // Rotate 180 degrees around X axis to fix upside-down orientation
                splat.rotation.x = Math.PI;
                
                // Spark loads asynchronously - wait a bit and check if it's ready
                // The splat will be added to scene immediately and render when ready
                scene.add(splat);
                splatMesh = splat;

                // Wait for splat to be ready (check periodically)
                const checkReady = setInterval(() => {{
                    if (splat.ready !== undefined && splat.ready) {{
                        clearInterval(checkReady);
                        status.textContent = `Loaded: 3D Gaussian Splatting model`;
                        
                        // Adjust camera after a short delay to ensure bounding box is computed
                        setTimeout(() => {{
                            if (splat.boundingBox) {{
                                const box = splat.boundingBox;
                                const center = new THREE.Vector3();
                                box.getCenter(center);
                                const size = box.getSize(new THREE.Vector3());
                                const maxDim = Math.max(size.x, size.y, size.z);
                                const distance = maxDim * 1.5;

                                camera.position.set(0, 0, distance);
                                controls.target.copy(center);
                                controls.update();
                            }} else {{
                                camera.position.set(0, 0, 3);
                                controls.target.set(0, 0, 0);
                                controls.update();
                            }}
                        }}, 500);
                    }}
                }}, 100);

                // Timeout after 10 seconds
                setTimeout(() => {{
                    clearInterval(checkReady);
                    if (status.textContent.includes('Loading')) {{
                        status.textContent = `Model loading (may take a moment for large files)...`;
                    }}
                }}, 10000);

            }} catch (error) {{
                console.error('Error loading PLY:', error);
                status.textContent = `Error: ${{error.message}}. Trying fallback method...`;
                
                // Fallback to basic PLY loader if Spark doesn't work
                loadPLYFileFallback();
            }}
        }}

        function loadPLYFileFallback() {{
            const status = document.getElementById('status');
            status.textContent = `Loading ${{PLY_FILE}} (fallback mode)...`;

            import('three/addons/loaders/PLYLoader.js').then(({{ PLYLoader }}) => {{
                const loader = new PLYLoader();
                
                loader.load(
                    PLY_FILE,
                    (geometry) => {{
                        try {{
                            // Remove previous splat if exists
                            if (splatMesh) {{
                                scene.remove(splatMesh);
                                if (splatMesh.geometry) {{
                                    splatMesh.geometry.dispose();
                                }}
                                if (splatMesh.material) {{
                                    splatMesh.material.dispose();
                                }}
                            }}

                            // Use larger points for better visibility
                            const material = new THREE.PointsMaterial({{
                                size: 0.05,
                                vertexColors: geometry.attributes.color !== undefined,
                                color: geometry.attributes.color ? 0xffffff : 0x4a9eff,
                                sizeAttenuation: true,
                                transparent: true,
                                opacity: 0.8,
                            }});

                            const points = new THREE.Points(geometry, material);
                            
                            // Center and scale
                            geometry.computeBoundingBox();
                            const box = geometry.boundingBox;
                            const center = box.getCenter(new THREE.Vector3());
                            const size = box.getSize(new THREE.Vector3());
                            const maxDim = Math.max(size.x, size.y, size.z);
                            const scale = 2 / maxDim;

                            points.position.sub(center);
                            points.scale.set(scale, scale, scale);
                            
                            // Rotate 180 degrees around X axis to fix upside-down orientation
                            points.rotation.x = Math.PI;

                            scene.add(points);
                            splatMesh = points;

                            // Adjust camera
                            camera.position.set(0, 0, 3);
                            controls.target.set(0, 0, 0);
                            controls.update();

                            const pointCount = geometry.attributes.position.count;
                            status.textContent = `Loaded: ${{pointCount.toLocaleString()}} points (fallback - not true 3DGS rendering)`;
                        }} catch (error) {{
                            console.error('Error processing PLY:', error);
                            status.textContent = `Error: ${{error.message}}`;
                        }}
                    }},
                    (progress) => {{
                        if (progress.total > 0) {{
                            const percent = (progress.loaded / progress.total * 100).toFixed(1);
                            status.textContent = `Loading: ${{percent}}%`;
                        }}
                    }},
                    (error) => {{
                        console.error('Error loading PLY:', error);
                        status.textContent = `Error loading file: ${{error.message}}`;
                    }}
                );
            }});
        }}

        function animate() {{
            requestAnimationFrame(animate);

            if (splatMesh && rotationSpeed > 0) {{
                splatMesh.rotation.y += rotationSpeed * 0.01;
            }}

            controls.update();
            renderer.render(scene, camera);
        }}

        // Start
        init();
    </script>
</body>
</html>
'''


def find_ply_files(output_dir):
    """Find all .ply files in the output directory (recursively)."""
    output_path = Path(output_dir)
    if not output_path.exists():
        return []

    # Search recursively for .ply files
    all_ply_files = list(output_path.rglob("*.ply"))

    # Group by filename to handle duplicates
    # Prefer files in subdirectories over files directly in output/
    ply_dict = {}
    for ply_file in all_ply_files:
        filename = ply_file.name
        # If we haven't seen this filename, or if this one is in a subdirectory, use it
        if filename not in ply_dict or len(ply_file.parts) > len(ply_dict[filename].parts):
            ply_dict[filename] = ply_file

    return sorted(ply_dict.values())


def generate_viewer_page(ply_file, base_dir):
    """Generate an HTML viewer page for a .ply file."""
    ply_path = Path(ply_file)
    filename = ply_path.name
    title = ply_path.stem

    # Create viewer filename (e.g., card_0.html for card_0.ply)
    viewer_filename = f"{ply_path.stem}.html"
    viewer_path = Path(base_dir) / viewer_filename

    # Calculate relative path from viewer (in root) to ply file
    # ply_file is already relative to the current working directory
    # Make sure we have an absolute path for proper relative calculation
    base_path = Path(base_dir).resolve()
    ply_abs_path = ply_path.resolve()

    # Get relative path from base to ply file
    try:
        ply_relative_path = ply_abs_path.relative_to(base_path).as_posix()
    except ValueError:
        # If paths don't share a common ancestor, use the path as-is
        ply_relative_path = ply_path.as_posix()

    # Generate HTML
    html_content = VIEWER_TEMPLATE.format(
        title=title,
        filename=filename,
        ply_path=ply_relative_path
    )

    # Write to file
    viewer_path.write_text(html_content, encoding='utf-8')
    print(f"Generated: {viewer_filename} -> {ply_relative_path}")

    return viewer_filename, title


def generate_launcher_index(ply_files_info, output_dir):
    """Generate the launcher index.html page."""
    index_path = Path(output_dir).parent / "index.html"

    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D Gaussian Splatting Gallery</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            color: #ffffff;
            min-height: 100vh;
            padding: 40px 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            margin-bottom: 50px;
        }

        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #4a9eff 0%, #6ab4ff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .subtitle {
            color: #aaa;
            font-size: 1.1em;
        }

        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 30px;
            margin-top: 40px;
        }

        .gallery-item {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 25px;
            transition: all 0.3s ease;
            cursor: pointer;
            border: 2px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
        }

        .gallery-item:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.1);
            border-color: #4a9eff;
            box-shadow: 0 10px 30px rgba(74, 158, 255, 0.3);
        }

        .gallery-item a {
            text-decoration: none;
            color: inherit;
            display: block;
        }

        .gallery-item h3 {
            font-size: 1.3em;
            margin-bottom: 10px;
            color: #4a9eff;
        }

        .gallery-item p {
            color: #ccc;
            font-size: 0.9em;
            margin-top: 10px;
        }

        .icon {
            font-size: 3em;
            margin-bottom: 15px;
            opacity: 0.8;
        }

        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #888;
        }

        .empty-state h2 {
            font-size: 1.5em;
            margin-bottom: 15px;
        }

        .empty-state p {
            font-size: 1.1em;
            line-height: 1.6;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>3D Gaussian Splatting Gallery</h1>
            <p class="subtitle">Select a model to view in 3D</p>
        </header>
        
        <div class="gallery">
'''

    if ply_files_info:
        for viewer_file, title in ply_files_info:
            html_content += f'''            <div class="gallery-item">
                <a href="{viewer_file}">
                    <div class="icon">🎨</div>
                    <h3>{title}</h3>
                    <p>Click to view in 3D</p>
                </a>
            </div>
'''
    else:
        html_content += '''            <div class="empty-state">
                <h2>No 3D models found</h2>
                <p>Run <code>process_images.py</code> to generate .ply files,<br>then run this script again to generate viewers.</p>
            </div>
'''

    html_content += '''        </div>
    </div>
</body>
</html>
'''

    index_path.write_text(html_content, encoding='utf-8')
    print(f"\nGenerated: index.html")


def main():
    """Main function to generate all viewer pages."""
    output_dir = "./output"
    base_dir = Path(".")

    print("=" * 60)
    print("3D Gaussian Splatting Viewer Generator")
    print("=" * 60)
    print()

    # Find all .ply files
    ply_files = find_ply_files(output_dir)

    if not ply_files:
        print(f"No .ply files found in {output_dir}")
        print("Run process_images.py first to generate .ply files.")
        # Still generate an empty launcher
        generate_launcher_index([], output_dir)
        return

    print(f"Found {len(ply_files)} .ply file(s):")
    for ply_file in ply_files:
        print(f"  - {ply_file.name}")
    print()

    # Generate viewer pages
    ply_files_info = []
    for ply_file in ply_files:
        viewer_file, title = generate_viewer_page(ply_file, base_dir)
        ply_files_info.append((viewer_file, title))

    print()

    # Generate launcher index
    generate_launcher_index(ply_files_info, output_dir)

    print()
    print("=" * 60)
    print(f"Successfully generated {len(ply_files_info)} viewer page(s)")
    print("=" * 60)


if __name__ == "__main__":
    main()
