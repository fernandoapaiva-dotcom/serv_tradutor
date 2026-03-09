self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open('servsolda-v1').then((cache) => cache.addAll([
      '/',
      '/static/logo.png',
      '/static/manifest.json'
    ])),
  );
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((response) => response || fetch(e.request)),
  );
});
