// BabaengBulacan Main JavaScript - Mobile Optimized

// Mobile Detection
const isMobile = () => window.innerWidth < 768;
const isTablet = () => window.innerWidth >= 768 && window.innerWidth < 1024;
const isDesktop = () => window.innerWidth >= 1024;

// Initialize on document ready
$(document).ready(function() {
    initializeTooltips();
    initializeAlerts();
    initializeReportPrompt();
    initializeMobileMenu();
    initializeFormHandlers();
    initializeTouchEvents();
    initializeResponsiveImages();
    initializeScrollAnimations();
    initializeFormValidation();
    handleWindowResize();
});

// Handle window resize for responsive behavior
function handleWindowResize() {
    $(window).on('resize', function() {
        if (isDesktop()) {
            $('.navbar-collapse').removeClass('show');
        }
    });
}

// Initialize Bootstrap Tooltips
function initializeTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize Alert Messages with animations
function initializeAlerts() {
    // Auto-hide alerts after 5 seconds
    $('.alert').each(function() {
        const $alert = $(this);
        const $closeBtn = $alert.find('.btn-close');
        
        // Manual close button
        $closeBtn.on('click', function() {
            $alert.fadeOut('fast', function() {
                $(this).remove();
            });
        });
        
        // Auto close
        setTimeout(function() {
            if ($alert.is(':visible')) {
                $alert.fadeOut('slow', function() {
                    $(this).remove();
                });
            }
        }, 5000);
    });
}

// Initialize Mobile Menu
function initializeMobileMenu() {
    const $navbarToggler = $('.navbar-toggler');
    const $navbarCollapse = $('.navbar-collapse');
    
    $navbarToggler.on('click', function() {
        $navbarCollapse.toggleClass('show');
    });
    
    // Close menu when clicking on a link
    $('.navbar-collapse .nav-link').on('click', function() {
        $navbarCollapse.removeClass('show');
    });
    
    // Close menu when clicking outside
    $(document).on('click', function(event) {
        if (!$(event.target).closest('.navbar').length && $navbarCollapse.hasClass('show')) {
            $navbarCollapse.removeClass('show');
        }
    });
}

// Prompt user to create an account before reporting an incident
function initializeReportPrompt() {
    // Applies to report buttons and links that require an account
    $(document).on('click', '.btn-quick-report, a.require-account', function(event) {
        event.preventDefault();

        const swalConfig = {
            icon: 'info',
            title: 'Create an account to report',
            text: 'To report an incident, you need to create an account first so we can keep your submission secure.',
            showCancelButton: true,
            confirmButtonText: 'Create Account',
            cancelButtonText: 'Continue as Guest',
            reverseButtons: true,
            didOpen: () => {
                // Adjust for mobile
                if (isMobile()) {
                    $('.swal2-popup').css('width', '90%');
                }
            }
        };

        // Use SweetAlert2 when available; otherwise fall back to the native confirm dialog
        if (typeof Swal !== 'undefined') {
            Swal.fire(swalConfig).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = '/accounts/register/';
                } else if (result.dismiss === Swal.DismissReason.cancel) {
                    window.location.href = '/reports/anonymous/';
                }
            });
        } else {
            const proceed = window.confirm('To report an incident, you need an account. Click OK to create one, or Cancel to continue as a guest.');
            if (proceed) {
                window.location.href = '/accounts/register/';
            } else {
                window.location.href = '/reports/anonymous/';
            }
        }
    });
}

// Initialize Touch Events
function initializeTouchEvents() {
    let touchStartX = 0;
    let touchEndX = 0;

    // Handle swipe gestures
    document.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
    });

    document.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    });

    function handleSwipe() {
        const swipeThreshold = 50;
        const diff = touchStartX - touchEndX;

        // Swipe left
        if (diff > swipeThreshold) {
            handleSwipeLeft();
        }
        // Swipe right
        else if (diff < -swipeThreshold) {
            handleSwipeRight();
        }
    }

    function handleSwipeLeft() {
        // Can be customized for specific actions
    }

    function handleSwipeRight() {
        // Close mobile menu if open
        const $navbarCollapse = $('.navbar-collapse');
        if ($navbarCollapse.hasClass('show')) {
            $navbarCollapse.removeClass('show');
        }
    }
}

