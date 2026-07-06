// Mobile Utilities - Enhanced mobile responsiveness and interactions

/**
 * Mobile Device Detection and Utilities
 */
const MobileUtils = {
    // Device type detection
    isPhone: () => window.innerWidth < 576,
    isTablet: () => window.innerWidth >= 576 && window.innerWidth < 992,
    isDesktop: () => window.innerWidth >= 992,
    
    // Touch support detection
    isTouchDevice: () => {
        return (('ontouchstart' in window) ||
                (navigator.maxTouchPoints > 0) ||
                (navigator.msMaxTouchPoints > 0));
    },
    
    // Orientation detection
    isPortrait: () => window.innerHeight > window.innerWidth,
    isLandscape: () => window.innerHeight < window.innerWidth,
    
    // Get device info
    getDeviceInfo: function() {
        return {
            type: this.isPhone() ? 'phone' : this.isTablet() ? 'tablet' : 'desktop',
            orientation: this.isPortrait() ? 'portrait' : 'landscape',
            touchEnabled: this.isTouchDevice(),
            width: window.innerWidth,
            height: window.innerHeight
        };
    }
};

/**
 * Touch Event Handler
 */
const TouchHandler = {
    startX: 0,
    startY: 0,
    endX: 0,
    endY: 0,
    minSwipeDistance: 50,
    
    init: function() {
        document.addEventListener('touchstart', this.onTouchStart.bind(this), false);
        document.addEventListener('touchend', this.onTouchEnd.bind(this), false);
    },
    
    onTouchStart: function(e) {
        this.startX = e.touches[0].clientX;
        this.startY = e.touches[0].clientY;
    },
    
    onTouchEnd: function(e) {
        this.endX = e.changedTouches[0].clientX;
        this.endY = e.changedTouches[0].clientY;
        this.handleGestures();
    },
    
    handleGestures: function() {
        const deltaX = this.startX - this.endX;
        const deltaY = this.startY - this.endY;
        
        // Horizontal swipe
        if (Math.abs(deltaX) > this.minSwipeDistance) {
            if (deltaX > 0) {
                this.onSwipeLeft();
            } else {
                this.onSwipeRight();
            }
        }
        
        // Vertical swipe
        if (Math.abs(deltaY) > this.minSwipeDistance) {
            if (deltaY > 0) {
                this.onSwipeUp();
            } else {
                this.onSwipeDown();
            }
        }
    },
    
    onSwipeLeft: function() {
        // Custom implementation
        document.dispatchEvent(new CustomEvent('swipeLeft'));
    },
    
    onSwipeRight: function() {
        // Close mobile menu on swipe right
        const navCollapse = document.querySelector('.navbar-collapse');
        if (navCollapse && navCollapse.classList.contains('show')) {
            navCollapse.classList.remove('show');
        }
        document.dispatchEvent(new CustomEvent('swipeRight'));
    },
    
    onSwipeUp: function() {
        document.dispatchEvent(new CustomEvent('swipeUp'));
    },
    
    onSwipeDown: function() {
        document.dispatchEvent(new CustomEvent('swipeDown'));
    }
};

/**
 * Responsive Image Lazy Loading
 */
const LazyImageLoader = {
    init: function() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.add('loaded');
                        observer.unobserve(img);
                    }
                });
            });
            
            document.querySelectorAll('img[data-src]').forEach(img => imageObserver.observe(img));
        }
    }
};

/**
 * Viewport Height Fix for Mobile (address bar)
 */
const ViewportHeightFix = {
    init: function() {
        const setViewportHeight = () => {
            const vh = window.innerHeight * 0.01;
            document.documentElement.style.setProperty('--vh', `${vh}px`);
        };
        
        setViewportHeight();
        window.addEventListener('resize', setViewportHeight);
        window.addEventListener('orientationchange', setViewportHeight);
    }
};

/**
 * Input Focus Management
 */
const InputFocusManager = {
    init: function() {
        const inputs = document.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            input.addEventListener('focus', this.onInputFocus);
            input.addEventListener('blur', this.onInputBlur);
        });
    },
    
    onInputFocus: function(e) {
        const formGroup = e.target.closest('.form-group');
        if (formGroup) {
            formGroup.classList.add('focused');
            // Scroll input into view on mobile
            if (MobileUtils.isPhone()) {
                setTimeout(() => {
                    e.target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 100);
            }
        }
    },
    
    onInputBlur: function(e) {
        const formGroup = e.target.closest('.form-group');
        if (formGroup && !e.target.value) {
            formGroup.classList.remove('focused');
        }
    }
};

/**
 * Keyboard Height Detection (for mobile with keyboard)
 */
const KeyboardDetector = {
    init: function() {
        let initialHeight = window.visualViewport.height;
        
        window.visualViewport.addEventListener('resize', () => {
            const currentHeight = window.visualViewport.height;
            if (currentHeight < initialHeight * 0.75) {
                this.onKeyboardShow();
            } else {
                this.onKeyboardHide();
            }
        });
    },
    
    onKeyboardShow: function() {
        document.body.classList.add('keyboard-visible');
    },
    
    onKeyboardHide: function() {
        document.body.classList.remove('keyboard-visible');
    }
};

/**
 * Responsive Modal Dialog
 */
const ResponsiveModal = {
    init: function() {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.addEventListener('show.bs.modal', this.onModalShow);
            modal.addEventListener('hidden.bs.modal', this.onModalHidden);
        });
    },
    
    onModalShow: function(e) {
        if (MobileUtils.isPhone()) {
            const modal = e.target.querySelector('.modal-dialog');
            if (modal) {
                modal.style.marginTop = '0';
                modal.style.marginBottom = '0';
            }
        }
    },
    
    onModalHidden: function(e) {
        // Cleanup if needed
    }
};

/**
 * Performance Optimization
 */
const PerformanceOptimizer = {
    init: function() {
        // Reduce animation duration on low-end devices
        if (!window.requestAnimationFrame) {
            document.documentElement.style.setProperty('--animation-duration', '0.1s');
        }
        
        // Detect if reduced motion is preferred
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            document.documentElement.style.setProperty('--animation-duration', '0.01ms');
        }
    }
};

/**
 * Safe Area Support (for notched devices)
 */
const SafeAreaSupport = {
    init: function() {
        const supportsSafeArea = CSS.supports('padding-top', 'env(safe-area-inset-top)');
        if (supportsSafeArea) {
            document.documentElement.classList.add('has-safe-area');
            const style = document.createElement('style');
            style.textContent = `
                body {
                    padding-top: env(safe-area-inset-top);
                    padding-left: env(safe-area-inset-left);
                    padding-right: env(safe-area-inset-right);
                    padding-bottom: env(safe-area-inset-bottom);
                }
            `;
            document.head.appendChild(style);
        }
    }
};

/**
 * Initialize all mobile utilities
 */
function initializeMobileUtilities() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAll);
    } else {
        initAll();
    }
    
    function initAll() {
        TouchHandler.init();
        LazyImageLoader.init();
        ViewportHeightFix.init();
        InputFocusManager.init();
        ResponsiveModal.init();
        PerformanceOptimizer.init();
        SafeAreaSupport.init();
        
        // Optional: Initialize keyboard detector if needed
        if (MobileUtils.isTouchDevice()) {
            // KeyboardDetector.init();
        }
        
        console.log('Mobile utilities initialized', MobileUtils.getDeviceInfo());
    }
}

// Auto-initialize on load
initializeMobileUtilities();

// Export for use in other scripts
window.MobileUtils = MobileUtils;
window.TouchHandler = TouchHandler;
