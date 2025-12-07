const CACHE_NAME = 'royal-crumbs-v3';
const urlsToCache = [
    '/',
    '/home',
    '/login',
    '/games',
    '/support',
    '/account/cartera',
    '/static/css/main.css',
    '/static/css/auth.css',
    '/static/img/logo.png',
    '/static/img/logo-192.png',
    '/static/img/logo-512.png',
    '/static/img/home_icon.png',
    '/static/img/games_icon.png',
    '/static/img/support_icon.png',
    '/static/img/wallet_icon.png',
    '/static/img/usuario_icon.png',
    '/static/img/casino.jpg',
    '/static/img/bonos.jpg',
    '/offline'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Opened cache');
                return cache.addAll(urlsToCache);
            })
    );
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', event => {
    // Strategy: Network First for HTML, Cache First for assets
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request)
                .catch(() => {
                    return caches.match(event.request)
                        .then(response => {
                            if (response) {
                                return response;
                            }
                            // Fallback to offline page
                            return caches.match('/offline');
                        });
                })
        );
    } else {
        event.respondWith(
            caches.match(event.request)
                .then(response => {
                    if (response) {
                        return response;
                    }
                    return fetch(event.request);
                })
        );
    }
});

// Push Notifications
self.addEventListener('push', event => {
    const data = event.data ? event.data.text() : 'Royal Crumbs Notification';
    const options = {
        body: data,
        icon: '/static/img/logo-192.png',
        badge: '/static/img/logo-192.png'
    };
    event.waitUntil(
        self.registration.showNotification('Royal Crumbs', options)
    );
});

// Background Sync
self.addEventListener('sync', event => {
    if (event.tag === 'sync-data') {
        console.log('Background sync triggered');
        // Logic to sync data would go here
    }
});

// Periodic Background Sync
self.addEventListener('periodicsync', event => {
    if (event.tag === 'daily-sync') {
        console.log('Periodic sync triggered');
        // Logic to fetch daily updates would go here
    }
});
