import { haptic, supportsHaptics } from 'https://esm.sh/ios-haptics';

// Track which images have already triggered haptic
const triggeredImages = new Set();
let hasReachedEnd = false;

// Status update helper
function updateStatus(message) {
    const statusEl = document.getElementById('haptic-status');
    if (statusEl) {
        statusEl.textContent = message;
        // Reset message after 2 seconds
        setTimeout(() => {
            if (statusEl.textContent === message) {
                statusEl.textContent = 'Keep scrolling...';
            }
        }, 2000);
    }
}

// Debug info
console.log('Haptics support:', supportsHaptics);
console.log('Navigator vibrate:', 'vibrate' in navigator);
console.log('User agent:', navigator.userAgent);

// Intersection Observer for image cards
const imageObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const card = entry.target;
            const index = card.dataset.index;

            // Add visual effect
            card.classList.add('in-view');

            // Trigger haptic only once per image when it enters viewport
            if (!triggeredImages.has(index)) {
                triggeredImages.add(index);
                try {
                    haptic();
                    updateStatus(`✓ Image ${parseInt(index, 10) + 1} - Haptic triggered!`);
                    console.log(`✓ Scroll haptic triggered for image ${parseInt(index, 10) + 1}`);
                } catch (error) {
                    console.log('❌ Haptic failed:', error);
                    updateStatus(`Image ${parseInt(index, 10) + 1} in view`);
                }
            }
        }
    });
}, {
    threshold: 0.5, // Trigger when 50% of the image is visible
    rootMargin: '0px'
});

// Intersection Observer for end marker
const endObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting && !hasReachedEnd) {
            hasReachedEnd = true;
            try {
                haptic.error();
                updateStatus('🔴 End reached - Error haptic triggered!');
                console.log('✓ End reached - haptic.error() triggered');
            } catch (error) {
                console.log('❌ End haptic failed:', error);
                updateStatus('🔴 End reached!');
            }

            // Visual feedback
            entry.target.style.animation = 'pulse 0.5s ease';
        }
    });
}, {
    threshold: 0.3,
    rootMargin: '0px'
});

// Initialize observers when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Show warning if not supported
    if (!supportsHaptics) {
        const warningEl = document.createElement('div');
        warningEl.style.cssText = 'padding: 20px; background: #ff6b6b; color: white; text-align: center; border-radius: 10px; margin: 20px;';
        warningEl.textContent = 'Haptics not supported on this device. Please try on iOS Safari.';
        document.body.prepend(warningEl);
    }

    // Observe all image cards
    const imageCards = document.querySelectorAll('.image-card');
    imageCards.forEach(card => {
        imageObserver.observe(card);

        // Also keep onclick handler as backup
        card.onclick = () => {
            const index = card.dataset.index;
            haptic();
            updateStatus(`✓ Image ${parseInt(index, 10) + 1} - Click haptic triggered!`);
            console.log(`✓ Click haptic triggered for image ${parseInt(index, 10) + 1}`);
        };
    });

    // Observe end marker
    const endMarker = document.querySelector('.end-marker');
    if (endMarker) {
        endObserver.observe(endMarker);

        // onclick handler as backup
        endMarker.onclick = () => {
            haptic.error();
            updateStatus('🔴 End - Error haptic triggered!');
            console.log('✓ Click error haptic triggered');
        };
    }

    // Test button - simple onclick like the working example
    const testBtn = document.getElementById('test-haptic-btn');
    if (testBtn) {
        testBtn.onclick = () => {
            haptic();
            updateStatus('🧪 Test haptic triggered!');
            console.log('✓ Test button haptic triggered');
        };
    }

    console.log('iOS Haptic Scroll Demo initialized');
    console.log('Haptics support:', supportsHaptics);
    console.log('Observing', imageCards.length, 'images');
});

// Add pulse animation dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
`;
document.head.appendChild(style);
