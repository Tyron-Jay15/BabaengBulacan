/**
 * Adds show/hide toggle to password fields across the site.
 */
(function () {
    'use strict';

    function enhancePasswordField(input) {
        if (!input || input.type !== 'password' || input.closest('.password-field-wrap')) {
            return;
        }

        const wrap = document.createElement('div');
        wrap.className = 'password-field-wrap';
        input.parentNode.insertBefore(wrap, input);
        wrap.appendChild(input);

        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'password-toggle-btn';
        btn.setAttribute('aria-label', 'Show password');
        btn.setAttribute('aria-pressed', 'false');
        btn.innerHTML = '<span class="password-toggle-icon" aria-hidden="true"><i class="fas fa-eye"></i></span>';

        btn.addEventListener('click', function () {
            const showing = input.type === 'text';
            input.type = showing ? 'password' : 'text';
            btn.setAttribute('aria-pressed', showing ? 'false' : 'true');
            btn.setAttribute('aria-label', showing ? 'Show password' : 'Hide password');
            btn.classList.toggle('is-active', !showing);
            const icon = btn.querySelector('i');
            if (icon) {
                icon.classList.toggle('fa-eye', showing);
                icon.classList.toggle('fa-eye-slash', !showing);
            }
        });

        wrap.appendChild(btn);
    }

    function initPasswordToggles() {
        document.querySelectorAll('input[type="password"]').forEach(enhancePasswordField);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPasswordToggles);
    } else {
        initPasswordToggles();
    }
})();