// Initialize Form Handlers
function initializeFormHandlers() {
    // Set up dynamic form inputs
    $('input[type="text"], input[type="email"], textarea').on('focus', function() {
        $(this).closest('.form-group').addClass('focused');
    }).on('blur', function() {
        if (!$(this).val()) {
            $(this).closest('.form-group').removeClass('focused');
        }
    });

    // Handle file uploads with visual feedback
    $('input[type="file"]').on('change', function() {
        const filename = $(this).val().split('\\').pop();
        if (filename) {
            $(this).closest('.form-group').find('.file-name').text(filename);
        }
    });
}

// Initialize Responsive Images
function initializeResponsiveImages() {
    const $images = $('img.img-responsive, img.img-thumbnail');
    
    $images.each(function() {
        $(this).addClass('lazyload');
    });
}

// Initialize Scroll Animations
function initializeScrollAnimations() {
    // Add scroll animation classes to elements
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                $(entry.target).addClass('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    $('.stat-card, .program-card, section').each(function() {
        observer.observe(this);
    });
}

// Initialize Form Validation
function initializeFormValidation() {
    $('form').on('submit', function(e) {
        const form = this;
        if (!form.checkValidity()) {
            e.preventDefault();
            e.stopPropagation();
            form.classList.add('was-validated');
            
            // Scroll to first invalid field on mobile
            if (isMobile()) {
                const firstInvalid = $(form).find(':invalid').first();
                if (firstInvalid.length) {
                    $('html, body').animate({
                        scrollTop: firstInvalid.offset().top - 100
                    }, 300);
                }
            }
        }
        form.classList.add('was-validated');
    });
}

// API Helper Functions
const API = {
    baseURL: '/api',

    get: function(endpoint) {
        return $.ajax({
            url: this.baseURL + endpoint,
            method: 'GET',
            dataType: 'json'
        });
    },

    post: function(endpoint, data) {
        return $.ajax({
            url: this.baseURL + endpoint,
            method: 'POST',
            data: JSON.stringify(data),
            contentType: 'application/json',
            dataType: 'json'
        });
    },

    uploadFile: function(endpoint, formData) {
        return $.ajax({
            url: this.baseURL + endpoint,
            method: 'POST',
            data: formData,
            processData: false,
            contentType: false
        });
    }
};

// Utility Functions
function showLoading() {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            title: 'Please wait...',
            allowOutsideClick: false,
            allowEscapeKey: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });
    }
}

function hideLoading() {
    if (typeof Swal !== 'undefined') {
        Swal.close();
    }
}

function showSuccess(message) {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            icon: 'success',
            title: 'Success!',
            text: message,
            timer: 3000,
            showConfirmButton: false,
            didOpen: () => {
                if (isMobile()) {
                    $('.swal2-popup').css('width', '90%');
                }
            }
        });
    } else {
        alert('Success: ' + message);
    }
}

function showError(message) {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: message,
            didOpen: () => {
                if (isMobile()) {
                    $('.swal2-popup').css('width', '90%');
                }
            }
        });
    } else {
        alert('Error: ' + message);
    }
}

function showInfo(message) {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            icon: 'info',
            title: 'Information',
            text: message,
            didOpen: () => {
                if (isMobile()) {
                    $('.swal2-popup').css('width', '90%');
                }
            }
        });
    } else {
        alert(message);
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Form Validation Helper
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return false;
    }
    return true;
}

// Responsive form cleanup
$(window).on('load resize', function() {
    if (isMobile()) {
        // Add mobile-specific classes
        $('body').addClass('mobile-view');
    } else {
        $('body').removeClass('mobile-view');
    }
});

// Add fade-in animation CSS
const style = document.createElement('style');
style.textContent = `
    .fade-in {
        animation: fadeIn 0.6s ease-in;
    }
    
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .focused {
        transition: all 0.3s ease;
    }
`;
document.head.appendChild(style);

// Console log to verify mobile optimization is loaded
console.log('Mobile optimized JavaScript loaded. Device type:', isMobile() ? 'Mobile' : isTablet() ? 'Tablet' : 'Desktop');