/**
 * Mobile-friendly login — camera (HTTPS) and reCAPTCHA handling.
 */
(function () {
    'use strict';

    let videoStream = null;

    function isSecureForCamera() {
        return window.isSecureContext === true
            && navigator.mediaDevices
            && typeof navigator.mediaDevices.getUserMedia === 'function';
    }

    function showCameraBlockedReason(error) {
        const noCam = document.getElementById('no-camera');
        const msgEl = document.getElementById('camera-help-text');
        let message = 'Could not access the camera.';

        if (!window.isSecureContext) {
            message = 'Camera access requires a secure connection (HTTPS). '
                + 'Face verification is required to log in — open this site with HTTPS to use your camera.';
        } else if (error && error.name === 'NotAllowedError') {
            message = 'Camera permission was denied. Allow camera access in your browser settings, then tap Start Camera again.';
        } else if (error && error.name === 'NotFoundError') {
            message = 'No camera was found on this device.';
        } else if (error && error.message) {
            message = error.message;
        }

        if (noCam) {
            noCam.textContent = message;
            noCam.classList.remove('d-none');
        }
        if (msgEl) {
            msgEl.textContent = message;
        }

        if (typeof Swal !== 'undefined') {
            Swal.fire({
                icon: 'warning',
                title: 'Camera Unavailable',
                html: message.replace(/\n/g, '<br>'),
                confirmButtonText: 'OK',
            });
        }
    }

    async function startCamera() {
        const video = document.getElementById('video');
        const startBtn = document.getElementById('startCamera');
        const captureBtn = document.getElementById('captureFace');

        if (!isSecureForCamera()) {
            showCameraBlockedReason(null);
            return;
        }

        const constraintSets = [
            { video: { facingMode: { ideal: 'user' }, width: { ideal: 640 }, height: { ideal: 480 } }, audio: false },
            { video: { facingMode: 'user' }, audio: false },
            { video: true, audio: false },
        ];

        let lastError = null;
        for (let i = 0; i < constraintSets.length; i++) {
            try {
                if (videoStream) {
                    videoStream.getTracks().forEach(function (t) { t.stop(); });
                }
                videoStream = await navigator.mediaDevices.getUserMedia(constraintSets[i]);
                video.srcObject = videoStream;
                video.setAttribute('playsinline', '');
                video.setAttribute('webkit-playsinline', '');
                video.muted = true;

                await new Promise(function (resolve, reject) {
                    video.onloadedmetadata = function () {
                        video.play().then(resolve).catch(reject);
                    };
                    video.onerror = reject;
                });

                video.classList.remove('d-none');
                startBtn.classList.add('d-none');
                captureBtn.classList.remove('d-none');
                document.getElementById('no-camera').classList.add('d-none');
                return;
            } catch (err) {
                lastError = err;
            }
        }
        showCameraBlockedReason(lastError);
    }

    function captureFace() {
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const context = canvas.getContext('2d');

        if (video.videoWidth === 0 || video.videoHeight === 0) {
            if (typeof Swal !== 'undefined') {
                Swal.fire({ icon: 'error', title: 'Video Not Ready', text: 'Please wait for the camera to initialize.' });
            }
            return;
        }

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        document.getElementById('faceImage').value = canvas.toDataURL('image/jpeg', 0.82);

        if (videoStream) {
            videoStream.getTracks().forEach(function (t) { t.stop(); });
            videoStream = null;
        }

        video.classList.add('d-none');
        document.getElementById('captureFace').classList.add('d-none');
        document.getElementById('startCamera').classList.remove('d-none');
        document.getElementById('faceCaptured').classList.remove('d-none');
        document.getElementById('loginBtn').disabled = false;

        if (typeof Swal !== 'undefined') {
            Swal.fire({ icon: 'success', title: 'Face Captured!', timer: 2000, showConfirmButton: false });
        }
    }

    function showFaceRequiredAlert() {
        const message = 'Face verification is required. Tap Start Camera and capture your face before logging in.';
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                icon: 'warning',
                title: 'Face Verification Required',
                text: message,
            });
        } else {
            alert(message);
        }
    }

    function initRecaptchaMobile() {
        const wrap = document.getElementById('recaptcha-wrap');
        if (!wrap || typeof grecaptcha === 'undefined') {
            return;
        }
        if (window.innerWidth < 400) {
            wrap.classList.add('recaptcha-compact');
        }
    }

    window.onRecaptchaLoad = initRecaptchaMobile;

    function initLoginForm() {
        const startBtn = document.getElementById('startCamera');
        const captureBtn = document.getElementById('captureFace');
        const form = document.getElementById('loginForm');

        if (startBtn) {
            startBtn.addEventListener('click', startCamera);
        }
        if (captureBtn) {
            captureBtn.addEventListener('click', captureFace);
        }

        if (!isSecureForCamera()) {
            const insecureNote = document.getElementById('camera-insecure-note');
            if (insecureNote) {
                insecureNote.classList.remove('d-none');
            }
        }

        if (form) {
            form.addEventListener('submit', function (e) {
                const recaptchaEl = document.querySelector('.g-recaptcha');
                if (typeof grecaptcha !== 'undefined' && recaptchaEl && recaptchaEl.offsetParent !== null) {
                    if (!grecaptcha.getResponse()) {
                        e.preventDefault();
                        if (typeof Swal !== 'undefined') {
                            Swal.fire({
                                icon: 'warning',
                                title: 'reCAPTCHA Required',
                                text: 'Please complete the reCAPTCHA verification.',
                            });
                        }
                        return false;
                    }
                }

                const faceImage = document.getElementById('faceImage').value;
                if (!faceImage) {
                    e.preventDefault();
                    showFaceRequiredAlert();
                    return false;
                }
            });
        }

        initRecaptchaMobile();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initLoginForm);
    } else {
        initLoginForm();
    }
})();
