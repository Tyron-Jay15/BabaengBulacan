/**
 * BabaengBulacan service worker — static asset caching & update detection.
 * Bump CACHE_VERSION when static assets change materially.
 */
const CACHE_VERSION = 'v2';
const CACHE_NAME = `babaengbulacan-static-${CACHE_VERSION}`;

const STATIC_ASSETS = [
    '/static/css/main.css',
    '/static/css/mobile-access.css',
    '/static/js/main.js',
    '/static/js/mobile-utils.js',
    '/static/js/utils.js',
    '/static/js/pwa-install.js',
    '/static/icons/icon-192.png',
    '/static/icons/icon-512.png',
    '/manifest.webmanifest',
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) =>
            cache.addAll(STATIC_ASSETS).catch(() => undefined)
        )
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(
                keys.filter((k) => k.startsWith('babaengbulacan-static-') && k !== CACHE_NAME)
                    .map((k) => caches.delete(k))
            )
        ).then(() => self.clients.matchAll({ type: 'window' }))
            .then((clients) => {
                clients.forEach((client) => {
                    client.postMessage({ type: 'SW_UPDATED', version: CACHE_VERSION });
                });
            })
    );
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    const { request } = event;
    if (request.method !== 'GET') {
        return;
    }

    const url = new URL(request.url);

    if (
        url.pathname.startsWith('/admin') ||
        url.pathname.startsWith('/api/') ||
        url.pathname.startsWith('/media/') ||
        url.pathname.startsWith('/admin-dashboard/')
    ) {
        return;
    }

    if (url.pathname.startsWith('/static/') || url.pathname.includes('manifest')) {
        event.respondWith(
            caches.match(request).then((cached) =>
                cached || fetch(request).then((response) => {
                    if (response.ok) {
                        const clone = response.clone();
                        caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
                    }
                    return response;
                })
            )
        );
        return;
    }

    event.respondWith(
        fetch(request).catch(() =>
            caches.match(request).then((cached) => cached || caches.match('/accounts/login/'))
        )
    );
});
