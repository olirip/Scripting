# Photo Book Tuiles

A beautiful, interactive photo book viewer with 3D page-turning animations and smooth horizontal scrolling.

## Features

- **Book-style layout**: Photos displayed as spreads (two pages at a time)
- **3D page effects**: Subtle 3D rotations for realistic book appearance
- **Horizontal scrolling**: Smooth scroll navigation between pages
- **Multiple navigation methods**:
  - Mouse/trackpad horizontal scroll
  - Mouse wheel (vertical scrolling converted to horizontal)
  - Navigation buttons
  - Keyboard arrows (← →)
- **Responsive design**: Adapts to different screen sizes
- **Snap scrolling**: Pages snap into place for clean viewing
- **Page indicator**: Shows current page numbers

## Usage

1. Open `index.html` in a web browser
2. Navigate using:
   - Scroll horizontally
   - Click Previous/Next buttons
   - Use arrow keys
   - Mouse wheel

## Configuration

Edit the `imageConfig` object in `tuiles.js` to add your own images:

```javascript
const imageConfig = {
    images: [
        'path/to/image1.jpg',
        'path/to/image2.jpg',
        // Add more images...
    ]
};
```

You can use:
- Local file paths: `'./images/photo.jpg'`
- URLs: `'https://example.com/photo.jpg'`
- Data URIs

## Customization

### Page Size
Modify in `styles.css`:
```css
.page {
    width: 400px;  /* Adjust width */
    height: 600px; /* Adjust height */
}
```

### Colors
Change the gradient background in `styles.css`:
```css
body {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
```

### 3D Effect Intensity
Adjust rotation values in `styles.css`:
```css
.page-spread:not(.active) .page.left {
    transform: rotateY(-5deg); /* Increase/decrease angle */
}
```

## Browser Support

Works in all modern browsers that support:
- CSS 3D Transforms
- Intersection Observer API
- CSS Grid/Flexbox

## Tips

- Images are displayed in pairs (spreads)
- For best results, use images with similar aspect ratios
- The first page is a left page (odd pages are on the left)
- Loading states show while images are being fetched
