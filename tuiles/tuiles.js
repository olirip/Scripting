class PhotoBook {
    constructor(images) {
        this.images = images;
        this.currentSpread = 0;
        this.book = document.getElementById('book');
        this.bookContainer = document.querySelector('.book-container');
        this.prevBtn = document.getElementById('prevBtn');
        this.nextBtn = document.getElementById('nextBtn');
        this.pageIndicator = document.getElementById('pageIndicator');

        this.init();
    }

    init() {
        this.createPages();
        this.setupEventListeners();
        this.updateControls();
        this.observeSpreads();
    }

    createPages() {
        // Create page spreads (pairs of pages)
        const spreads = [];

        for (let i = 0; i < this.images.length; i += 2) {
            const spread = document.createElement('div');
            spread.className = 'page-spread';
            spread.dataset.spreadIndex = spreads.length;

            // Left page
            const leftPage = this.createPage(this.images[i], 'left');
            spread.appendChild(leftPage);

            // Right page (if exists)
            if (i + 1 < this.images.length) {
                const rightPage = this.createPage(this.images[i + 1], 'right');
                spread.appendChild(rightPage);
            }

            spreads.push(spread);
            this.book.appendChild(spread);
        }

        // Mark first spread as active
        if (spreads.length > 0) {
            spreads[0].classList.add('active');
        }

        this.totalSpreads = spreads.length;
    }

    createPage(imageSrc, position) {
        const page = document.createElement('div');
        page.className = `page ${position} loading`;

        const img = document.createElement('img');
        img.src = imageSrc;
        img.alt = 'Book page';

        img.onload = () => {
            page.classList.remove('loading');
        };

        img.onerror = () => {
            page.classList.remove('loading');
            page.style.background = '#f0f0f0';
            page.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#999;">Image not found</div>';
        };

        page.appendChild(img);
        return page;
    }

    setupEventListeners() {
        this.prevBtn.addEventListener('click', () => this.previousSpread());
        this.nextBtn.addEventListener('click', () => this.nextSpread());

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') {
                this.previousSpread();
            } else if (e.key === 'ArrowRight') {
                this.nextSpread();
            }
        });

        // Scroll-based navigation
        this.bookContainer.addEventListener('scroll', () => {
            this.handleScroll();
        });

        // Mouse wheel horizontal scroll
        this.bookContainer.addEventListener('wheel', (e) => {
            if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
                e.preventDefault();
                this.bookContainer.scrollLeft += e.deltaY;
            }
        }, { passive: false });
    }

    observeSpreads() {
        const options = {
            root: this.bookContainer,
            threshold: 0.5
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    // Remove active class from all spreads
                    document.querySelectorAll('.page-spread').forEach(spread => {
                        spread.classList.remove('active');
                    });

                    // Add active class to current spread
                    entry.target.classList.add('active');

                    // Update current spread index
                    this.currentSpread = parseInt(entry.target.dataset.spreadIndex, 10);
                    this.updateControls();
                }
            });
        }, options);

        document.querySelectorAll('.page-spread').forEach(spread => {
            observer.observe(spread);
        });
    }

    handleScroll() {
        // This is called during scroll, observer handles the active state
        // You could add additional effects here if needed
    }

    goToSpread(index) {
        if (index < 0 || index >= this.totalSpreads) return;

        const spreads = document.querySelectorAll('.page-spread');
        const targetSpread = spreads[index];

        if (targetSpread) {
            targetSpread.scrollIntoView({
                behavior: 'smooth',
                block: 'nearest',
                inline: 'center'
            });
        }
    }

    nextSpread() {
        if (this.currentSpread < this.totalSpreads - 1) {
            this.goToSpread(this.currentSpread + 1);
        }
    }

    previousSpread() {
        if (this.currentSpread > 0) {
            this.goToSpread(this.currentSpread - 1);
        }
    }

    updateControls() {
        // Update buttons
        this.prevBtn.disabled = this.currentSpread === 0;
        this.nextBtn.disabled = this.currentSpread === this.totalSpreads - 1;

        // Update page indicator
        const startPage = this.currentSpread * 2 + 1;
        const endPage = Math.min(startPage + 1, this.images.length);
        this.pageIndicator.textContent = `${startPage}-${endPage} / ${this.images.length}`;
    }
}

// Configuration - Add your image paths here
const imageConfig = {
    images: [
        'https://picsum.photos/800/1200?random=1',
        'https://picsum.photos/800/1200?random=2',
        'https://picsum.photos/800/1200?random=3',
        'https://picsum.photos/800/1200?random=4',
        'https://picsum.photos/800/1200?random=5',
        'https://picsum.photos/800/1200?random=6',
        'https://picsum.photos/800/1200?random=7',
        'https://picsum.photos/800/1200?random=8',
        'https://picsum.photos/800/1200?random=9',
        'https://picsum.photos/800/1200?random=10',
        'https://picsum.photos/800/1200?random=11',
        'https://picsum.photos/800/1200?random=12'
    ]
};

// Initialize the photo book when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new PhotoBook(imageConfig.images);
    });
} else {
    new PhotoBook(imageConfig.images);
}
