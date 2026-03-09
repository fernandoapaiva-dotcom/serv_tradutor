self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open('servsolda-v3').then((cache) => cache.addAll([
      '/',
      '/static/pwa-icon.png?v=2',
      '/static/manifest.json?v=2'
    ])),
  );
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((response) => response || fetch(e.request)),
  );
});
