# React Three Fiber with Bun

A React Three Fiber project set up with Bun.

## Getting Started

1. Install dependencies:
```bash
bun install
```

2. Start the development server:
```bash
bun run dev
```

The app will be available at `http://localhost:3000`. The server automatically rebuilds when you change files in the `src/` directory.

## Project Structure

- `src/index.jsx` - Entry point
- `src/App.jsx` - Main app component with Canvas
- `src/Scene.jsx` - 3D scene with a rotating box
- `index.html` - HTML entry point
- `server.js` - Development server with hot reload
- `bundle.js` - Generated bundle (auto-created on dev server start)

## Features

- React Three Fiber for 3D rendering
- React Three Drei for additional helpers
- Three.js for 3D graphics
- Bun for fast JavaScript runtime
- Automatic file watching and rebuilding
- Hot reload during development

## Building for Production

```bash
bun run build
```

This will create a production build in the `dist/` directory.

