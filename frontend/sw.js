/**
 * AREOX Service Worker (sw.js)
 * Progressive Web App Engine: Offline Caching, Shell Pre-caching, Network-First Telemetry
 */

const CACHE_NAME = 'areox-shell-v1.0.7';
const DATA_CACHE_NAME = 'areox-data-v1.0.7';

const PRECACHE_ASSETS = [
  '/',
  '/manifest.json',
  '/offline.html',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
  '/icons/icon-maskable.png',
  '/icons/apple-touch-icon.png',
  '/icons/favicon.png',
  '/static/style.css',
  '/static/app.js'
];

// 1. Install Event: Pre-cache App Shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[AREOX SW] Pre-caching Core App Shell...');
      return cache.addAll(PRECACHE_ASSETS).catch((err) => {
        console.warn('[AREOX SW] Some assets could not be pre-cached:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

// 2. Activate Event: Prune Old Caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(
        keyList.map((key) => {
          if (key !== CACHE_NAME && key !== DATA_CACHE_NAME) {
            console.log('[AREOX SW] Removing legacy cache:', key);
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// 3. Fetch Event: Smart Routing
self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // Ignore non-GET requests and browser extensions
  if (request.method !== 'GET' || url.protocol.startsWith('chrome-extension')) {
    return;
  }

  // A. Real-Time API Endpoints: Network-First with Cache Fallback
  if (url.pathname.startsWith('/api/v1/')) {
    event.respondWith(
      fetch(request)
        .then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const resClone = networkResponse.clone();
            caches.open(DATA_CACHE_NAME).then((cache) => {
              cache.put(request, resClone);
            });
          }
          return networkResponse;
        })
        .catch(() => {
          // Fallback to cached API data
          return caches.match(request).then((cachedResponse) => {
            if (cachedResponse) {
              return cachedResponse;
            }
            // Return polite offline JSON payload if no cache
            return new Response(
              JSON.stringify({
                status: 'offline',
                offline: true,
                message: 'Device is offline. Showing cached snapshot.'
              }),
              {
                headers: { 'Content-Type': 'application/json' },
                status: 200
              }
            );
          });
        })
    );
    return;
  }

  // B. HTML Navigation Requests
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).catch(() => {
        return caches.match(request).then((cached) => {
          return cached || caches.match('/offline.html') || caches.match('/');
        });
      })
    );
    return;
  }

  // C. Static Assets: Network-First with Cache Fallback for instant updates
  event.respondWith(
    fetch(request)
      .then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200) {
          const resClone = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, resClone);
          });
        }
        return networkResponse;
      })
      .catch(() => caches.match(request))
  );
});

// 4. Message Event: Skip waiting on prompt
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
