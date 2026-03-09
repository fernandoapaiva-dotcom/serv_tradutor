self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open('servsolda-v2').then((cache) => cache.addAll([
      '/',
      '/static/pwa-icon.png',
      '/static/manifest.webmanifest'
    ])),
  );
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((response) => response || fetch(e.request)),
  );
});
