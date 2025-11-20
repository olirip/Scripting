# iOS Haptic Scroll Demo

A demonstration of the `ios-haptic` npm package featuring a scroll view with haptic feedback.

## Features

- **5 Random Images**: Beautiful images from Picsum Photos
- **Scroll-based Haptic Feedback**: Each image triggers `haptic()` when entering the viewport
- **End Detection**: Triggers `haptic.error()` when reaching the bottom
- **Visual Feedback**: Smooth animations and status updates
- **Intersection Observer**: Efficient viewport detection

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Open the provided URL in your browser (typically `http://localhost:5173`)

## How It Works

- **Image Detection**: Uses Intersection Observer API to detect when 50% of an image is visible
- **Haptic Triggers**: Each image triggers `haptic()` only once (tracked via Set)
- **End Marker**: When the end marker becomes visible, `haptic.error()` is triggered
- **Status Bar**: Fixed bottom bar shows real-time feedback of haptic events

## Usage on iOS

For the best experience, open this demo on an iOS device with Safari to feel the actual haptic feedback.

## Files

- `scroll.html` - Main HTML structure
- `scroll.css` - Styling and animations
- `scroll.js` - Haptic logic and intersection observers
