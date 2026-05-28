self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open('servsolda-v5').then((cache) => cache.addAll([
      '/',
      '/static/pwa-icon.png?v=4',
      '/static/manifest_servsolda.json?v=4'
    ])),
  );
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((response) => response || fetch(e.request)),
  );
});
