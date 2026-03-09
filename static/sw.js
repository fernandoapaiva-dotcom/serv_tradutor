self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open('servsolda-v4').then((cache) => cache.addAll([
      '/',
      '/static/pwa-icon.png?v=3',
      '/static/manifest_servsolda.json?v=3'
    ])),
  );
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((response) => response || fetch(e.request)),
  );
});
