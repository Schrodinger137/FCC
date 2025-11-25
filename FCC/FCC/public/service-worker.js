const CACHE_NAME = 'miapp-cache-v1';
const OFFLINE_URL = '/offline/';

const FILES_TO_CACHE = [
  '/',
  '/static/css/main.css',
  '/static/js/main.js',
  '/static/icons/icon-192.png',
  OFFLINE_URL
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(FILES_TO_CACHE))
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(clients.claim());
});

self.addEventListener('fetch', event => {
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() =>
        caches.open(CACHE_NAME).then(cache => cache.match(OFFLINE_URL))
      )
    );
    return;
  }
  event.respondWith(
    caches.match(event.request).then(resp => resp || fetch(event.request))
  );
});
