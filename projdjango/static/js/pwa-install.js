/**
 * BabaengBulacan PWA — install prompt, floating download button, auto-update.
 */
(function () {
    'use strict';

    const SW_URL = '/sw.js';
    const DISMISS_KEY = 'babaeng_pwa_install_dismissed';

    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register(SW_URL, { scope: '/' })
            .then(function (registration) {
                registration.addEventListener('updatefound', function () {
                    const newWorker = registration.installing;
                    if (!newWorker) {
                        return;
                    }
                    newWorker.addEventListener('statechange', function () {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            showUpdateToast();
                        }
                    });
                });
                setInterval(function () {
                    registration.update();
                }, 60 * 60 * 1000);
            })
            .catch(function (err) {
                console.warn('Service worker registration failed:', err);
            });

        navigator.serviceWorker.addEventListener('message', function (event) {
            if (event.data && event.data.type === 'SW_UPDATED') {
                showUpdateToast();
            }
        });
    }

    let deferredPrompt = null;
    const banner = document.getElementById('pwaInstallBanner');

    function bindInstallButtons() {
        document.querySelectorAll('[data-pwa-install]').forEach(function (btn) {
            if (btn.dataset.pwaBound) {
                return;
            }
            btn.dataset.pwaBound = '1';
            btn.addEventListener('click', function (event) {
                event.preventDefault();
                triggerInstall();
            });
        });
    }

    function isStandalone() {
        return window.matchMedia('(display-mode: standalone)').matches
            || window.navigator.standalone === true;
    }

    function isMobileDevice() {
        return window.innerWidth < 992
            || /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }

    function isIOS() {
        return /iPhone|iPad|iPod/i.test(navigator.userAgent) && !window.MSStream;
    }

    function isAndroid() {
        return /Android/i.test(navigator.userAgent);
    }

    function showInstallControls() {
        if (isStandalone()) {
            hideInstallControls();
            return;
        }
        document.querySelectorAll('.pwa-install-control').forEach(function (el) {
            el.classList.add('is-visible');
            el.removeAttribute('hidden');
        });
    }

    function hideInstallControls() {
        document.querySelectorAll('.pwa-install-control').forEach(function (el) {
            el.classList.remove('is-visible');
            el.setAttribute('hidden', 'hidden');
        });
        hideBanner();
    }

    function showBanner() {
        if (banner && !sessionStorage.getItem(DISMISS_KEY)) {
            banner.classList.add('is-visible');
            document.body.classList.add('pwa-banner-visible');
        }
    }

    function hideBanner() {
        if (banner) {
            banner.classList.remove('is-visible');
            document.body.classList.remove('pwa-banner-visible');
        }
    }

    function showIOSInstructions() {
        if (typeof Swal === 'undefined') {
            alert('Tap the Share button in Safari, then choose "Add to Home Screen".');
            return;
        }
        Swal.fire({
            icon: 'info',
            title: 'Install BabaengBulacan',
            html: '<p class="mb-2">Add this app to your home screen:</p>'
                + '<ol class="text-start small mb-0">'
                + '<li>Tap the <strong>Share</strong> button <i class="fas fa-share-square"></i> in Safari</li>'
                + '<li>Scroll down and tap <strong>Add to Home Screen</strong></li>'
                + '<li>Tap <strong>Add</strong></li>'
                + '</ol>',
            confirmButtonText: 'Got it',
        });
    }

    function showAndroidManualInstructions() {
        if (typeof Swal === 'undefined') {
            alert('Open Chrome menu (⋮) and tap "Install app" or "Add to Home screen".');
            return;
        }
        Swal.fire({
            icon: 'info',
            title: 'Install BabaengBulacan',
            html: '<p class="mb-2">Add this app to your home screen:</p>'
                + '<ol class="text-start small mb-0">'
                + '<li>Tap the <strong>menu</strong> <i class="fas fa-ellipsis-v"></i> in Chrome (top right)</li>'
                + '<li>Tap <strong>Install app</strong> or <strong>Add to Home screen</strong></li>'
                + '<li>Tap <strong>Install</strong></li>'
                + '</ol>',
            confirmButtonText: 'Got it',
        });
    }

    async function triggerInstall() {
        if (isStandalone()) {
            return;
        }
        if (deferredPrompt) {
            deferredPrompt.prompt();
            const choice = await deferredPrompt.userChoice;
            if (choice.outcome === 'accepted') {
                hideInstallControls();
            }
            deferredPrompt = null;
            return;
        }
        if (isIOS()) {
            showIOSInstructions();
        } else if (isAndroid()) {
            showAndroidManualInstructions();
        } else if (typeof Swal !== 'undefined') {
            Swal.fire({
                icon: 'info',
                title: 'Install BabaengBulacan',
                text: 'Use your browser menu to install or add this site to your home screen.',
                confirmButtonText: 'OK',
            });
        }
    }

    window.addEventListener('beforeinstallprompt', function (e) {
        e.preventDefault();
        deferredPrompt = e;
        showInstallControls();
        showBanner();
    });

    const dismissBtn = document.getElementById('pwaDismissBtn');
    if (dismissBtn) {
        dismissBtn.addEventListener('click', function () {
            sessionStorage.setItem(DISMISS_KEY, '1');
            hideBanner();
        });
    }

    window.addEventListener('appinstalled', function () {
        deferredPrompt = null;
        hideInstallControls();
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                icon: 'success',
                title: 'BabaengBulacan Installed',
                text: 'Open the app from your home screen anytime.',
                timer: 3000,
                showConfirmButton: false,
            });
        }
    });

    function showUpdateToast() {
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                icon: 'info',
                title: 'Update Available',
                text: 'A new version of BabaengBulacan is ready.',
                showCancelButton: true,
                confirmButtonText: 'Reload',
                cancelButtonText: 'Later',
            }).then(function (result) {
                if (result.isConfirmed) {
                    window.location.reload();
                }
            });
        }
    }

    function init() {
        bindInstallButtons();
        if (isStandalone()) {
            hideInstallControls();
            return;
        }
        if (isMobileDevice()) {
            showInstallControls();
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    window.addEventListener('resize', function () {
        if (!isStandalone() && isMobileDevice()) {
            showInstallControls();
        }
    });

    window.BabaengPWA = { triggerInstall: triggerInstall, showUpdateToast: showUpdateToast };
})();
